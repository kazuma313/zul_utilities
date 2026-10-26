---
name: infografis-satu-lembar
description: One-sheet 4:5 infographic (1080x1350, Instagram ready) in three layouts. 'adaptif' composes the sheet from 2 to 4 blocks chosen by the shape of the information (time ribbon, stages, flow, comparison, steps, percentages), and each block's height follows its content. 'produk' explains a product or service through a problem, a solution, a worked example and prices. 'linimasa' (timeline) is a ready-made assembly of adaptive blocks for one historical period split into three eras. Use when the user asks for an infographic ("infografis"), a product summary poster or an explainer post for Instagram. The model only fills one short JSON file; a script checks it with plain-language repair messages and draws it, so a small model can drive it. Needs Node.js 18+; PNG and PDF need Edge, Chrome or Chromium.
version: 1.0.0
license: MIT (skill code); the Geist font is loaded from Google Fonts at render time (SIL Open Font License 1.1) and is not bundled
requires:
  python: ">=3.9"                # only the wrapper infografis_satu_lembar_skill.py
  node: ">=18"                   # scripts/*.mjs, no npm packages
  pip: []                        # standard library only
  optional:
    - Microsoft Edge, Google Chrome or Chromium (PNG, PDF)   # without it, --tanpa-gambar still writes infografis.html
    - langchain-core (only for the tools periksa_infografis_tool and buat_infografis_tool)
entry: infografis_satu_lembar_skill.py
functions:
  - periksa_infografis(isi_json) -> str
  - buat_infografis(isi_json, folder_keluar, tanpa_gambar) -> str
tools:
  - periksa_infografis_tool (infografis_satu_lembar_skill.py; None without langchain-core)
  - buat_infografis_tool (infografis_satu_lembar_skill.py; None without langchain-core)
scripts:
  - scripts/cek.mjs (isi.json -> LOLOS or GAGAL lines with the fix)
  - scripts/bangun.mjs (isi.json -> infografis.html, .png, .pdf, then a layout overlap check; draws the produk layout and hands adaptif and linimasa to adaptif.mjs)
  - scripts/adaptif.mjs (the adaptif layout: header, height budget, elastic block heights)
  - scripts/blok_pita.mjs, blok_tahap.mjs, blok_alur.mjs, blok_banding.mjs, blok_langkah.mjs, blok_angka.mjs (one block each: check rules, natural and maximum height, drawing)
  - scripts/linimasa.mjs (the linimasa layout: check rules, and conversion into adaptif blocks)
  - scripts/umum.mjs (text checker, icons, palette that follows the item count, and the overlap script shared by all layouts)
  - scripts/skema.mjs (icons, character limits, item counts, vague words)
assets: [contoh/kosong.json, contoh/tanam_kota.json, contoh/kosong_adaptif.json, contoh/adaptif_cara_menanam.json, contoh/adaptif_dua_kota.json, contoh/kosong_linimasa.json, contoh/majapahit_masa_pudar.json, merek/tanam_kota.json, merek/jejak.json]
references: [references/prompt_satu_tempelan.md, references/katalog_blok.md]
env:
  CHROME_PATH: path to the browser executable used for PNG and PDF
  INFOGRAFIS_OUTPUT_DIR: output folder for relative folder names in the wrapper (default ./hasil)
inputs:
  - isi.json (shape of contoh/kosong.json, contoh/kosong_adaptif.json or contoh/kosong_linimasa.json, chosen by the optional field susunan; item counts per layout; icon names from a fixed list; years as plain numbers)
outputs: [html, png (2160x2700), pdf]
limits:
  text_words: 260 (warning above)
  solution_nodes: 4
  packages: 2 to 4
  adaptif_blocks: 2 to 4, each kind at most once (pita_waktu, tahap, alur, banding, langkah, angka)
  chars_per_field: see scripts/skema.mjs (BATAS)
tested_with:
  engine: Node v24.19.0 and Microsoft Edge on Windows 11; contoh/tanam_kota.json (produk), contoh/majapahit_masa_pudar.json (linimasa), contoh/adaptif_cara_menanam.json and contoh/adaptif_dua_kota.json (adaptif) pass cek.mjs and render without overlapping text
  llm_runner: not yet verified with a live model. The claim that a small model can drive it is untested until the study in framework/studies is run
---
