---
name: xlsx
description: Use this skill whenever a spreadsheet is involved — reading/analyzing uploaded .xlsx/.csv files, creating new Excel spreadsheets from data, editing tabular data, or generating formatted reports as Excel files. Trigger when the user mentions "spreadsheet", "Excel", ".xlsx", ".csv", or wants data presented in a table/sheet format.
---

# xlsx

## Overview

Three tools:
- **`read_xlsx`** — reads an uploaded .xlsx or .csv file, returns sheet names, column info, and data as markdown tables
- **`create_xlsx`** — generates a new Excel file from JSON data with formatting, returns a download URL
- **`analyze_data`** — runs comprehensive automatic analysis on an uploaded CSV or Excel file with charts

## When to use

- User message contains `[Attached Spreadsheet — file_id: ...]`
- User uploads an `.xlsx` or `.csv` file and asks to read, analyze, or summarize it
- User asks to create a spreadsheet, export data to Excel, or produce a table as a file
- User wants to analyze data and save results as a workbook

## ⚠️ CRITICAL BEHAVIOR FOR analyze_data ⚠️

**DO NOT ASK THE USER WHAT THEY WANT TO DO WITH THE DATA.**
**DO NOT OFFER OPTIONS OR CHOICES.**
**IMMEDIATELY call `analyze_data` when a CSV/Excel file is uploaded.**

The user wants a full analysis right away — just do it.

## Tools

### analyze_data

```
analyze_data(file_id="<thread_id>/<uuid>.csv")
```

Runs immediately when the user uploads a CSV or Excel file. Generates:
- Data overview (rows, columns, types, missing values)
- Statistical summary of all numeric columns + top correlations
- Correlation heatmap chart
- Distribution histograms for numeric columns
- Bar charts for categorical columns
- Time-series trend charts (if date columns detected)

Returns text analysis plus `chart_url:` tokens for each chart generated.

### read_xlsx

```
read_xlsx(file_id="<thread_id>/<uuid>.xlsx", sheet="")
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `file_id` | Yes | From `[Attached File — file_id: ...]` in the message |
| `sheet`   | No  | Sheet name to read. Omit to read all sheets. |

### create_xlsx

```
create_xlsx(data='{"Sheet1": [...]}', filename="report.xlsx")
```

| Parameter  | Required | Description |
|------------|----------|-------------|
| `data`     | Yes | JSON string — see formats below |
| `filename` | Yes | Output filename (must end in .xlsx) |

**Data format — single sheet (array of objects):**
```json
[
  {"Name": "Alice", "Score": 95, "Grade": "A"},
  {"Name": "Bob",   "Score": 82, "Grade": "B"}
]
```

**Data format — multi-sheet (object with sheet names as keys):**
```json
{
  "Sales":    [{"Month": "Jan", "Revenue": 50000}, {"Month": "Feb", "Revenue": 62000}],
  "Summary":  [{"Total": 112000, "Avg": 56000}]
}
```

## Expected output

`read_xlsx` returns sheet data as markdown tables with column stats.

`create_xlsx` returns `file_url:/static/downloads/filename.xlsx` — the frontend renders a download button.

`analyze_data` returns a text analysis block followed by `chart_url:` lines, for example:
```
## Overview
Rows: 1216 | Columns: 30 | ...

chart_url:/static/charts/d45f581331264c49acd38a1237fefc01.png
chart_url:/static/charts/fda29b11e0e449348378eeb1da94ee6f.png
chart_url:/static/charts/c75854ee42d74b9c8f0755f0a36a41ea.png
chart_url:/static/charts/ac23ac1cb3fd486392e1ac780a97caf9.png
```

## ⚠️ Workflow: analyze then report ⚠️

When the user asks for a report (PPT, Word doc) from uploaded data:

**Step 1 — always call `analyze_data` first** to get chart URLs.

**Step 2 — collect every `chart_url:` line** from the tool result. There will be 2–5 charts.

**Step 3 — call `create_pptx` or `create_docx`** using those exact `chart_url:` strings.
- For PPT: use `"layout": "image"` or `"layout": "image_bullets"` — one slide per chart.
- For Word: use `{"type": "image", "image_url": "chart_url:..."}` — one section per chart.

**DO NOT skip step 1. DO NOT invent chart URLs. DO NOT create a document without charts.**

## Implementation

See `xlsx_skill.py` in this folder.
