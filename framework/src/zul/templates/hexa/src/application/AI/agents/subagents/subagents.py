"""
Pola subagents: satu supervisor mengoordinasikan beberapa subagent spesialis.

    User -> supervisor -> (tool call) -> subagent A / subagent B -> supervisor

Gunanya:
    Memecah pekerjaan lintas domain (cuaca, email, database, ...) ke agent
    yang masing-masing punya prompt dan tools sendiri. Setiap subagent
    dibungkus menjadi satu tool ("tool per agent"). Supervisor memilih
    subagent dari nama dan deskripsi tool-nya, mengirim satu query, lalu
    menerima pesan terakhir subagent sebagai hasil tool.

Cara pakai:
    supervisor = build_supervisor_agent(
        llm=llm,
        subagents=[
            SubagentSpec(
                name="weather_agent",
                description="Look up current weather for a location.",
                system_prompt="You are a weather specialist.",
                tools=[get_weather],
            ),
        ],
        checkpointer=InMemorySaver(),
    )
    ChatUseCase(supervisor).execute("cuaca di sf?", thread_id="t1")

Yang perlu diingat:
    - Subagent tidak punya memory: tiap pemanggilan mulai dari konteks
      kosong dan hanya melihat query dari supervisor.
    - Supervisor hanya menerima pesan terakhir subagent, jadi prompt
      subagent harus meminta semua hasil ditaruh di jawaban akhir.
    - Isi `SubagentSpec.llm` untuk memberi subagent model sendiri (misal
      model yang lebih murah); kosongkan untuk memakai model supervisor.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from langchain.tools import BaseTool, tool
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver

from src.application.AI.agents.react.react import build_react_agent
from src.domain.templates.prompt.subagents.subagents_prompt_templates import (
    SUPERVISOR_SYSTEM_PROMPT,
)

# --------------------------------------------------------------------------
# Batas Langkah Subagent
# --------------------------------------------------------------------------
#
# Setiap subagent mempunyai batas langkahnya sendiri untuk satu tugas,
# terpisah dari batas langkah supervisor. Dengan begitu subagent yang
# terus memanggil tool tidak menghabiskan jatah langkah supervisor.
#

MAX_SUBAGENT_STEPS = 15

# --------------------------------------------------------------------------
# Definisi Subagent
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SubagentSpec:
    """
    Definisi satu subagent.

    `name` dan `description` adalah satu-satunya hal yang dilihat supervisor
    saat memilih subagent, jadi tulis sejelas mungkin tugas apa yang ditangani.
    `llm` adalah model khusus subagent ini; None berarti memakai model
    supervisor.
    """

    name: str
    description: str
    system_prompt: str
    tools: Sequence[BaseTool]
    llm: BaseChatModel | None = None


# --------------------------------------------------------------------------
# Perakit
# --------------------------------------------------------------------------


def build_subagent_tool(spec: SubagentSpec, default_llm: BaseChatModel) -> BaseTool:
    """Rakit subagent dari spec-nya lalu bungkus menjadi tool untuk supervisor."""
    subagent = build_react_agent(
        llm=spec.llm or default_llm,
        tools=spec.tools,
        system_prompt=spec.system_prompt,
    )

    # Subagent dirakit tanpa checkpointer, jadi setiap pemanggilan mulai
    # dari percakapan kosong. Supervisor hanya menerima teks pesan
    # terakhirnya, bukan seluruh langkah kerja subagent itu.
    @tool(spec.name, description=spec.description)
    def call_subagent(query: str) -> str:
        result = subagent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            {"recursion_limit": MAX_SUBAGENT_STEPS},
        )

        return str(result["messages"][-1].text)

    return call_subagent


def build_supervisor_agent(
    llm: BaseChatModel,
    subagents: Sequence[SubagentSpec],
    system_prompt: str = SUPERVISOR_SYSTEM_PROMPT,
    checkpointer: BaseCheckpointSaver | None = None,
):
    """
    Rakit supervisor yang mendelegasikan pekerjaan ke subagent.

    Args:
        llm: Chat model supervisor (dan subagent yang tidak punya model sendiri).
        subagents: Definisi subagent yang tersedia.
        system_prompt: Instruksi sistem untuk supervisor.
        checkpointer: Penyimpan percakapan supervisor per thread_id.

    Returns:
        Graph ter-compile; panggil dengan .invoke({"messages": [...]}, config).
    """
    names = [spec.name for spec in subagents]
    duplicated_names = {name for name in names if names.count(name) > 1}

    if duplicated_names:
        raise ValueError(
            f"Nama subagent harus unik, duplikat: {sorted(duplicated_names)}"
        )

    subagent_tools = [build_subagent_tool(spec, default_llm=llm) for spec in subagents]

    return build_react_agent(
        llm=llm,
        tools=subagent_tools,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
    )
