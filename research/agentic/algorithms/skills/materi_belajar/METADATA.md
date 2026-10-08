---
name: materi-belajar
description: Lesson for one module as a visual HTML page for a beginner - objectives, 3-6 chapters (Apa / Bagaimana / Mengapa penting) with term boxes and step diagrams, an interactive step-by-step demo, summary, multiple-choice quiz, exercises with expected results, and a glossary. Use whenever the user wants material to study - "buatkan materi modul 2", "lanjut modul berikutnya", "bahan ajar", "modul pembelajaran", "pelajaran tentang X", "ajari saya X lengkap dengan kuis/latihan" - or names a module of a syllabus. Pairs with silabus-belajar: with its JSON, the module card is the contract. Runs with a local model through Ollama (the model writes JSON, code builds the page) or with any model that writes the JSON itself.
version: 2.0.0
requires:
  python: ">=3.9"
  pip: []                      # standard library only
  optional:
    - langchain-core (only for the tool create_materi)
  model: a local chat model through Ollama or an OpenAI-compatible server (see RECOMMENDED in scripts/generate_materi.py), or none when the JSON is written elsewhere
  network: the model server only (localhost:11434 by default)
entry: materi_belajar_skill.py
functions:
  - generate_materi(topic, silabus_json, module, output, model, files) -> {ok, path, warnings, chapters, questions, exercises, model, stats}
  - build_materi(spec, filename, silabus_json, module, sources) -> {ok, path, warnings, ...}
tools:
  - create_materi (materi_belajar_skill.py; None without langchain-core)
scripts:
  - scripts/generate_materi.py (module card, topic or material -> local model JSON -> page)
  - scripts/read_material.py (PDF, images, docx, pptx, xlsx, html, text, folders, links -> text; images and scans by a vision model)
  - scripts/build_materi.py (JSON -> page, with repairs, rule checks and an arithmetic check)
assets: [template-materi.html, materi.schema.json, prompts/system_prompt.txt]
references: [SKILL-claude.md (the original claude.ai workflow), contoh-materi.html, diagram-recipes.md]
outputs: [html]
pairs_with: silabus_belajar
verified: 2026-10-08 with gemma3:4b, qwen3:4b and qwen3:8b on an RTX 3060 Laptop 6 GB (Ollama 0.32.6, OLLAMA_VULKAN=0), two module cards each, against Claude-written reference specs; results in research/learning_skills_comparison and docs/konsep/model-lokal-untuk-skill-belajar.md
---
