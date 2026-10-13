---
name: mind-map
description: Draw a mind map (PNG, SVG, PDF, interactive HTML, Markdown or Mermaid) from anything the user gives you - a lesson, chapter, article, notes, a PDF/DOCX file or just a topic. Central topic in the middle, coloured main branches, sub points and details on curved lines, five colour themes, radial or left-to-right layout. Use when the user asks for a mind map, peta pikiran, peta konsep, concept map, ringkasan bercabang or a visual summary of study material. You write a short indented outline; the script lays it out and draws it. Needs Python 3.9+ only for SVG/HTML/MD; PNG/PDF need Edge, Chrome or Chromium.
version: 1.0.0
license: MIT (skill code); Poppins font under the SIL Open Font License 1.1 (assets/fonts/LICENSE-Poppins-OFL.txt)
requires:
  python: ">=3.9"
  pip: []                      # standard library only for SVG/HTML/MD/MMD
  optional:
    - Microsoft Edge, Google Chrome or Chromium (PNG, PDF)   # or pip install cairosvg
    - Pillow (exact PNG cropping)                             # pip install pillow
    - pdftotext (poppler) or pypdf (PDF sources)              # pip install pypdf
    - langchain-core (scripts/langchain_tool.py)
entry: mind_map_skill.py
tools:
  - create_mind_map (scripts/langchain_tool.py)
env:
  PPTX_OUTPUT_DIR: output folder for relative filenames (default ./output)
  POSTER_BROWSER: path to the browser executable used for PNG/PDF
  PPTX_PUBLIC_URL: base URL prefixed to the file name in the tool's reply
inputs:
  - Markdown outline (# root, - branch, indented sub points)   # recommended for small models
  - JSON {"root", "nodes": [{"text", "children"}]}
  - Mermaid `mindmap` block
outputs: [svg, html, png, pdf, md, mmd, json]
limits:
  branches: 8
  children_per_node: 6
  depth_below_root: 3
  text_chars: 90 (longer text becomes a note)
tested_with:
  engine: [Python 3.10, Python 3.11, Chromium (PNG/PDF), rule-based --no-llm path]
  llm_runner: verified 2026-10-03 against live models through Ollama 0.32.6 on a 6 GB laptop GPU - gemma3:4b (default; 16 of 16 maps, 8-98 s; 6 of 6 as an agent), qwen3:4b, qwen3:8b. Numbers and repairs in references/small_models.md; re-run with evals/local_models.py and evals/agent_loop.py
---
