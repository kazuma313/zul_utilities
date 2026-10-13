"""
Controller chat subagents: supervisor yang mendelegasikan ke subagent spesialis.

Gunanya:
    Composition root pola subagents. `SUBAGENTS` adalah daftar agent
    spesialis yang bisa dipanggil supervisor.

Cara menambah subagent:
    SUBAGENTS.append(
        SubagentSpec(
            name="calendar_agent",
            description="Create and look up calendar events. Give it ...",
            system_prompt=CALENDAR_AGENT_SYSTEM_PROMPT,
            tools=[create_event, list_events],
        )
    )
"""

from functools import lru_cache

from src.application.AI.agents.subagents.subagents import (
    SubagentSpec,
    build_supervisor_agent,
)
from src.application.usecases.chat import ChatUseCase
from src.domain.templates.prompt.subagents.subagents_prompt_templates import (
    EMAIL_AGENT_SYSTEM_PROMPT,
    WEATHER_AGENT_SYSTEM_PROMPT,
)
from src.infrastructure.AI.llm.openai import get_llm_model
from src.infrastructure.AI.memory.checkpointer import get_checkpointer
from src.infrastructure.AI.tools.email_tool import send_email
from src.infrastructure.AI.tools.weather_tool import get_weather

# --------------------------------------------------------------------------
# Daftar Subagent
# --------------------------------------------------------------------------
#
# Nama dan deskripsi adalah satu-satunya hal yang dibaca supervisor saat
# memilih subagent. Tulis deskripsi yang menyebut tugas subagent itu,
# masukan yang dibutuhkannya, dan apa yang akan dikembalikannya.
#

SUBAGENTS = [
    SubagentSpec(
        name="weather_agent",
        description=(
            "Look up current weather for one or more locations. "
            "Give it the location names; it returns the weather for each."
        ),
        system_prompt=WEATHER_AGENT_SYSTEM_PROMPT,
        tools=[get_weather],
    ),
    SubagentSpec(
        name="email_agent",
        description=(
            "Write and send an email. Give it the recipient address and what the "
            "email should say; it returns a confirmation of what was sent."
        ),
        system_prompt=EMAIL_AGENT_SYSTEM_PROMPT,
        tools=[send_email],
    ),
]

# --------------------------------------------------------------------------
# Composition Root
# --------------------------------------------------------------------------


@lru_cache
def get_supervisor_agent():
    """Supervisor yang dilayani `POST /subagents/chat` dan dicoba di playground."""
    return build_supervisor_agent(
        llm=get_llm_model(),
        subagents=SUBAGENTS,
        checkpointer=get_checkpointer(),
    )


@lru_cache
def get_subagents_chat_usecase() -> ChatUseCase:
    return ChatUseCase(get_supervisor_agent())
