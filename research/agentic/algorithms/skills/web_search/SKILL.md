---
name: web-search
description: Use this skill to search the web for current, real-time, or post-training information — news, prices, recent events, documentation updates, or anything that may have changed after the model's knowledge cutoff.
---

# web-search

## Overview

Queries the Tavily Search API and returns the top 5 search results (title, URL, and a 300-character snippet per result). Use this whenever the answer requires up-to-date information.

## When to use

- User asks about recent news, events, or announcements
- User asks about current prices, stock values, or live data
- User asks about the latest version of a library, tool, or product
- User asks about something that happened after mid-2025
- User explicitly says "search for" or "look up"

**Do NOT use** for math (use `math_calculator`), for general knowledge that doesn't require recency, or for reading an uploaded file (use `read_pdf`).

## How to invoke

Call the `web_search` tool with a single `query` argument:

```
web_search(query="<concise 2-10 word search query>")
```

### Input examples

| User request | query to pass |
|---|---|
| "What is the latest Dota 2 patch?" | `Dota 2 latest patch notes 2025` |
| "Current Bitcoin price" | `Bitcoin price today` |
| "LangChain 0.3 release notes" | `LangChain 0.3 release notes changelog` |

### Multi-hop usage (thinking mode)

In thinking mode, you may call `web_search` multiple times if the first result is insufficient. Refine the query based on what you learned and search again.

## Expected output

A formatted string:
```
Search results for: <query>

1. **<title>** <url>
   <snippet>

2. ...
```

## Implementation

See `web_search.py` in this folder.
