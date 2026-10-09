---
name: youtube-transcript
description: YouTube video link -> the transcript (what is said in the video) with its metadata: title, channel, upload date, duration, category, tags, chapters, language and caption type. Use when the message contains a youtube.com or youtu.be video link (watch, shorts, live, embed) and the user wants what is said in it - a summary, notes, quotes, the main points, or the transcript itself ("ambil transcript", "rangkum video ini", "ubah video jadi teks", "download subtitle"). Not for finding or recommending videos (use web search) and not for pictures. Needs network access to YouTube and pip install youtube-transcript-api yt-dlp; no speech-to-text, so a video without captions has no transcript.
---

# youtube-transcript

Turns YouTube videos into text: the captions YouTube already has, with the video's metadata in a YAML header. It never transcribes audio and never invents text; a video without captions is reported as such.

No language model is used anywhere in this skill. The captions come from YouTube (or Supadata), the metadata from yt-dlp, and the header, paragraphs, chapter headings and parts are made by code. It runs without a model server and without LangChain (`tests/` checks both).

## From Python, without a model

```python
from utilities.youtube_transcript.youtube_transcript_skill import fetch_transcript

record = fetch_transcript("https://youtu.be/Pc3GWaOWHLk")
record["metadata"]           # dict: title, channel, upload_date, duration, category, tags, chapters, captions, ...
record["transcript"]         # paragraphs, with a "### HH:MM:SS title" heading per chapter
record["document"]           # the same .txt text that scripts/yt_transcripts.py writes
```

`fetch_transcript(url, language="", with_timestamps=False)` raises `ValueError` for a link that is not a video, and the errors of *When it fails* otherwise. The folder `research/agentic/algorithms/` must be on `sys.path`.

## One video, inside a conversation: the tool

```
get_youtube_transcript(url="https://youtu.be/Pc3GWaOWHLk")
get_youtube_transcript(url="https://youtu.be/Pc3GWaOWHLk", part=2)      # the next part of a long video
get_youtube_transcript(url="...", language="en")                        # prefer English captions
```

Part 1 starts with the metadata. A long video comes in parts of about 12 000 characters, and the reply ends with `[part N of M; call again with part=N+1 for the rest]`. Read every part before you summarise the whole video.

## Many videos, or files to keep: the script

```
pip install -r scripts/requirements.txt
python scripts/yt_transcripts.py URL1 URL2 -o transcripts
python scripts/yt_transcripts.py -i urls.txt -o transcripts
```

`urls.txt` holds one URL or video ID per line; blank lines and lines starting with `#` are ignored. Playlist and channel URLs are not supported: ask for the video URLs.

Read the last log line (`N sukses, N dilewati, N gagal`) and the exit code: 0 nothing failed, 1 something failed (listed in `<output>/failed_urls.txt`), 2 no input. Report every failure with its reason, and run the failed ones again later with `-i <output>/failed_urls.txt`.

### Only educational videos from a mixed list

```
python scripts/yt_transcripts.py -i urls.txt -o transcripts --skip-category Gaming "Film & Animation" Music
```

`--skip-category` reads YouTube's own category before fetching the transcript. Do not filter for the category `Education`: podcasts and talks are almost always filed under `Entertainment`, `People & Blogs` or `News & Politics` (5 of 5 educational videos in `evals/sample_urls.txt`). Excluding the categories you do not want works; including only `Education` drops most real lessons.

## Options

| Option | Use |
|---|---|
| `-l original id en` | Language order (the default). `original` is the language spoken in the video; within a language, manual captions come before automatic ones. YouTube also lists machine translations, so `-l id` on an English video gives a translated track. |
| `-t` | One line per caption with `[HH:MM:SS]`; the default is paragraphs. |
| `--skip-category CAT ...` | Skip videos of these YouTube categories (see above). |
| `--keep-sound-tags` | Keep `[musik]`, `[Music]`, `[tertawa]`, `[Applause]` and similar markers; they are removed by default. |
| `--overwrite` | Fetch again although the file exists. Without it, existing videos are skipped, so a run can be repeated safely. |
| `--delay S` | Seconds between videos (default 3). |
| `--provider auto` | Where the transcript comes from. `auto` (default): YouTube, and Supadata only after YouTube blocks this IP, then for the rest of the batch. `youtube` or `supadata` uses only that one. |
| `--proxy URL` | Use a proxy when YouTube blocks this IP. |
| `--retries N`, `--retry-delay S`, `--block-delay S` | Attempts per video, first wait after an error, first wait after a block (default 30 s; both double per attempt). |

## Output

One file per video, `<name>-<videoId>.txt`:

```
---
name: trader-sejati-berani-cutloss-cintain-cuannya-bukan-coin-nya
description: "Transcript of the YouTube video \"...\" by Theresa Learns (44:10; language id, auto-generated captions; uploaded 2026-10-04). Video summary: ..."
title: "Trader Sejati = Berani CUTLOSS, Cintain Cuannya Bukan Coin-nya #TheInnerCircle KJo"
channel: "Theresa Learns"
url: "https://www.youtube.com/watch?v=Qft-J2LG0NM"
upload_date: "2026-10-04"
duration: "44:10"
category: "People & Blogs"
tags: ["crypto", "trading", ...]
transcript_language: "id"
captions: "auto-generated"
caption_coverage: 1.0
words: 6978
chapters: ["00:00:00 Intro dan Teaser", "00:01:30 Awal Mula Masuk Crypto", ...]
---

## Video description

(the uploader's description, unchanged)

## Transcript

### 00:01:30 Awal Mula Masuk Crypto

(paragraphs)
```

- `name` (at most 64 characters, cut between words) and `description` (one line, at most 1024 characters) follow the SKILL.md header format. A recorded live stream gets its date in `name`, because its title is often the same every week.
- `caption_coverage` is the share of the video that the captions reach. Below 0.9 the log warns that the transcript is incomplete.
- `captions: auto-generated` means speech recognition by YouTube: expect misheard words and names. Say so when you quote it.
- Chapters of the video become `###` headings with their start time.

## When YouTube blocks this IP

YouTube limits how often one IP may ask for captions (HTTP 429, `IpBlocked`). On a home connection it happened after about 30 transcript and metadata requests within a few minutes, and it lasted more than half an hour. Waiting is free but slow; two things get the transcript at once:

1. **A transcript service: Supadata.** Its servers ask YouTube, so the block on this IP does not matter. The free plan gives 100 transcripts a month, one request per second, without a card. Sign up at supadata.ai and put the key in the `.env` file at the root of the repository (it is in `.gitignore`):

    ```
    SUPADATA_API_KEY=YOUR_KEY
    ```

    Replace `YOUR_KEY` with the key from the Supadata dashboard. The script and the tool read it from the environment or from the nearest `.env`, and use Supadata only after YouTube refuses, so free videos stay free. They ask only for captions that exist (`mode=native`, 1 credit per video); Supadata can also generate a transcript with AI, but that costs 2 credits per minute of video. Supadata does not say whether captions are automatic, so `captions` is `unknown` and `transcript_source` is `supadata`. The metadata still comes from yt-dlp, which kept working during the block; Supadata's metadata (1 more credit, no category or chapters) is used only when yt-dlp fails.
2. **Rotating residential proxies**, the remedy the youtube-transcript-api authors recommend: set `WEBSHARE_PROXY_USERNAME` and `WEBSHARE_PROXY_PASSWORD` (webshare.io, paid per GB), or pass any proxy with `--proxy URL` (tool: `YT_TRANSCRIPT_PROXY`). A proxy of a cloud provider is usually blocked already.

## When it fails

| Message | Meaning | What to do |
|---|---|---|
| `IpBlocked`, `RequestBlocked`, `HTTP Error 429` | YouTube refuses requests from this IP for a while (see *When YouTube blocks this IP*). | With `SUPADATA_API_KEY` the script turns to Supadata by itself. Without it, after two blocked videos in a row the script stops and lists the rest in `failed_urls.txt`: wait, then run `-i <output>/failed_urls.txt`, or set a key or proxy. Do not retry in a loop. In a sandbox without access to youtube.com only Supadata works. |
| `Supadata menolak API key`, `kredit bulan ini habis` | The key is wrong, or the 100 free credits of this month are used. | Check `.env`, or wait for next month. |
| `TranscriptsDisabled`, `NoTranscriptFound` | The video has no captions. | Permanent; report it. |
| `VideoUnavailable`, `VideoUnplayable`, `AgeRestricted` | Private, removed, or restricted by region or age. | Permanent; report it. |
| `bukan URL/ID video YouTube yang valid` | A wrong URL, a playlist or a channel. | Ask for the video URL. |

The metadata comes from yt-dlp, else from oEmbed (title and channel only), else the video ID is the title; missing metadata never costs the transcript. When `metadata_source` is not `yt-dlp`, tell the user that the duration, category and chapters are missing.

## Files

| File | Purpose |
|---|---|
| `youtube_transcript_skill.py` | `fetch_transcript` (plain Python, no model) and the optional LangChain tool `get_youtube_transcript` |
| `scripts/yt_transcripts.py` | Batch script: URLs -> one `.txt` per video |
| `scripts/requirements.txt` | `youtube-transcript-api`, `yt-dlp` |
| `evals/sample_urls.txt`, `evals/check_metadata.py` | The test videos, and a check that every file has enough metadata and a complete transcript |
| `tests/` | `pytest` tests without network access |
