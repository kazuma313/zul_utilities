"""Tests without network access for scripts/yt_transcripts.py and the get_youtube_transcript tool.

    python -m pytest research/agentic/algorithms/skills/youtube_transcript/tests -q -p no:cacheprovider
"""

import io
import re
import json
import sys
import urllib.error
from pathlib import Path

import pytest
import yaml

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(SKILL.parent.parent))
import yt_transcripts as yt  # noqa: E402
from skills.youtube_transcript import youtube_transcript_skill as skill  # noqa: E402
from youtube_transcript_api import IpBlocked, NoTranscriptFound  # noqa: E402

# the URLs from evals/sample_urls.txt, in the forms users paste them
URLS = {
    "https://www.youtube.com/live/56HmqxOTK0U?si=nIQaoKYTBU8MUGAt": "56HmqxOTK0U",
    "https://youtu.be/Qft-J2LG0NM?si=4BZhF60S3gUFPZ77": "Qft-J2LG0NM",
    "https://youtu.be/NJD_0BtZrlA?si=drQd_ip-lcl4zkS-": "NJD_0BtZrlA",
    "https://www.youtube.com/watch?v=uYGmdIGqUXs": "uYGmdIGqUXs",
    "youtube.com/shorts/Pc3GWaOWHLk": "Pc3GWaOWHLk",
    "https://m.youtube.com/watch?v=MOl6qqoJKWA&t=30s": "MOl6qqoJKWA",
    "https://music.youtube.com/watch?v=gqCEJ1McXCQ": "gqCEJ1McXCQ",
    "https://www.youtube-nocookie.com/embed/gqCEJ1McXCQ": "gqCEJ1McXCQ",
    "Qft-J2LG0NM": "Qft-J2LG0NM",
}


def metadata(**changes):
    values = dict(video_id="Qft-J2LG0NM", title="⁠Trader Sejati = Berani CUTLOSS", channel="Theresa Learns",
                  channel_url="https://www.youtube.com/@Theresalearns", upload_date="2026-10-04", duration=600.0,
                  category="People & Blogs", tags=("crypto", "trading"), language="id", source="yt-dlp",
                  summary="Kali ini kita ngobrol bareng KJo soal trading.\n\nTwitch ➡ https://www.twitch.tv/x\n#podcast #crypto\n=====")
    values.update(changes)
    return yt.VideoMetadata(**values)


def transcript(n=60, step=10.0, generated=True, text="kalimat ke {i}."):
    snippets = tuple(yt.Snippet(text.format(i=i), i * step, step) for i in range(n))
    return yt.Transcript(snippets, "id", generated)


@pytest.mark.parametrize("url, video_id", URLS.items())
def test_every_url_form_gives_the_video_id(url, video_id):
    assert yt.extract_video_id(url) == video_id


@pytest.mark.parametrize("url", ["https://www.youtube.com/playlist?list=PL123", "https://www.youtube.com/@MalakaProjectid",
                                 "https://vimeo.com/123456789", "not a url"])
def test_playlists_channels_and_other_sites_are_not_videos(url):
    assert yt.extract_video_id(url) is None


def test_titles_lose_invisible_characters_and_names_are_cut_between_words():
    assert yt.clean_text("⁠Trauma, Gen Z,​ dan  Bapak") == "Trauma, Gen Z, dan Bapak"
    long_title = "Trader Sejati = Berani CUTLOSS, Cintain Cuannya Bukan Coin-nya #TheInnerCircle KJo"
    name = yt.slugify(long_title)
    assert len(name) <= 64 and name == "trader-sejati-berani-cutloss-cintain-cuannya-bukan-coin-nya"
    assert yt.build_name(metadata(title="Timothy Ronald Show", live=True, upload_date="2026-10-05")) == "timothy-ronald-show-2026-10-05"
    assert yt.build_name(metadata(title="!!!")) == "video-Qft-J2LG0NM"


def test_sound_markers_are_removed_unless_kept():
    assert yt.spoken("[musik] Oke, jadi kita [tertawa] live [ __ ] ya [Music]", False) == "Oke, jadi kita live ya"
    assert yt.spoken("[musik] Oke", True) == "[musik] Oke"
    assert yt.spoken("pasal [12] ayat", False) == "pasal [12] ayat"          # numbers in brackets are speech


def test_the_summary_line_drops_links_hashtags_and_separators():
    assert yt.summary_line(metadata().summary) == "Kali ini kita ngobrol bareng KJo soal trading. Twitch"


def test_the_spoken_language_comes_first():
    fetcher = yt.TranscriptFetcher(["original", "id", "en"])
    assert fetcher.languages_for("en-US") == ["en-US", "en", "id"]
    assert fetcher.languages_for("") == ["id", "en"]
    assert yt.TranscriptFetcher(["en"]).languages_for("ja") == ["en"]


def test_chapters_become_headings_and_text_before_the_first_one_is_kept():
    chapters = (yt.Chapter(100.0, "Awal Mula Masuk Crypto"), yt.Chapter(300.0, "Cut Loss"))
    body = yt.build_body(transcript(n=40), metadata(chapters=chapters), with_timestamps=False)
    assert body.index("kalimat ke 0.") < body.index("### 00:01:40 Awal Mula Masuk Crypto") < body.index("kalimat ke 10.")
    assert body.index("kalimat ke 29.") < body.index("### 00:05:00 Cut Loss") < body.index("kalimat ke 30.")
    timed = yt.build_body(transcript(n=3), metadata(), with_timestamps=True)
    assert timed.splitlines() == ["[00:00:00] kalimat ke 0.", "[00:00:10] kalimat ke 1.", "[00:00:20] kalimat ke 2."]


def test_the_header_is_valid_yaml_with_the_metadata():
    chapters = (yt.Chapter(0.0, "Intro"), yt.Chapter(90.0, "Awal: crypto \"pertama\""))
    document = yt.build_document(metadata(chapters=chapters), transcript(n=60, text="[musik] kalimat ke {i}."))
    header, body = document.split("---\n")[1], document.split("---\n", 2)[2]
    fields = yaml.safe_load(header)
    assert fields["name"] == "trader-sejati-berani-cutloss"
    assert fields["title"] == "Trader Sejati = Berani CUTLOSS"            # without the invisible character
    assert fields["duration"] == "10:00" and fields["duration_seconds"] == 600
    assert fields["category"] == "People & Blogs" and fields["tags"] == ["crypto", "trading"]
    assert fields["captions"] == "auto-generated" and fields["caption_coverage"] == 1.0
    assert fields["chapters"] == ["00:00:00 Intro", '00:01:30 Awal: crypto "pertama"']
    assert fields["words"] == 60 * 3 and fields["live_recording"] is False
    assert fields["description"].startswith('Transcript of the YouTube video "Trader Sejati = Berani CUTLOSS" by Theresa Learns '
                                            "(10:00; language id, auto-generated captions; uploaded 2026-10-04). Video summary:")
    assert len(fields["description"]) <= 1024
    assert "## Video description" in body and "https://www.twitch.tv/x" in body     # the full description stays
    assert "[musik]" not in body.split("## Transcript")[1]


def test_low_coverage_is_measured_and_unknown_duration_is_null():
    assert yt.coverage(metadata(duration=1200.0), transcript(n=60)) == 0.5
    fields = yaml.safe_load(yt.build_document(metadata(duration=0.0, source="oembed"), transcript()).split("---\n")[1])
    assert fields["caption_coverage"] is None and "duration" not in fields and fields["metadata_source"] == "oembed"


class FakeFetcher:
    def __init__(self, *outcomes):
        self.outcomes, self.asked = list(outcomes), []

    def fetch(self, video_id, spoken_language=""):
        self.asked.append(video_id)
        outcome = self.outcomes.pop(0) if self.outcomes else transcript()
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def test_a_skipped_category_costs_no_transcript_request(monkeypatch, tmp_path):
    monkeypatch.setattr(yt, "fetch_metadata", lambda video_id, proxy=None, supadata=None: metadata(video_id=video_id, category="Gaming"))
    fetcher = FakeFetcher()
    settings = yt.Settings(output_dir=tmp_path, skip_categories=frozenset({"gaming", "film & animation"}))
    result = yt.process("https://youtu.be/NJD_0BtZrlA", settings, fetcher)
    assert (result.status, fetcher.asked) == ("skipped", [])
    assert "Gaming" in result.detail
    monkeypatch.setattr(yt, "fetch_metadata", lambda video_id, proxy=None, supadata=None: metadata(video_id=video_id))
    assert yt.process("https://youtu.be/Qft-J2LG0NM", settings, fetcher).status == "ok"
    assert (tmp_path / "trader-sejati-berani-cutloss-Qft-J2LG0NM.txt").exists()


def test_two_blocked_videos_in_a_row_stop_the_batch(monkeypatch, tmp_path):
    monkeypatch.setattr(yt, "fetch_metadata", lambda video_id, proxy=None, supadata=None: metadata(video_id=video_id))
    monkeypatch.setattr(yt.time, "sleep", lambda seconds: None)
    blocked = IpBlocked("Qft-J2LG0NM")
    fetcher = FakeFetcher(transcript(), blocked, blocked, blocked, blocked)
    monkeypatch.setattr(yt, "TranscriptFetcher", lambda languages, proxy=None: fetcher)
    sources = ["Qft-J2LG0NM", "gqCEJ1McXCQ", "Pc3GWaOWHLk", "MOl6qqoJKWA", "56HmqxOTK0U"]
    results = yt.run(sources, yt.Settings(output_dir=tmp_path, retries=2, block_delay=0.0), delay=0.0)
    assert [r.status for r in results] == ["ok", "failed", "failed", "failed", "failed"]
    assert fetcher.asked == ["Qft-J2LG0NM", "gqCEJ1McXCQ", "gqCEJ1McXCQ", "Pc3GWaOWHLk", "Pc3GWaOWHLk"]  # 2 attempts each, then stop
    assert results[-1].detail.startswith("tidak dicoba")
    assert yt.report(results, tmp_path) == 1
    assert (tmp_path / "failed_urls.txt").read_text(encoding="utf-8").count("\n") == 8   # comment + URL per failure


def test_a_permanent_error_is_not_retried(monkeypatch, tmp_path):
    monkeypatch.setattr(yt, "fetch_metadata", lambda video_id, proxy=None, supadata=None: metadata(video_id=video_id))
    fetcher = FakeFetcher(NoTranscriptFound("Qft-J2LG0NM", ["id"], None))
    result = yt.process("Qft-J2LG0NM", yt.Settings(output_dir=tmp_path, retries=3), fetcher)
    assert result.status == "failed" and len(fetcher.asked) == 1 and not result.blocked


def test_long_documents_are_split_between_paragraphs():
    document = "\n\n".join(f"paragraf {i} " + "x" * 90 for i in range(50))
    parts = skill.split_parts(document, size=1000)
    assert all(len(p) <= 1000 for p in parts) and "\n\n".join(parts) == document
    assert skill.split_parts("y" * 2500, size=1000) == ["y" * 1000, "y" * 1000, "y" * 500]


def test_the_tool_pages_through_a_long_video(monkeypatch):
    document = "---\nname: x\n---\n\n" + "\n\n".join(f"paragraf {i} " + "x" * 300 for i in range(100))
    monkeypatch.setattr(skill, "fetch_transcript", lambda url, language="", with_timestamps=False: {"document": document})
    first = skill.get_youtube_transcript.invoke({"url": "https://youtu.be/Qft-J2LG0NM"})
    assert first.startswith("---\nname: x") and first.endswith("call again with part=2 for the rest]")
    total = int(first.rsplit(" of ", 1)[1].split(";")[0])
    last = skill.get_youtube_transcript.invoke({"url": "https://youtu.be/Qft-J2LG0NM", "part": total + 5})
    assert last.endswith(f"[part {total} of {total}; this is the end]")


def test_the_tool_explains_failures_without_inventing_text(monkeypatch):
    reply = skill.get_youtube_transcript.invoke({"url": "video investasi saham untuk pemula"})
    assert "Not a YouTube video" in reply and "use web search" in reply

    def blocked(url, language="", with_timestamps=False):
        raise IpBlocked("Qft-J2LG0NM")
    monkeypatch.setattr(skill, "fetch_transcript", blocked)
    reply = skill.get_youtube_transcript.invoke({"url": "Qft-J2LG0NM"})
    assert "refusing requests" in reply and "Do not write a transcript yourself" in reply


# ---------------------------------------------------------------------------
# No model and no LangChain: everything is made by code
# ---------------------------------------------------------------------------

def test_fetch_transcript_returns_metadata_and_text_by_code_alone(monkeypatch):
    chapters = (yt.Chapter(0.0, "Intro"), yt.Chapter(300.0, "Cut Loss"))
    calls = []

    def fetch_video(video_id, settings, sources):
        calls.append(video_id)
        return metadata(video_id=video_id, chapters=chapters), transcript(n=60), ""
    monkeypatch.setattr(skill._yt, "fetch_video", fetch_video)
    skill._records.clear()
    record = skill.fetch_transcript("https://youtu.be/Qft-J2LG0NM?si=x")
    assert set(record) == {"metadata", "video_description", "transcript", "document"}
    assert record["metadata"]["title"] == "Trader Sejati = Berani CUTLOSS" and record["metadata"]["duration"] == "10:00"
    assert record["metadata"]["chapters"] == ["00:00:00 Intro", "00:05:00 Cut Loss"]
    assert record["transcript"].startswith("### 00:00:00 Intro") and "### 00:05:00 Cut Loss" in record["transcript"]
    assert record["document"] == yt.render_document(record["metadata"], record["video_description"], record["transcript"])
    assert skill.fetch_transcript("Qft-J2LG0NM") is record and calls == ["Qft-J2LG0NM"]     # the second call is from memory
    with pytest.raises(ValueError):
        skill.fetch_transcript("https://www.youtube.com/@MalakaProjectid")


NO_LLM_CHECK = r"""
import sys
sys.modules["langchain_core"] = None          # as if LangChain were not installed
sys.path.insert(0, sys.argv[1])
from skills.youtube_transcript import youtube_transcript_skill as skill
sys.path.insert(0, sys.argv[2])
import yt_transcripts
loaded = {name.split(".")[0] for name, module in sys.modules.items() if module is not None}
models = sorted(loaded & {"openai", "anthropic", "ollama", "langchain", "langchain_core",
          "langchain_openai", "langchain_ollama", "langchain_community", "transformers", "torch", "google"})
print(skill.get_youtube_transcript is None, callable(skill.fetch_transcript), models)
"""


def test_the_skill_imports_no_model_client_and_works_without_langchain():
    import subprocess

    done = subprocess.run([sys.executable, "-c", NO_LLM_CHECK, str(SKILL.parent.parent), str(SKILL / "scripts")],
                          capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == "True True []"


def test_no_source_file_calls_a_model():
    model_calls = re.compile(r"\b(openai|anthropic|ollama|ChatOpenAI|ChatOllama|chat\.completions|/api/chat|/v1/chat|"
                             r"bind_tools|invoke_model|generate_content)\b", re.I)
    sources = [SKILL / "youtube_transcript_skill.py", *sorted((SKILL / "scripts").glob("*.py"))]
    found = {p.name: model_calls.findall(p.read_text(encoding="utf-8")) for p in sources}
    assert all(not hits for hits in found.values()), found


# ---------------------------------------------------------------------------
# Supadata: the fallback while YouTube blocks this IP (HTTP answers are faked; no key, no network)
# ---------------------------------------------------------------------------

class FakeResponse:
    def __init__(self, status, payload):
        self.status, self._body = status, json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def fake_supadata(monkeypatch, answers):
    """Answer Supadata requests in order; returns the list of requested URLs."""
    asked = []

    def urlopen(request, timeout=None):
        asked.append(request.full_url)
        assert request.headers["X-api-key"] == "test-key"
        status, payload = answers.pop(0)
        if status >= 400:
            raise urllib.error.HTTPError(request.full_url, status, "error", {}, io.BytesIO(json.dumps(payload).encode()))
        return FakeResponse(status, payload)
    monkeypatch.setattr(yt.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(yt.time, "sleep", lambda seconds: None)
    return asked


CONTENT = {"content": [{"text": "[musik] Halo semua", "offset": 0, "duration": 4000, "lang": "id"},
                       {"text": "selamat datang", "offset": 596000, "duration": 4000, "lang": "id"}], "lang": "id"}


def test_supadata_reads_captions_in_milliseconds_and_never_generates_them(monkeypatch):
    asked = fake_supadata(monkeypatch, [(200, CONTENT)])
    result = yt.SupadataFetcher("test-key", ["original", "id", "en"]).fetch("Qft-J2LG0NM", "en-US")
    assert "mode=native" in asked[0] and "lang=en" in asked[0] and "text=false" in asked[0]
    assert result.source == "supadata" and result.is_generated is None and result.end == 600.0
    assert yt.caption_kind(result) == "unknown"


def test_a_long_video_is_a_job_to_wait_for(monkeypatch):
    asked = fake_supadata(monkeypatch, [(202, {"jobId": "job-1"}), (200, {"status": "active"}), (200, {"status": "completed", **CONTENT})])
    result = yt.SupadataFetcher("test-key", ["id"]).fetch("MOl6qqoJKWA")
    assert asked[1].endswith("/transcript/job-1") and len(result.snippets) == 2


@pytest.mark.parametrize("status, payload, kind, words", [
    (206, {"error": "transcript-unavailable", "details": "No captions"}, yt.SupadataNoTranscript, "tidak ada caption"),
    (401, {"error": "unauthorized"}, yt.SupadataError, "API key"),
    (402, {"error": "upgrade-required"}, yt.SupadataError, "kredit bulan ini habis"),
])
def test_supadata_errors_say_what_to_do(monkeypatch, status, payload, kind, words):
    fake_supadata(monkeypatch, [(status, payload)])
    with pytest.raises(kind, match=words):
        yt.SupadataFetcher("test-key", ["id"]).fetch("Qft-J2LG0NM")


def test_auto_turns_to_supadata_when_youtube_blocks_and_stays_there(monkeypatch):
    blocked = IpBlocked("Qft-J2LG0NM")
    youtube = FakeFetcher(blocked, blocked, blocked)
    monkeypatch.setattr(yt, "TranscriptFetcher", lambda languages, proxy=None: youtube)
    asked = fake_supadata(monkeypatch, [(200, CONTENT), (200, CONTENT)])
    sources = yt.TranscriptSources(yt.Settings(retries=3, supadata_key="test-key"))
    assert sources.fetch("Qft-J2LG0NM", "id").source == "supadata"
    assert sources.fetch("gqCEJ1McXCQ", "id").source == "supadata"
    assert youtube.asked == ["Qft-J2LG0NM"]          # one try, no retries on a block, and not asked again
    assert len(asked) == 2


def test_without_a_key_auto_keeps_to_youtube_and_supadata_needs_one(monkeypatch):
    youtube = FakeFetcher(transcript())
    monkeypatch.setattr(yt, "TranscriptFetcher", lambda languages, proxy=None: youtube)
    sources = yt.TranscriptSources(yt.Settings())
    assert sources.supadata is None and sources.fetch("Qft-J2LG0NM").source == "youtube"
    with pytest.raises(ValueError, match="SUPADATA_API_KEY"):
        yt.TranscriptSources(yt.Settings(provider="supadata"))


def test_webshare_credentials_from_the_environment_become_a_proxy(monkeypatch):
    monkeypatch.delenv("WEBSHARE_PROXY_USERNAME", raising=False)
    assert yt.proxy_config(None) is None
    monkeypatch.setenv("WEBSHARE_PROXY_USERNAME", "user")
    monkeypatch.setenv("WEBSHARE_PROXY_PASSWORD", "secret")
    assert type(yt.proxy_config(None)).__name__ == "WebshareProxyConfig"
    assert type(yt.proxy_config("http://proxy:8080")).__name__ == "GenericProxyConfig"


def test_settings_come_from_the_environment_or_the_nearest_env_file(monkeypatch, tmp_path):
    monkeypatch.delenv("SUPADATA_API_KEY", raising=False)
    (tmp_path / ".env").write_text('OTHER=1\nexport SUPADATA_API_KEY="from-file"\n', encoding="utf-8")
    inner = tmp_path / "a" / "b"
    inner.mkdir(parents=True)
    monkeypatch.chdir(inner)
    assert yt.setting("SUPADATA_API_KEY") == "from-file"
    monkeypatch.setenv("SUPADATA_API_KEY", "from-env")
    assert yt.setting("SUPADATA_API_KEY") == "from-env"
    assert yt.setting("NOT_THERE") is None
