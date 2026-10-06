"""YouTube transcript skill: what is said in a YouTube video, with the video's metadata.

No language model is involved anywhere: the captions come from YouTube (or Supadata), the metadata from
yt-dlp, and the header, the paragraphs, the chapter headings and the parts are made by code.

    from skills.youtube_transcript.youtube_transcript_skill import fetch_transcript
    record = fetch_transcript("https://youtu.be/Pc3GWaOWHLk")
    record["metadata"]["title"], record["metadata"]["duration"], record["transcript"]

`get_youtube_transcript` is the same thing as a LangChain tool for an agent; it is None when
langchain-core is not installed, and the plain functions work without it.  For many videos at once, or to
keep the transcripts as files, run scripts/yt_transcripts.py (see SKILL.md).

Environment, for when YouTube blocks this machine's IP (read from the environment or the nearest .env):
  SUPADATA_API_KEY      transcripts through supadata.ai, used only after YouTube refuses
  YT_TRANSCRIPT_PROXY   http://user:pass@host:port, or WEBSHARE_PROXY_USERNAME / WEBSHARE_PROXY_PASSWORD
"""

import importlib
import sys
from collections import OrderedDict
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent / "scripts"
PART_CHARS = 12000      # one tool reply; a one-hour podcast is about 55 000 characters, too much for an 8k context
CACHED_VIDEOS = 8       # records kept in memory, so part=2, 3 ... do not fetch the video again


def _load(required, optional=()):
    """Import this skill's scripts without leaving their names behind (the other skills share module names)."""
    own = {p.stem for p in _SCRIPTS.glob("*.py")}
    aside = {name: sys.modules.pop(name) for name in own if name in sys.modules}
    sys.path.insert(0, str(_SCRIPTS))
    loaded = {}
    try:
        for name in required:
            loaded[name] = importlib.import_module(name)
        for name in optional:
            try:
                loaded[name] = importlib.import_module(name)
            except ImportError:
                loaded[name] = None
    finally:
        for name in own:
            sys.modules.pop(name, None)
        sys.modules.update(aside)
        while str(_SCRIPTS) in sys.path:
            sys.path.remove(str(_SCRIPTS))
    return loaded


_yt = _load(["yt_transcripts"])["yt_transcripts"]
_records: "OrderedDict[tuple, dict]" = OrderedDict()
_sources: dict = {}       # one TranscriptSources per setup: it remembers that YouTube blocked this IP


# ---------------------------------------------------------------------------
# Plain functions: no model, no LangChain
# ---------------------------------------------------------------------------

def fetch_transcript(url: str, language: str = "", with_timestamps: bool = False) -> dict:
    """Metadata and transcript of one YouTube video.

    Returns {"metadata": {...}, "video_description": str, "transcript": str, "document": str}:
      metadata           name, description, title, channel, channel_url, url, video_id, upload_date, duration,
                         duration_seconds, live_recording, category, tags, spoken_language, transcript_language,
                         captions, transcript_source, caption_coverage, words, chapters, metadata_source
      video_description  the uploader's description, unchanged
      transcript         the captions as paragraphs (or [HH:MM:SS] lines), a "###" heading per chapter
      document           all of it as the text of one .txt file, the way scripts/yt_transcripts.py writes it
    Raises ValueError for something that is not a video link, and the fetch error otherwise (SKILL.md, "When it fails").
    """
    video_id = _yt.extract_video_id(url or "")
    if not video_id:
        raise ValueError(f"not a YouTube video URL or ID: {url!r}")
    language = (language or "").strip()
    key = (video_id, language, with_timestamps)
    if key not in _records:
        languages = [language, *_yt.DEFAULT_LANGUAGES] if language else list(_yt.DEFAULT_LANGUAGES)
        settings = _yt.Settings(languages=languages, retries=2, block_delay=10.0, with_timestamps=with_timestamps,
                                proxy=_yt.setting("YT_TRANSCRIPT_PROXY"), supadata_key=_yt.setting("SUPADATA_API_KEY"))
        sources = _sources.setdefault((tuple(languages), settings.proxy, settings.supadata_key), _yt.TranscriptSources(settings))
        metadata, transcript, _ = _yt.fetch_video(video_id, settings, sources)
        fields = _yt.document_fields(metadata, transcript)
        body = _yt.build_body(transcript, metadata, with_timestamps)
        _records[key] = {"metadata": fields, "video_description": metadata.summary, "transcript": body,
                         "document": _yt.render_document(fields, metadata.summary, body)}
        while len(_records) > CACHED_VIDEOS:
            _records.popitem(last=False)
    return _records[key]


def split_parts(document: str, size: int = PART_CHARS) -> list[str]:
    """Pieces of at most `size` characters, cut between paragraphs (inside one only when it is longer than `size`)."""
    parts, current = [], ""
    for block in document.split("\n\n"):
        while len(block) > size:
            if current:
                parts.append(current)
                current = ""
            parts.append(block[:size])
            block = block[size:]
        if current and len(current) + 2 + len(block) > size:
            parts.append(current)
            current = ""
        current = f"{current}\n\n{block}" if current else block
    if current:
        parts.append(current)
    return parts or [""]


def transcript_part(url: str, part: int = 1, language: str = "") -> str:
    """One part of the document, with "[part N of M ...]" at the end when there are more; errors as plain sentences."""
    try:
        document = fetch_transcript(url, language)["document"]
    except ValueError:
        # gemma3:4b sends "is there a good YouTube video about ...?" here; the reply points it to the right skill.
        return (f"Not a YouTube video URL or ID: {url!r}. This tool needs the link of one video. To find or recommend "
                "videos, use web search instead; for a playlist or channel, ask the user for the video links.")
    except Exception as error:  # noqa: BLE001 - the reason goes back to the caller as text
        if _yt.is_blocked(error):
            return ("YouTube is refusing requests from this machine right now (too many requests). Tell the user to "
                    "try again in a few minutes, or to set SUPADATA_API_KEY (a transcript service with a free plan) or "
                    "YT_TRANSCRIPT_PROXY. Do not write a transcript yourself.")
        return f"No transcript for {url}: {_yt.short(error)}. Do not write a transcript yourself."
    parts = split_parts(document)
    number = min(max(1, int(part or 1)), len(parts))
    text = parts[number - 1]
    if len(parts) > 1:
        more = f"; call again with part={number + 1} for the rest" if number < len(parts) else "; this is the end"
        text += f"\n\n[part {number} of {len(parts)}{more}]"
    return text


# ---------------------------------------------------------------------------
# Optional: the same as a LangChain tool, for an agent
# ---------------------------------------------------------------------------

def _get_youtube_transcript(url: str, part: int = 1, language: str = "") -> str:
    """Get the transcript (what is said) and the metadata of one YouTube video.

    Use it whenever the user gives a YouTube link (youtube.com/watch, youtu.be, shorts, live) and wants
    to read, summarise, quote, translate or study the video, even without saying "transcript".
    Part 1 starts with the metadata: title, channel, upload date, duration, category, chapters, language
    and whether the captions are automatic. A long video comes in parts; the reply ends with
    "[part N of M ...]" - call again with part=N+1 for the rest. Never write a transcript yourself.

    Args:
        url: The video's URL or its 11-character ID.
        part: Which part of a long transcript to return; 1 is the start.
        language: Language code to prefer, for example "id" or "en". Empty: the language spoken in the video.
    """
    return transcript_part(url, part, language)


try:
    from langchain_core.tools import StructuredTool
except ImportError:  # pragma: no cover - the plain functions above work without LangChain
    get_youtube_transcript = None
else:
    get_youtube_transcript = StructuredTool.from_function(_get_youtube_transcript, name="get_youtube_transcript")


__all__ = ["fetch_transcript", "transcript_part", "split_parts", "get_youtube_transcript"]
