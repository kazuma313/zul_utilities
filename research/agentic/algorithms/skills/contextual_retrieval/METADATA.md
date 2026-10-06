---
name: contextual-retrieval
description: Prepare documents for a vector database or RAG with Anthropic's contextual retrieval - split a document into chunks and put a short context in front of each one (which document, source and section it is from, and what it is about) so that embeddings and BM25 find the right chunk. Runs on a local model (Ollama); every context is checked by code and dropped if it adds names or numbers that are not in the document. Use when the user wants notes, Markdown, documentation or YouTube transcripts chunked, contextualized, embedded or loaded into a knowledge base. Output is JSONL, one chunk per line.
version: 1.0.0
requires:
  python: ">=3.9"
  pip: []                      # standard library only
  optional:
    - PyYAML (reads YAML front matter; a simple reader is used without it)
    - langchain-core (only for the tool contextualize_document)
  model: a local chat model through Ollama or an OpenAI-compatible server; none with --no-llm
  embeddings: optional, e.g. nomic-embed-text through Ollama (--embed)
entry: contextual_retrieval_skill.py
functions:
  - contextualize_file(path, model, use_model, base_url, embed, language) -> list of records
  - contextualize_text(text, title, source, ...) -> list of records
  - write_jsonl(records, path)
tools:
  - contextualize_document (contextual_retrieval_skill.py; None without langchain-core)
scripts:
  - scripts/contextualize.py (files -> JSONL)
env:
  SKILL_MODEL: one model for every skill instead of the recommended one
outputs: [jsonl]
source: https://www.anthropic.com/engineering/contextual-retrieval
---
