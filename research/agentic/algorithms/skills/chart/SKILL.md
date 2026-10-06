---
name: chart-generator
description: Use this skill to generate and visualize data as charts or graphs. Supports bar, line, scatter, histogram, heatmap, and box plots using pandas, matplotlib, and seaborn.
---

# chart-generator

## Overview

Accepts raw data (JSON or CSV) and a chart configuration, renders the chart using seaborn/matplotlib, saves it as a PNG, and returns a URL the frontend can display.

## When to use

- User asks to "plot", "visualize", "chart", "graph", or "show" data
- User provides a table of numbers and wants to see it visually
- User asks for trend analysis, distribution, or comparison charts
- After web search returns data, user asks to plot it

**Do NOT use** for math calculations (use `math_calculator`) or PDF reading.

## How to invoke

Call the `generate_chart` tool with the following arguments:

```
generate_chart(
    data="<JSON array or CSV string>",
    chart_type="<type>",
    x_col="<column name>",
    title="<chart title>",       # optional, default "Chart"
    y_col="<column name>",       # optional, not needed for histogram
    hue="<column name>",         # optional, for color grouping
)
```

### Supported chart types

| `chart_type` | Best for | Requires `y_col` |
|---|---|---|
| `bar` | Comparing categories | Yes |
| `line` | Trends over time | Yes |
| `scatter` | Correlation between two variables | Yes |
| `histogram` | Distribution of a single variable | No |
| `heatmap` | Correlation matrix of numeric columns | No |
| `box` | Distribution spread / outliers per category | Optional |

### Data format

**JSON** (preferred for structured data):
```json
[{"month":"Jan","sales":100},{"month":"Feb","sales":150},{"month":"Mar","sales":130}]
```

**CSV** (accepted for tabular data):
```
month,sales
Jan,100
Feb,150
Mar,130
```

### Full invocation examples

Bar chart:
```
generate_chart(data='[{"month":"Jan","sales":100},{"month":"Feb","sales":150}]', chart_type="bar", x_col="month", y_col="sales", title="Monthly Sales")
```

Histogram:
```
generate_chart(data='[{"score":75},{"score":88},{"score":92},{"score":60}]', chart_type="histogram", x_col="score", title="Score Distribution")
```

## Expected output

```
Chart generated successfully. chart_url:/static/charts/<uuid>.png
```

The frontend will automatically render the image when it sees `chart_url:` in your response.

## Implementation

See `chart_skill.py` in this folder.
