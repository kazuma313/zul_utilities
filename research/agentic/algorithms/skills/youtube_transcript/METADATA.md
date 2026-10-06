---
name: youtube-transcript
description: YouTube video link -> the transcript (what is said in the video) with its metadata: title, channel, upload date, duration, category, tags, chapters, language and caption type. Use when the message contains a youtube.com or youtu.be video link (watch, shorts, live, embed) and the user wants what is said in it - a summary, notes, quotes, the main points, or the transcript itself ("ambil transcript", "rangkum video ini", "ubah video jadi teks", "download subtitle"). Not for finding or recommending videos (use web search) and not for pictures. Needs network access to YouTube and pip install youtube-transcript-api yt-dlp; no speech-to-text, so a video without captions has no transcript.
version: 1.1.0
requires:
  python: ">=3.9"
  pip: ["youtube-transcript-api>=1.2", "yt-dlp"]   # yt-dlp is optional: without it only title and channel
  optional:
    - langchain-core (only for the tool get_youtube_transcript; fetch_transcript works without it)
  model: none                  # no language model anywhere; metadata, text and parts are made by code
  network: www.youtube.com
entry: youtube_transcript_skill.py
functions:
  - fetch_transcript(url, language, with_timestamps) -> {metadata, video_description, transcript, document}
tools:
  - get_youtube_transcript (youtube_transcript_skill.py; None without langchain-core)
scripts:
  - scripts/yt_transcripts.py (many URLs -> one .txt per video)
env:                           # read from the environment or the nearest .env file
  SUPADATA_API_KEY: transcript service used only after YouTube blocks this IP (supadata.ai, 100 free a month)
  WEBSHARE_PROXY_USERNAME: rotating residential proxies (with WEBSHARE_PROXY_PASSWORD)
  YT_TRANSCRIPT_PROXY: any proxy URL for the tool (the script takes --proxy)
outputs: [txt]
verified: 2026-10-06 with the 7 videos of evals/sample_urls.txt on a home connection - straight from YouTube, 5 of 5 educational videos with full metadata and 100% caption coverage (7 URLs in 36 s, the gameplay video and the anime clip skipped by category); through Supadata, 2 of 2 (9 and 26 minutes) with word-for-word the same transcript
---
