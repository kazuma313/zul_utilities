#!/usr/bin/env python3
"""YouTube videos -> one .txt per video: a YAML header with the video's metadata, then the transcript.

    python scripts/yt_transcripts.py URL [URL ...] -o transcripts
    python scripts/yt_transcripts.py -i urls.txt -o transcripts --skip-category Gaming "Film & Animation"
    cat urls.txt | python scripts/yt_transcripts.py -i -

urls.txt: one URL or video ID per line; blank lines and lines starting with # are ignored.
Exit code: 0 when nothing failed (skipped videos are not failures), 1 when some failed (they are
listed in <output>/failed_urls.txt, so `-i <output>/failed_urls.txt` runs them again), 2 without input.

Needs `pip install "youtube-transcript-api>=1.2" yt-dlp`.  yt-dlp is optional: without it the metadata
is only the title and the channel (from oEmbed), and --skip-category cannot work.

When YouTube blocks this IP (HTTP 429, IpBlocked), two things get the transcript anyway:
  SUPADATA_API_KEY                         a transcript service (supadata.ai, 100 free transcripts a month);
                                           used only after YouTube refuses, for the rest of the batch.
                                           Read from the environment or from the nearest .env file
  WEBSHARE_PROXY_USERNAME / _PASSWORD      rotating residential proxies (webshare.io), or --proxy URL
"""

from __future__ import annotations

import argparse
import bisect
import json
import logging
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Sequence, TypeVar

from youtube_transcript_api import (
    AgeRestricted,
    InvalidVideoId,
    NoTranscriptFound,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
    VideoUnplayable,
    YouTubeTranscriptApi,
)
from youtube_transcript_api.proxies import GenericProxyConfig, WebshareProxyConfig

log = logging.getLogger("yt_transcripts")

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

DEFAULT_LANGUAGES = ("original", "id", "en")   # "original" = the language spoken in the video
DEFAULT_OUTPUT_DIR = "transcripts"
FAILED_URLS_FILENAME = "failed_urls.txt"

MAX_NAME_LENGTH = 64            # `name` limit of the skill format
MAX_DESCRIPTION_LENGTH = 1024   # `description` limit of the skill format
PARAGRAPH_TARGET_CHARS = 700    # rough length of one paragraph
PARAGRAPH_PAUSE_SECONDS = 4.0   # a pause in speech that may start a new paragraph
LOW_COVERAGE = 0.9              # below this share of the video the transcript is reported as incomplete
BLOCK_DELAY = 30.0              # first wait after YouTube refuses requests from this IP; doubles per attempt
BLOCKED_IN_A_ROW = 2            # this many blocked videos in a row stop the batch: going on only extends the block

SUPADATA_API = "https://api.supadata.ai/v1"
SUPADATA_WAIT = 600.0           # longest wait for a Supadata job (videos over 20 minutes are processed as a job)
PROVIDERS = ("auto", "youtube", "supadata")


class SupadataError(RuntimeError):
    """Supadata answered with an error (bad key, quota used up, rate limit, failed job)."""


class SupadataNoTranscript(SupadataError):
    """Supadata found no captions for the video (it is not asked to generate any: that costs 2 credits a minute)."""


# Errors that stay the same however often the request is repeated.
PERMANENT_ERRORS = (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, VideoUnplayable, AgeRestricted,
                    InvalidVideoId, SupadataNoTranscript)

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
PATH_PREFIXES_WITH_ID = ("shorts", "embed", "live", "v")
# Sounds in automatic captions: [musik], [Music], [tertawa], [Laughter], [tepuk tangan], and [ __ ] for a bleeped word.
SOUND_TAG_RE = re.compile(r"\[[^\[\]\d]{1,40}\]")
# Characters that do not show but end up in titles (seen: U+2060 at the start of a MALAKA title).
INVISIBLE_RE = re.compile("[\u200b-\u200f\u2060-\u2064\ufeff]")
URL_RE = re.compile(r"https?://\S+|www\.\S+")

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Snippet:
    text: str
    start: float
    duration: float = 0.0


@dataclass(frozen=True)
class Transcript:
    snippets: tuple[Snippet, ...]
    language_code: str
    is_generated: bool | None      # None: the source does not say whether the captions are automatic
    source: str = "youtube"        # youtube | supadata

    @property
    def end(self) -> float:
        last = self.snippets[-1] if self.snippets else Snippet("", 0.0)
        return last.start + last.duration


@dataclass(frozen=True)
class Chapter:
    start: float
    title: str


@dataclass(frozen=True)
class VideoMetadata:
    video_id: str
    title: str
    channel: str = ""
    channel_url: str = ""
    summary: str = ""        # the uploader's description of the video
    upload_date: str = ""    # YYYY-MM-DD
    duration: float = 0.0    # seconds; 0 when unknown
    live: bool = False       # recorded from a live stream
    category: str = ""       # YouTube's category: Education, Entertainment, Gaming, Film & Animation ...
    tags: tuple[str, ...] = ()
    chapters: tuple[Chapter, ...] = ()
    language: str = ""       # spoken language according to YouTube (id, en-US ...)
    source: str = "minimal"  # where the metadata came from: yt-dlp, supadata, oembed, minimal

    @property
    def url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.video_id}"


@dataclass(frozen=True)
class Result:
    source: str
    status: str             # "ok" | "skipped" | "failed"
    detail: str = ""
    blocked: bool = False   # failed because YouTube refuses requests from this IP


@dataclass(frozen=True)
class Settings:
    output_dir: Path = Path(DEFAULT_OUTPUT_DIR)
    languages: Sequence[str] = DEFAULT_LANGUAGES
    with_timestamps: bool = False
    keep_sound_tags: bool = False
    overwrite: bool = False
    retries: int = 3
    retry_delay: float = 2.0
    block_delay: float = BLOCK_DELAY
    proxy: str | None = None
    skip_categories: frozenset[str] = field(default_factory=frozenset)   # lower case
    provider: str = "auto"               # auto: YouTube, then Supadata once YouTube blocks; or only one of them
    supadata_key: str | None = None      # from SUPADATA_API_KEY; never written to a file


# ---------------------------------------------------------------------------
# Input: URL -> video ID
# ---------------------------------------------------------------------------

def extract_video_id(url_or_id: str) -> str | None:
    """The 11-character video ID of a URL (watch, youtu.be, shorts, live, embed) or of a bare ID; None otherwise."""
    candidate = url_or_id.strip()
    if VIDEO_ID_RE.match(candidate):
        return candidate
    if "://" not in candidate:
        candidate = "https://" + candidate
    parsed = urllib.parse.urlparse(candidate)
    host = (parsed.hostname or "").lower().removeprefix("www.").removeprefix("m.").removeprefix("music.")
    segments = [s for s in parsed.path.split("/") if s]
    video_id = None
    if host == "youtu.be" and segments:
        video_id = segments[0]
    elif host.endswith("youtube.com") or host.endswith("youtube-nocookie.com"):
        if segments[:1] == ["watch"]:
            video_id = urllib.parse.parse_qs(parsed.query).get("v", [None])[0]
        elif len(segments) >= 2 and segments[0] in PATH_PREFIXES_WITH_ID:
            video_id = segments[1]
    return video_id if video_id and VIDEO_ID_RE.match(video_id) else None


def read_sources(cli_urls: Sequence[str], input_file: str | None) -> list[str]:
    """URLs from the arguments and from a file or stdin, without comments and duplicates."""
    lines: list[str] = list(cli_urls)
    if input_file == "-":
        lines += sys.stdin.read().splitlines()
    elif input_file:
        lines += Path(input_file).read_text(encoding="utf-8").splitlines()
    cleaned = (line.strip() for line in lines)
    return list(dict.fromkeys(s for s in cleaned if s and not s.startswith("#")))


# ---------------------------------------------------------------------------
# Retry
# ---------------------------------------------------------------------------

def is_blocked(error: BaseException) -> bool:
    """YouTube refuses requests from this IP: IpBlocked / RequestBlocked, or HTTP 429 on the caption endpoint.

    Seen after about 30 transcript and metadata requests within a few minutes from one laptop.  It passes
    by itself after a while; retrying quickly only makes it last longer.
    """
    return isinstance(error, RequestBlocked) or "429" in str(error) or "Too Many Requests" in str(error)


def with_retry(action: Callable[[], T], attempts: int, base_delay: float, label: str, block_delay: float = BLOCK_DELAY,
               retry_blocked: bool = True) -> T:
    """Run `action`; repeat it with exponential backoff after an error that may be temporary (longer when blocked).

    retry_blocked=False gives up at the first block, when there is another source to turn to.
    """
    for attempt in range(1, attempts + 1):
        try:
            return action()
        except PERMANENT_ERRORS:
            raise
        except Exception as error:  # network, rate limit, parsing ...
            if attempt == attempts or (is_blocked(error) and not retry_blocked):
                raise
            wait = (block_delay if is_blocked(error) else base_delay) * 2 ** (attempt - 1)
            log.warning("%s gagal (percobaan %d/%d): %s. Ulang dalam %.0fs", label, attempt, attempts, short(error), wait)
            time.sleep(wait)
    raise AssertionError("unreachable")


def short(error: BaseException) -> str:
    """One line of an error message (the library's messages run to many lines)."""
    lines = [line.strip() for line in str(error).splitlines() if line.strip()]
    # youtube-transcript-api: the first line is generic, the cause is on the second.
    is_library_message = len(lines) > 1 and lines[0].startswith("Could not retrieve")
    message = lines[1] if is_library_message else (lines[0] if lines else "")
    return f"{type(error).__name__}: {message}"[:300]


# ---------------------------------------------------------------------------
# Transcript
# ---------------------------------------------------------------------------

def language_order(languages: Sequence[str], spoken_language: str) -> list[str]:
    """The preference list with "original" replaced by the spoken language (en-US is tried as en-US, then en)."""
    order: list[str] = []
    for code in languages:
        if code == "original":
            order += [spoken_language, spoken_language.split("-")[0]] if spoken_language else []
        else:
            order.append(code)
    return list(dict.fromkeys(c for c in order if c))


def setting(name: str) -> str | None:
    """An environment variable, else NAME=value from the nearest .env file (this folder or one of the five above it).

    Keeps the API key out of the shell history and out of every command; .env is in .gitignore.
    """
    if os.environ.get(name):
        return os.environ[name]
    for folder in [Path.cwd(), *Path.cwd().parents][:6]:
        env = folder / ".env"
        if env.is_file():
            for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
                key, sep, value = line.strip().partition("=")
                if sep and key.strip().removeprefix("export ").strip() == name:
                    return value.strip().strip('"').strip("'") or None
            return None                         # only the nearest .env counts
    return None


def proxy_config(proxy: str | None):
    """--proxy URL, else Webshare rotating residential proxies from WEBSHARE_PROXY_USERNAME / _PASSWORD, else none."""
    if proxy:
        return GenericProxyConfig(http_url=proxy, https_url=proxy)
    username, password = setting("WEBSHARE_PROXY_USERNAME"), setting("WEBSHARE_PROXY_PASSWORD")
    if username and password:
        return WebshareProxyConfig(proxy_username=username, proxy_password=password)
    return None


class TranscriptFetcher:
    """Captions straight from YouTube (youtube-transcript-api): free, but YouTube blocks an IP that asks too often."""

    def __init__(self, languages: Sequence[str], proxy: str | None = None):
        self._languages = list(languages)
        self._api = YouTubeTranscriptApi(proxy_config=proxy_config(proxy))

    def fetch(self, video_id: str, spoken_language: str = "") -> Transcript:
        available = self._api.list(video_id)
        fetched = self._choose(available, spoken_language).fetch()
        snippets = tuple(Snippet(s.text, s.start, getattr(s, "duration", 0.0)) for s in fetched)
        if not snippets:
            raise RuntimeError("transcript kosong")
        return Transcript(snippets, fetched.language_code, fetched.is_generated)

    def languages_for(self, spoken_language: str) -> list[str]:
        return language_order(self._languages, spoken_language)

    def _choose(self, available, spoken_language: str):
        """Preferred languages first (manual before automatic within a language); else whatever there is.

        The spoken language comes first by default: YouTube also lists machine-translated tracks, and an
        Indonesian translation of an English lecture is a worse source than the English captions.
        """
        try:
            return available.find_transcript(self.languages_for(spoken_language))
        except NoTranscriptFound:
            candidates = sorted(available, key=lambda t: t.is_generated)
            if not candidates:
                raise
            log.info("Bahasa %s tidak tersedia, memakai '%s'", self._languages, candidates[0].language_code)
            return candidates[0]


class SupadataFetcher:
    """Captions through supadata.ai, a transcript service with its own IPs: works while YouTube blocks this one.

    Free plan: 100 requests a month, 1 per second, no card.  Only existing captions are asked for
    (mode=native, 1 credit per video); "auto" would let Supadata generate a transcript with AI for a video
    without captions, at 2 credits per minute, so one podcast could use up the month.
    """

    def __init__(self, api_key: str, languages: Sequence[str], wait: float = SUPADATA_WAIT):
        self._key, self._languages, self._wait = api_key, list(languages), wait

    def fetch(self, video_id: str, spoken_language: str = "") -> Transcript:
        params = {"url": f"https://www.youtube.com/watch?v={video_id}", "mode": "native", "text": "false"}
        order = language_order(self._languages, spoken_language)
        if order:
            params["lang"] = order[0].split("-")[0]
        status, data = self._get("/transcript?" + urllib.parse.urlencode(params))
        if status == 202:                       # videos over 20 minutes: a job to wait for
            data = self._wait_for(data["jobId"])
        result = data.get("result") or data
        content = result.get("content") or []
        snippets = tuple(Snippet(str(c.get("text") or ""), float(c.get("offset") or 0) / 1000, float(c.get("duration") or 0) / 1000)
                         for c in content if isinstance(c, dict))
        if not snippets:
            raise SupadataNoTranscript(f"Supadata: tidak ada caption untuk {video_id}")
        log.info("Transcript %s diambil lewat Supadata (1 kredit)", video_id)
        return Transcript(snippets, result.get("lang") or params.get("lang", ""), None, source="supadata")

    def metadata(self, video_id: str) -> VideoMetadata:
        """Title, channel, description, duration, tags and date; no category or chapters.  Costs 1 credit."""
        _, data = self._get("/metadata?" + urllib.parse.urlencode({"url": f"https://www.youtube.com/watch?v={video_id}"}))
        created = str(data.get("createdAt") or "")
        return VideoMetadata(
            video_id=video_id, title=clean_text(data.get("title") or "") or video_id,
            channel=clean_text((data.get("author") or {}).get("displayName") or ""), summary=(data.get("description") or "").strip(),
            upload_date=created[:10] if re.match(r"\d{4}-\d{2}-\d{2}", created) else "",
            duration=float((data.get("media") or {}).get("duration") or 0), tags=tuple(clean_text(t) for t in data.get("tags") or [] if t),
            source="supadata")

    def _wait_for(self, job_id: str) -> dict:
        deadline = time.monotonic() + self._wait
        while time.monotonic() < deadline:
            time.sleep(2.0)                     # Supadata asks for about one poll a second; the free plan allows 1 request/s
            _, data = self._get(f"/transcript/{urllib.parse.quote(job_id)}")
            if data.get("status") == "completed":
                return data
            if data.get("status") == "failed":
                error = data.get("error") or {}
                message = error.get("message") if isinstance(error, dict) else str(error)
                if "unavailable" in str(error):
                    raise SupadataNoTranscript(f"Supadata: {message or 'tidak ada caption'}")
                raise SupadataError(f"Supadata: job gagal: {message}")
        raise SupadataError(f"Supadata: job {job_id} belum selesai setelah {self._wait:.0f} detik")

    def _get(self, path: str) -> tuple[int, dict]:
        request = urllib.request.Request(SUPADATA_API + path, headers={"x-api-key": self._key, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                status, body = response.status, response.read()
        except urllib.error.HTTPError as error:
            status, body = error.code, error.read()
        try:
            data = json.loads(body.decode("utf-8") or "{}")
        except ValueError:
            data = {}
        code = str(data.get("error") or "") if isinstance(data, dict) else ""
        detail = data.get("details") or data.get("message") or "" if isinstance(data, dict) else ""
        if status == 206 or code == "transcript-unavailable":       # Supadata says "no transcript" with 206
            raise SupadataNoTranscript(f"Supadata: tidak ada caption ({detail})")
        if status in (401, 403):
            raise SupadataError("Supadata menolak API key (periksa SUPADATA_API_KEY)")
        if status == 402:
            raise SupadataError("Supadata: kredit bulan ini habis (paket gratis 100 per bulan)")
        if status == 429:
            raise SupadataError(f"Supadata: terlalu banyak permintaan, Too Many Requests ({detail})")
        if status >= 400:
            raise SupadataError(f"Supadata HTTP {status}: {code} {detail}".strip())
        return status, data


class TranscriptSources:
    """Where a transcript comes from: YouTube first (free); Supadata once YouTube blocks, for the rest of the batch."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.youtube = TranscriptFetcher(settings.languages, settings.proxy) if settings.provider != "supadata" else None
        self.supadata = SupadataFetcher(settings.supadata_key, settings.languages) if settings.supadata_key else None
        if settings.provider == "supadata" and not self.supadata:
            raise ValueError("--provider supadata butuh SUPADATA_API_KEY")
        self.youtube_blocked = False

    def fetch(self, video_id: str, spoken_language: str = "") -> Transcript:
        s = self.settings
        if self.youtube and not (self.youtube_blocked and self.supadata):
            fallback = s.provider == "auto" and self.supadata is not None
            try:
                return with_retry(lambda: self.youtube.fetch(video_id, spoken_language), s.retries, s.retry_delay,
                                  f"Transcript {video_id}", s.block_delay, retry_blocked=not fallback)
            except Exception as error:
                if not (fallback and is_blocked(error)):
                    raise
                self.youtube_blocked = True
                log.warning("YouTube memblokir IP ini; transcript berikutnya diambil lewat Supadata")
        if not self.supadata:
            raise SupadataError("tidak ada sumber transcript (YouTube diblokir dan SUPADATA_API_KEY tidak diisi)")
        return with_retry(lambda: self.supadata.fetch(video_id, spoken_language), s.retries, s.retry_delay,
                          f"Supadata {video_id}", block_delay=2.0)


# ---------------------------------------------------------------------------
# Metadata (yt-dlp -> Supadata -> oEmbed -> minimal)
# ---------------------------------------------------------------------------

def fetch_metadata(video_id: str, proxy: str | None = None, supadata: SupadataFetcher | None = None) -> VideoMetadata:
    """Never fails: missing metadata must not cost the transcript.

    yt-dlp kept working while YouTube blocked the transcript requests, so Supadata (1 credit, no category
    or chapters) is only asked when yt-dlp fails.
    """
    providers = [_metadata_from_ytdlp] + ([lambda vid, _proxy: supadata.metadata(vid)] if supadata else []) + [_metadata_from_oembed]
    for provider in providers:
        try:
            return provider(video_id, proxy)
        except Exception as error:
            log.debug("%s gagal untuk %s: %s", getattr(provider, "__name__", "supadata"), video_id, short(error))
    log.warning("Metadata %s tidak didapat; memakai video ID sebagai judul", video_id)
    return VideoMetadata(video_id=video_id, title=video_id)


def _metadata_from_ytdlp(video_id: str, proxy: str | None) -> VideoMetadata:
    import yt_dlp  # optional: without it the metadata comes from oEmbed

    options = {"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": True, "proxy": proxy}
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
    raw_date = info.get("upload_date") or ""
    chapters = tuple(Chapter(float(c.get("start_time") or 0), clean_text(c.get("title") or ""))
                     for c in info.get("chapters") or [] if c.get("title"))
    return VideoMetadata(
        video_id=video_id,
        title=clean_text(info.get("title") or "") or video_id,
        channel=clean_text(info.get("channel") or info.get("uploader") or ""),
        channel_url=info.get("channel_url") or info.get("uploader_url") or "",
        summary=(info.get("description") or "").strip(),
        upload_date=f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}" if len(raw_date) == 8 else "",
        duration=float(info.get("duration") or 0),
        live=bool(info.get("was_live")) or info.get("live_status") in ("was_live", "is_live", "post_live"),
        category=", ".join(info.get("categories") or []),
        tags=tuple(clean_text(t) for t in info.get("tags") or [] if t),
        chapters=chapters,
        language=info.get("language") or "",
        source="yt-dlp",
    )


def _metadata_from_oembed(video_id: str, proxy: str | None) -> VideoMetadata:
    query = urllib.parse.urlencode({"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"})
    handlers = [urllib.request.ProxyHandler({"http": proxy, "https": proxy})] if proxy else []
    with urllib.request.build_opener(*handlers).open(f"https://www.youtube.com/oembed?{query}", timeout=15) as response:
        data = json.load(response)
    return VideoMetadata(video_id=video_id, title=clean_text(data["title"]), channel=clean_text(data.get("author_name", "")),
                         channel_url=data.get("author_url", ""), source="oembed")


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    return " ".join(INVISIBLE_RE.sub("", text).split())


def slugify(text: str, max_length: int = MAX_NAME_LENGTH) -> str:
    """'Belajar Python #1: Dasar' -> 'belajar-python-1-dasar' (lower case, digits, '-'), cut at a word boundary."""
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    if len(slug) <= max_length:
        return slug
    cut = slug[:max_length + 1]
    return (cut.rsplit("-", 1)[0] if "-" in cut[:max_length] else slug[:max_length]).strip("-")


def build_name(metadata: VideoMetadata) -> str:
    """A slug of the title.  A live stream also gets its date: its title is often the same every week."""
    if metadata.live and metadata.upload_date:
        base = slugify(metadata.title, MAX_NAME_LENGTH - len(metadata.upload_date) - 1)
        return f"{base}-{metadata.upload_date}" if base else f"video-{metadata.video_id}"
    return slugify(metadata.title) or f"video-{metadata.video_id}"


def clock(seconds: float) -> str:
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def short_duration(seconds: float) -> str:
    """2650 -> '44:10', 3612 -> '1:00:12' (the way YouTube shows it)."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def summary_line(summary: str) -> str:
    """The uploader's description without links, hashtags and separator lines, as one line."""
    lines = []
    for line in summary.splitlines():
        line = URL_RE.sub("", line)
        line = re.sub(r"(?:^|\s)#\w+", "", line)
        if re.search(r"[A-Za-z]{3}", line) and not re.fullmatch(r"[\W_]*", line):
            lines.append(line.strip(" :-|>➡"))
    return clean_text(" ".join(lines))


def caption_kind(transcript: Transcript) -> str:
    if transcript.is_generated is None:
        return "unknown"
    return "auto-generated" if transcript.is_generated else "manual"


def coverage(metadata: VideoMetadata, transcript: Transcript) -> float | None:
    """The share of the video the captions reach, from 0 to 1; None when the duration is unknown."""
    return round(min(transcript.end / metadata.duration, 1.0), 2) if metadata.duration else None


def build_description(metadata: VideoMetadata, transcript: Transcript) -> str:
    facts = [short_duration(metadata.duration)] if metadata.duration else []
    kind = caption_kind(transcript)
    facts.append(f"language {transcript.language_code}, " + ("captions" if kind == "unknown" else f"{kind} captions"))
    if metadata.upload_date:
        facts.append(("streamed live " if metadata.live else "uploaded ") + metadata.upload_date)
    text = f'Transcript of the YouTube video "{clean_text(metadata.title)}"'
    text += f" by {clean_text(metadata.channel)}" if metadata.channel else ""
    text += f" ({'; '.join(facts)})."
    summary = summary_line(metadata.summary)
    return truncate(text + (f" Video summary: {summary}" if summary else ""), MAX_DESCRIPTION_LENGTH)


def spoken(text: str, keep_sound_tags: bool) -> str:
    return clean_text(text if keep_sound_tags else SOUND_TAG_RE.sub(" ", text))


def build_body(transcript: Transcript, metadata: VideoMetadata, with_timestamps: bool, keep_sound_tags: bool = False) -> str:
    """The transcript in paragraphs (or one timed line per caption), under a heading for every chapter."""
    parts = []
    for chapter, snippets in split_by_chapters(transcript.snippets, metadata.chapters):
        lines = [(s.start, spoken(s.text, keep_sound_tags)) for s in snippets]
        lines = [(start, text) for start, text in lines if text]
        if with_timestamps:
            text = "\n".join(f"[{clock(start)}] {line}" for start, line in lines)
        else:
            text = "\n\n".join(paragraphs(lines))
        if chapter is not None:
            parts.append(f"### {clock(chapter.start)} {clean_text(chapter.title)}")
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def split_by_chapters(snippets: Sequence[Snippet], chapters: Sequence[Chapter]):
    """[(chapter or None, its snippets)]: None holds what comes before the first chapter, or everything without chapters."""
    starts = [c.start for c in chapters]
    groups: list[tuple[Chapter | None, list[Snippet]]] = [(None, [])] + [(c, []) for c in chapters]
    for snippet in snippets:
        groups[bisect.bisect_right(starts, snippet.start)][1].append(snippet)
    return [(chapter, group) for chapter, group in groups if group or chapter is not None]


def paragraphs(lines: Sequence[tuple[float, str]]) -> Iterable[str]:
    """New paragraph after a long pause in speech, or when the paragraph has grown too long."""
    current: list[str] = []
    length = 0
    previous_start = lines[0][0] if lines else 0.0
    for start, text in lines:
        long_pause = start - previous_start >= PARAGRAPH_PAUSE_SECONDS * 2
        too_long = length >= PARAGRAPH_TARGET_CHARS and current[-1].endswith((".", "?", "!"))
        far_too_long = length >= PARAGRAPH_TARGET_CHARS * 2
        if current and (long_pause and length >= PARAGRAPH_TARGET_CHARS // 2 or too_long or far_too_long):
            yield " ".join(current)
            current, length = [], 0
        current.append(text)
        length += len(text) + 1
        previous_start = start
    if current:
        yield " ".join(current)


def document_fields(metadata: VideoMetadata, transcript: Transcript, keep_sound_tags: bool = False) -> dict:
    """The video's metadata as one flat dict, built by code alone: name and description first, then the facts."""
    return {
        "name": build_name(metadata), "description": build_description(metadata, transcript),
        "title": clean_text(metadata.title), "channel": clean_text(metadata.channel), "channel_url": metadata.channel_url,
        "url": metadata.url, "video_id": metadata.video_id, "upload_date": metadata.upload_date,
        "duration": short_duration(metadata.duration) if metadata.duration else "",
        "duration_seconds": int(metadata.duration) if metadata.duration else None,
        "live_recording": metadata.live, "category": metadata.category, "tags": list(metadata.tags),
        "spoken_language": metadata.language, "transcript_language": transcript.language_code,
        "captions": caption_kind(transcript), "transcript_source": transcript.source,
        "caption_coverage": coverage(metadata, transcript),
        "words": sum(len(re.findall(r"\w+", spoken(s.text, keep_sound_tags))) for s in transcript.snippets),
        "chapters": [f"{clock(c.start)} {clean_text(c.title)}" for c in metadata.chapters],
        "metadata_source": metadata.source,
    }


def render_document(fields: dict, video_description: str, body: str) -> str:
    """Header (fields as YAML), the uploader's description, the transcript: the text of one .txt file."""
    header = [f"name: {fields['name']}", f"description: {yaml_scalar(fields['description'])}"]
    header += [f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in fields.items()
               if key not in ("name", "description")
               and (value not in ("", [], None) or key in ("live_recording", "caption_coverage"))]
    sections = ["## Video description\n\n" + video_description.strip()] if video_description.strip() else []
    sections.append("## Transcript\n\n" + body.strip())
    return "---\n" + "\n".join(header) + "\n---\n\n" + "\n\n".join(sections) + "\n"


def build_document(metadata: VideoMetadata, transcript: Transcript, with_timestamps: bool = False,
                   keep_sound_tags: bool = False) -> str:
    """Header (name, description and the video's metadata as YAML), the video description, the transcript."""
    return render_document(document_fields(metadata, transcript, keep_sound_tags), metadata.summary,
                           build_body(transcript, metadata, with_timestamps, keep_sound_tags))


def truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def yaml_scalar(value: str) -> str:
    """The value as it is when that is a safe YAML plain scalar, else in double quotes."""
    is_plain_safe = (re.match(r"[A-Za-z0-9]", value) is not None and ": " not in value and " #" not in value
                     and not value.endswith(":") and '"' not in value)
    return value if is_plain_safe else json.dumps(value, ensure_ascii=False)


# ---------------------------------------------------------------------------
# One video
# ---------------------------------------------------------------------------

def find_existing(output_dir: Path, video_id: str) -> Path | None:
    return next(iter(output_dir.glob(f"*-{video_id}.txt")), None)


def fetch_video(video_id: str, settings: Settings, sources) -> tuple[VideoMetadata, Transcript | None, str]:
    """(metadata, transcript, why it was skipped).  The metadata comes first: a skipped category costs no transcript.

    `sources` is a TranscriptSources, or anything with fetch(video_id, spoken_language).
    """
    metadata = fetch_metadata(video_id, settings.proxy, getattr(sources, "supadata", None))
    categories = {c.strip().lower() for c in metadata.category.split(",") if c.strip()}
    skipped = categories & settings.skip_categories
    if skipped:
        return metadata, None, f"kategori {metadata.category} dilewati (--skip-category)"
    if settings.skip_categories and metadata.source != "yt-dlp":
        log.warning("Kategori %s tidak diketahui (yt-dlp tidak jalan); video tidak dilewati", video_id)
    if isinstance(sources, TranscriptSources):
        transcript = sources.fetch(video_id, metadata.language)
    else:
        transcript = with_retry(lambda: sources.fetch(video_id, metadata.language), settings.retries, settings.retry_delay,
                                f"Transcript {video_id}", settings.block_delay)
    share = coverage(metadata, transcript)
    if share is not None and share < LOW_COVERAGE:
        log.warning("Transcript %s hanya menutup %d%% video (%s dari %s)", video_id, share * 100, short_duration(transcript.end),
                    short_duration(metadata.duration))
    return metadata, transcript, ""


def process(source: str, settings: Settings, fetcher) -> Result:
    video_id = extract_video_id(source)
    if not video_id:
        return Result(source, "failed", "bukan URL/ID video YouTube yang valid")
    existing = find_existing(settings.output_dir, video_id)
    if existing and not settings.overwrite:
        return Result(source, "skipped", f"sudah ada: {existing.name}")
    try:
        metadata, transcript, skipped = fetch_video(video_id, settings, fetcher)
    except Exception as error:
        return Result(source, "failed", short(error), blocked=is_blocked(error))
    if transcript is None:
        return Result(source, "skipped", skipped)
    target = settings.output_dir / f"{build_name(metadata)}-{video_id}.txt"
    write_atomically(target, build_document(metadata, transcript, settings.with_timestamps, settings.keep_sound_tags))
    if existing and existing != target:
        existing.unlink()   # the title changed: do not leave the old file behind
    return Result(source, "ok", target.name)


def write_atomically(target: Path, content: str) -> None:
    """Write a temporary file and rename it, so a half-written file never exists."""
    temporary = target.with_suffix(".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(target)


# ---------------------------------------------------------------------------
# Batch
# ---------------------------------------------------------------------------

def run(sources: Sequence[str], settings: Settings, delay: float) -> list[Result]:
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    fetcher = TranscriptSources(settings)
    results: list[Result] = []
    for index, source in enumerate(sources, start=1):
        result = process(source, settings, fetcher)
        results.append(result)
        level = logging.ERROR if result.status == "failed" else logging.INFO
        log.log(level, "[%d/%d] %-7s %s -> %s", index, len(sources), result.status.upper(), source, result.detail)
        if len(results) >= BLOCKED_IN_A_ROW and all(r.blocked for r in results[-BLOCKED_IN_A_ROW:]) and index < len(sources):
            rest = sources[index:]
            log.error("YouTube memblokir permintaan dari IP ini; %d URL sisanya tidak dicoba. Tunggu beberapa menit "
                      "sampai satu jam lalu jalankan ulang dengan -i %s, isi SUPADATA_API_KEY, atau pakai --proxy.", len(rest),
                      settings.output_dir / FAILED_URLS_FILENAME)
            results += [Result(s, "failed", "tidak dicoba: YouTube memblokir IP ini", blocked=True) for s in rest]
            break
        if not result.detail.startswith("sudah ada") and index < len(sources):
            time.sleep(delay)   # polite to YouTube; fewer blocks
    return results


def report(results: Sequence[Result], output_dir: Path) -> int:
    failed = [r for r in results if r.status == "failed"]
    counts = {s: sum(r.status == s for r in results) for s in ("ok", "skipped", "failed")}
    log.info("Selesai: %(ok)d sukses, %(skipped)d dilewati, %(failed)d gagal", counts)
    failed_file = output_dir / FAILED_URLS_FILENAME
    if failed:
        failed_file.write_text("\n".join(f"# {r.detail}\n{r.source}" for r in failed) + "\n", encoding="utf-8")
        log.info("URL gagal disimpan di %s (jalankan ulang dengan -i)", failed_file)
    elif failed_file.exists():
        failed_file.unlink()
    return 1 if failed else 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ambil transcript YouTube menjadi .txt ber-header metadata.")
    parser.add_argument("urls", nargs="*", help="URL atau ID video YouTube")
    parser.add_argument("-i", "--input-file", help="file berisi daftar URL ('-' untuk stdin)")
    parser.add_argument("-o", "--output-dir", default=DEFAULT_OUTPUT_DIR, help=f"folder keluaran (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("-l", "--languages", nargs="+", default=list(DEFAULT_LANGUAGES),
                        help="urutan prioritas bahasa; 'original' = bahasa yang diucapkan di video (default: original id en)")
    parser.add_argument("-t", "--timestamps", action="store_true", help="satu baris per caption dengan [HH:MM:SS]")
    parser.add_argument("--keep-sound-tags", action="store_true", help="pertahankan penanda seperti [musik] dan [tertawa]")
    parser.add_argument("--skip-category", nargs="+", default=[], metavar="CATEGORY",
                        help='lewati video dengan kategori YouTube ini, mis. Gaming "Film & Animation" Music')
    parser.add_argument("--overwrite", action="store_true", help="ambil ulang walau file sudah ada")
    parser.add_argument("--retries", type=int, default=3, help="jumlah percobaan (default: 3)")
    parser.add_argument("--retry-delay", type=float, default=2.0, help="jeda awal backoff dalam detik (default: 2)")
    parser.add_argument("--delay", type=float, default=3.0, help="jeda antar video dalam detik (default: 3)")
    parser.add_argument("--block-delay", type=float, default=BLOCK_DELAY,
                        help=f"jeda awal saat YouTube memblokir IP ini, berlipat tiap percobaan (default: {BLOCK_DELAY:.0f})")
    parser.add_argument("--proxy", help="URL proxy, mis. http://user:pass@host:port")
    parser.add_argument("--provider", choices=PROVIDERS, default="auto",
                        help="sumber transcript: auto = YouTube, lalu Supadata bila YouTube memblokir (butuh SUPADATA_API_KEY)")
    parser.add_argument("-v", "--verbose", action="store_true", help="tampilkan log debug")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001 - an old console keeps its encoding
        pass
    sources = read_sources(args.urls, args.input_file)
    if not sources:
        log.error("Tidak ada URL. Beri URL sebagai argumen atau lewat -i urls.txt")
        return 2
    settings = Settings(output_dir=Path(args.output_dir), languages=args.languages, with_timestamps=args.timestamps,
                        keep_sound_tags=args.keep_sound_tags, overwrite=args.overwrite, retries=max(1, args.retries),
                        retry_delay=args.retry_delay, block_delay=args.block_delay, proxy=args.proxy,
                        skip_categories=frozenset(c.strip().lower() for c in args.skip_category),
                        provider=args.provider, supadata_key=setting("SUPADATA_API_KEY"))
    if settings.provider == "supadata" and not settings.supadata_key:
        log.error("--provider supadata butuh SUPADATA_API_KEY di lingkungan atau di file .env (daftar gratis di supadata.ai)")
        return 2
    return report(run(sources, settings, args.delay), settings.output_dir)


if __name__ == "__main__":
    sys.exit(main())
