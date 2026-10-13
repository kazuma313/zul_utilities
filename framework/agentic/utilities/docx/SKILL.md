---
name: docx
description: Use this skill whenever the user wants to read, analyze, or create a Word document (.docx). Triggers include requests for "Word doc", ".docx", "report", "memo", "letter", or any structured document with headings, tables, bullets, or formatting. Also use when extracting text from an uploaded .docx file.
---

# docx

## Overview

Two tools:
- **`read_docx`** — extracts text, headings, and tables from an uploaded .docx file
- **`create_docx`** — generates a formatted .docx file from structured JSON content, returns a download URL

## When to use

- User message contains `[Attached Word Document — file_id: ...]`
- User uploads a `.docx` file and asks to read, summarize, or extract information
- User wants to create a Word document, report, memo, or letter
- User wants structured output with headings, bullets, tables, or multi-section formatting

## Tools

### read_docx

```
read_docx(file_id="<thread_id>/<uuid>.docx")
```

### create_docx

```
create_docx(content='{"title":"...","sections":[...]}', filename="report.docx")
```

**Content JSON format:**
```json
{
  "title": "Document Title",
  "author": "Author Name",
  "sections": [
    {"type": "heading1", "text": "Introduction"},
    {"type": "heading2", "text": "Background"},
    {"type": "paragraph", "text": "Body text here."},
    {"type": "bullet",    "items": ["Point A", "Point B", "Point C"]},
    {"type": "numbered",  "items": ["Step 1", "Step 2", "Step 3"]},
    {"type": "table",     "headers": ["Name", "Value", "Note"],
                          "rows": [["Alice", "95", "Top performer"], ["Bob", "82", ""]]},
    {"type": "page_break"}
  ]
}
```

**Image section example:**
```json
{"type": "image", "image_url": "chart_url:/static/charts/abc123.png", "caption": "Figure 1: Correlation Heatmap", "width_inches": 6.0}
```
For `image_url` pass the exact `chart_url:` token returned by `analyze_data` or `generate_chart`.

**Supported section types:**

| type | Required fields | Notes |
|------|-----------------|-------|
| `heading1` | `text` | Large section header |
| `heading2` | `text` | Sub-section header |
| `heading3` | `text` | Sub-sub-section header |
| `paragraph` | `text` | Body text, supports `bold: true` |
| `bullet` | `items` | Unordered list |
| `numbered` | `items` | Ordered list |
| `table` | `headers`, `rows` | Auto-styled with header row |
| `image` | `image_url` | Embed a chart; optional `caption`, `width_inches` (default 6.0) |
| `page_break` | — | Inserts a page break |

## Expected output

`read_docx` returns the document content as structured markdown text.

`create_docx` returns `file_url:/static/downloads/filename.docx` — the frontend renders a download button.

## PDF alternative

If the user needs a PDF, suggest creating the DOCX first and then using LibreOffice or Word to export to PDF. The DOCX skill is preferred for document creation.

## Implementation

See `docx_skill.py` in this folder.
