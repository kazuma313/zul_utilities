---
name: subagent-research
description: Use this skill to research multiple distinct topics in parallel. Dispatches independent research subagents simultaneously — each one searches the web and returns a structured report — then hands all findings back to you for synthesis. Use when a question has 2 or more independent research angles that can be investigated simultaneously.
---

# subagent-research

## Overview

Dispatches N stateless research subagents in parallel. Each subagent:
1. Receives a focused topic + suggested queries + conversation context
2. Runs its own web searches independently
3. Returns a structured `ResearchReport` (findings, sources, summary, confidence)

All subagents run simultaneously — wall-clock time equals the slowest single subagent, not the sum of all.

## When to use

- The question has **2 or more independent research angles** (e.g., "compare X vs Y vs Z")
- You need **broad coverage** across different dimensions simultaneously
- The user asks for a comparison, pros/cons of multiple options, or a multi-faceted analysis
- Thinking mode is active and depth + breadth are both expected

**Do NOT use** for:
- Single-topic lookups (use `web_search` directly — faster)
- Simple factual questions
- Questions that don't require web research
- Tasks requiring file creation or mutation (subagents are read-only)

## How to invoke

```python
dispatch_research_subagents(tasks=[
    {
        "topic": "PostgreSQL strengths and weaknesses for OLTP",
        "queries": ["PostgreSQL pros cons 2025", "PostgreSQL scalability limits OLTP"],
        "context": "User wants to choose a database for a high-traffic web app"
    },
    {
        "topic": "MongoDB strengths and weaknesses for document storage",
        "queries": ["MongoDB pros cons 2025", "MongoDB vs relational performance"],
        "context": "User wants to choose a database for a high-traffic web app"
    },
    {
        "topic": "Database selection criteria for high-traffic web apps",
        "queries": ["database selection high traffic web app 2025", "PostgreSQL vs MongoDB migration cost"],
        "context": "User wants to choose a database for a high-traffic web app"
    }
])
```

### Parameter schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `topic` | string | Yes | A focused, specific research topic (1 sentence max) |
| `queries` | list[string] | Recommended | 2-4 web search queries to guide the subagent |
| `context` | string | Recommended | Brief context from the conversation so the subagent can focus its interpretation |

### Caps and limits

- Maximum **5 subagents** per call (configurable via `SUBAGENT_MAX_PARALLEL`)
- Each subagent has a **30-second timeout** (configurable via `SUBAGENT_TIMEOUT_SECONDS`)
- Timed-out or failed subagents return a low-confidence placeholder — partial results are always returned

## Expected output

A JSON array of research reports:

```json
[
  {
    "topic": "PostgreSQL strengths and weaknesses for OLTP",
    "findings": [
      "PostgreSQL excels at ACID compliance and complex queries",
      "Strong ecosystem with mature tooling and extensions",
      "Can struggle with horizontal sharding at very high write volumes"
    ],
    "sources": [
      "https://www.postgresql.org/docs/",
      "https://benchmarks.example.com/pg-vs-mongo"
    ],
    "summary": "PostgreSQL is the leading choice for structured, relational data with strong consistency requirements. It handles OLTP workloads well but requires careful tuning beyond ~10k writes/sec.",
    "confidence": "high"
  },
  ...
]
```

## Workflow after receiving reports

After `dispatch_research_subagents` returns, synthesize the reports in your response:

1. Reference findings by topic: "According to the PostgreSQL research..." / "The MongoDB subagent found..."
2. Compare across topics when relevant
3. Highlight where confidence is low and note limitations
4. Provide a final recommendation that integrates all findings

## Example full workflow

```
User: "Compare React, Vue, and Svelte for a large enterprise dashboard app"

1. create_plan(tasks=[
     "Dispatch parallel research on React, Vue, Svelte",
     "Synthesize comparison and give recommendation"
   ])
2. update_task(0, "in_progress")
3. dispatch_research_subagents(tasks=[
     {"topic": "React for enterprise dashboard apps", "queries": [...], "context": "..."},
     {"topic": "Vue for enterprise dashboard apps", "queries": [...], "context": "..."},
     {"topic": "Svelte for enterprise dashboard apps", "queries": [...], "context": "..."}
   ])
4. update_task(0, "completed") → update_task(1, "in_progress")
5. [synthesize all three reports in the response]
6. update_task(1, "completed")
```
