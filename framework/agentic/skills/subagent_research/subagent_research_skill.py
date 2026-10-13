"""Subagent research skill — dispatch_research_subagents tool.

Return value protocol
---------------------
The tool returns a ``subagent_reports:<json>`` prefixed string.
stream.py intercepts this prefix and converts it to a dedicated SSE event:

    SSE {"type": "subagent_done", "count": N, "topics": [...], "reports": [...]}

This keeps the raw JSON out of the model's visible response while still
surfacing it in the frontend's Research Agents activity card.
"""

import json
import logging

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Prefix detected by stream.py to emit the subagent_done SSE event.
_SUBAGENT_REPORTS_PREFIX = "subagent_reports:"


@tool
async def dispatch_research_subagents(tasks: list[dict]) -> str:
    """Dispatch multiple research subagents in parallel for deep, multi-angle research.

    Each subagent independently searches the web on its assigned topic and
    returns a structured report (findings, sources, summary, confidence).
    All subagents run simultaneously — use this instead of sequential web_search
    calls when you need to cover 2 or more independent research angles at once.

    Args:
        tasks: List of research task dicts. Each must have:
            - topic (str): A focused research topic, e.g.
              "PostgreSQL performance characteristics for OLTP workloads"
            - queries (list[str]): 2-4 suggested web search queries for this topic
            - context (str): Brief context from the conversation to focus the subagent

    Returns:
        JSON array of ResearchReport objects, each with:
        - topic, findings (list), sources (list), summary, confidence

    Example:
        dispatch_research_subagents(tasks=[
            {
                "topic": "React for large-scale enterprise apps",
                "queries": ["React enterprise scalability 2025", "React performance large apps"],
                "context": "User is choosing a frontend framework for a 50-person team"
            },
            {
                "topic": "Vue for large-scale enterprise apps",
                "queries": ["Vue enterprise scalability 2025", "Vue vs React team adoption"],
                "context": "User is choosing a frontend framework for a 50-person team"
            }
        ])
    """
    # Lazy import avoids circular dependency at module-load time
    # (this skill is discovered before app.agent.subagent is fully initialised)
    from app.agent.subagent import ResearchTask, run_research_subagents  # noqa: PLC0415

    if not tasks:
        return "No research tasks provided — nothing to dispatch."

    research_tasks: list[ResearchTask] = []
    for t in tasks:
        topic = str(t.get("topic", "")).strip()
        if not topic:
            continue
        research_tasks.append(ResearchTask(
            topic=topic,
            queries=[str(q) for q in t.get("queries", []) if q],
            context=str(t.get("context", "")),
        ))

    if not research_tasks:
        return "All tasks were empty or malformed — nothing to dispatch."

    logger.info(
        "[dispatch_research_subagents] Dispatching %d subagent(s): %s",
        len(research_tasks),
        [t.topic for t in research_tasks],
    )

    reports = await run_research_subagents(
        research_tasks,
        model_profile="general",
    )

    payload = json.dumps(
        [r.model_dump() for r in reports],
        ensure_ascii=False,
    )

    logger.info(
        "[dispatch_research_subagents] %d report(s) ready | confidences: %s",
        len(reports),
        [r.confidence for r in reports],
    )

    # The "subagent_reports:" prefix is intercepted by stream.py and converted
    # to a dedicated SSE event — it never appears as raw text in the chat.
    return f"{_SUBAGENT_REPORTS_PREFIX}{payload}"
