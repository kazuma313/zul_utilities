---
name: silabus-belajar
description: Learning path for one topic as a visual HTML page - final skills, a module map, module cards with a main question, checkable objectives, terms and an exercise, a weekly schedule, a final project and sources, with progress the reader can tick. Use whenever the user wants to learn something step by step or needs a study plan - "buatkan silabus", "kurikulum", "roadmap belajar", "rencana belajar", "learning path", "saya mau belajar X dari nol", "ajari saya X step by step" - even without the words silabus or HTML. Pairs with materi-belajar, which writes each module's lesson from its card. Runs with a local model through Ollama (the model writes JSON, code builds the page) or with any model that writes the JSON itself.
version: 2.0.0
requires:
  python: ">=3.9"
  pip: []                      # standard library only
  optional:
    - langchain-core (only for the tool create_silabus)
  model: a local chat model through Ollama or an OpenAI-compatible server (see RECOMMENDED in scripts/generate_silabus.py), or none when the JSON is written elsewhere
  network: the model server only (localhost:11434 by default)
entry: silabus_belajar_skill.py
functions:
  - generate_silabus(topic, output, level, goal, hours_per_week, model, files) -> {ok, path, json, warnings, modules, hours, weeks, model, stats}
  - build_silabus(spec, filename, sources, hours_per_week) -> {ok, path, json, warnings, ...}
tools:
  - create_silabus (silabus_belajar_skill.py; None without langchain-core)
scripts:
  - scripts/generate_silabus.py (topic or material -> local model JSON -> page)
  - scripts/read_material.py (PDF, images, docx, pptx, xlsx, html, text, folders, links -> text; images and scans by a vision model)
  - scripts/build_silabus.py (JSON -> page, with repairs and rule checks)
assets: [template-silabus.html, silabus.schema.json, prompts/system_prompt.txt]
references: [SKILL-claude.md (the original claude.ai workflow), contoh-silabus.html, diagram-recipes.md]
outputs: [html, json]
pairs_with: materi_belajar (the JSON's module cards are its contracts)
verified: 2026-10-08 with gemma3:4b, qwen3:4b and qwen3:8b on an RTX 3060 Laptop 6 GB (Ollama 0.32.6, OLLAMA_VULKAN=0), two topics each, against Claude-written reference specs; results in research/learning_skills_comparison and docs/konsep/model-lokal-untuk-skill-belajar.md
---
