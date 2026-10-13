"""
Node dan routing untuk agent human-in-the-loop.

Gunanya:
    `should_continue`     ke `human_review` jika LLM meminta tool call
    `make_human_review`   node yang berhenti menunggu keputusan manusia
    `make_tool_node`      menjalankan tool call yang tidak ditolak

Format payload interrupt dan keputusan mengikuti HITL LangChain
(`action_requests` / `review_configs` / `decisions`), supaya UI atau client
yang sudah mengenal format itu bisa langsung dipakai.

Contoh payload yang diterima manusia:
    {
        "action_requests": [
            {"name": "send_email", "args": {"to": "alice@example.com", ...},
             "description": "Tool `send_email` menunggu persetujuan"}
        ],
        "review_configs": [
            {"action_name": "send_email",
             "allowed_decisions": ["approve", "edit", "reject"]}
        ],
    }

Aturan `interrupt()` yang harus dijaga saat mengubah file ini:
    - Jangan taruh side effect sebelum `interrupt()`: node dijalankan ulang
      dari awal saat di-resume.
    - Jangan bungkus `interrupt()` dengan try/except umum: ia bekerja
      dengan melempar exception khusus.
    - Payload harus JSON-serializable.
"""

from collections.abc import Collection, Sequence
from typing import Any, Literal

from langchain.messages import AIMessage, AnyMessage, ToolCall, ToolMessage
from langchain.tools import BaseTool
from langgraph.graph import END
from langgraph.types import Command, interrupt
from pydantic import ValidationError

from src.domain.entities.agents.react.react import AgentState

# --------------------------------------------------------------------------
# Keputusan Review
# --------------------------------------------------------------------------
#
# Tiga jenis keputusan yang boleh diberikan manusia untuk satu aksi. Saat
# sebuah aksi ditolak tanpa alasan, pesan bawaan di bawah ini dikirim
# ke LLM sebagai hasil tool supaya ia tahu aksinya tidak jalan.
#

ALLOWED_DECISIONS = ["approve", "edit", "reject"]

REJECTED_BY_USER_MESSAGE = "User rejected this action. It was not executed."

APPROVE = {"type": "approve"}

NO_DECISION = {
    "type": "reject",
    "message": "No decision was given for this action. It was not executed.",
}

# --------------------------------------------------------------------------
# Routing
# --------------------------------------------------------------------------


def should_continue(state: AgentState) -> Literal["human_review", END]:
    """Pilih langkah berikutnya: minta review manusia, atau selesai."""
    if state["messages"][-1].tool_calls:
        return "human_review"

    return END


# --------------------------------------------------------------------------
# Node Review
# --------------------------------------------------------------------------


def build_review_request(tool_calls: Sequence[ToolCall]) -> dict[str, Any]:
    """Payload yang ditampilkan ke manusia. Harus JSON-serializable."""
    return {
        "action_requests": [
            {
                "name": tool_call["name"],
                "args": tool_call["args"],
                "description": f"Tool `{tool_call['name']}` menunggu persetujuan",
            }
            for tool_call in tool_calls
        ],
        "review_configs": [
            {"action_name": tool_call["name"], "allowed_decisions": ALLOWED_DECISIONS}
            for tool_call in tool_calls
        ],
    }


def _apply_decision(
    tool_call: ToolCall, decision: dict[str, Any]
) -> tuple[ToolCall, ToolMessage | None]:
    """Terapkan satu keputusan: tool call hasil revisi dan pesan penolakannya."""
    if decision["type"] == "edit":
        edited_action = decision["edited_action"]
        edited_call = {
            **tool_call,
            "name": edited_action["name"],
            "args": edited_action["args"],
        }

        return edited_call, None

    if decision["type"] == "reject":
        # Penolakan disampaikan ke LLM sebagai hasil tool berstatus error.
        # Dengan begitu riwayat percakapan tetap sah bagi provider LLM,
        # karena setiap tool call tetap mempunyai ToolMessage-nya.
        rejection = ToolMessage(
            content=decision.get("message") or REJECTED_BY_USER_MESSAGE,
            name=tool_call["name"],
            tool_call_id=tool_call["id"],
            status="error",
        )

        return tool_call, rejection

    return tool_call, None


def make_human_review(tools_requiring_approval: Collection[str]):
    """
    Buat node yang berhenti menunggu keputusan manusia.

    Args:
        tools_requiring_approval: Nama tool yang wajib disetujui manusia sebelum
            dijalankan. Tool lain langsung diteruskan ke tool_node.
    """

    def human_review(state: AgentState) -> Command[Literal["tool_node", "llm_call"]]:
        """Berhenti menunggu keputusan untuk tool call yang butuh persetujuan."""
        ai_message = state["messages"][-1]
        calls_to_review = [
            tool_call
            for tool_call in ai_message.tool_calls
            if tool_call["name"] in tools_requiring_approval
        ]

        if not calls_to_review:
            return Command(goto="tool_node")

        # Saat di-resume, node ini dijalankan lagi dari baris pertama. Jadi
        # tidak boleh ada side effect sebelum interrupt(). Nilai yang ada
        # di Command(resume=...) menjadi nilai kembalian interrupt().
        response = interrupt(build_review_request(calls_to_review))

        reviewed_call_ids = [tool_call["id"] for tool_call in calls_to_review]
        decision_by_call_id = dict(
            zip(reviewed_call_ids, response["decisions"], strict=False)
        )

        # Tool call yang tidak butuh review langsung disetujui. Sebaliknya,
        # aksi yang butuh review tetapi tidak mendapat keputusan dianggap
        # ditolak: tanpa persetujuan, aksi itu tidak boleh berjalan.
        revised_calls, rejections = [], []
        for tool_call in ai_message.tool_calls:
            if tool_call["id"] in reviewed_call_ids:
                decision = decision_by_call_id.get(tool_call["id"], NO_DECISION)
            else:
                decision = APPROVE

            revised_call, rejection = _apply_decision(tool_call, decision)

            revised_calls.append(revised_call)
            if rejection:
                rejections.append(rejection)

        # Pesan hasil review memakai id yang sama dengan pesan aslinya,
        # sehingga reducer add_messages menggantikan AIMessage yang
        # lama dan tidak menambah pesan kedua ke dalam riwayat.
        reviewed_message = ai_message.model_copy(update={"tool_calls": revised_calls})
        has_calls_to_run = len(rejections) < len(revised_calls)

        return Command(
            update={"messages": [reviewed_message, *rejections]},
            goto="tool_node" if has_calls_to_run else "llm_call",
        )

    return human_review


# --------------------------------------------------------------------------
# Node Tool
# --------------------------------------------------------------------------
#
# Node tool di sini ditulis sendiri, bukan memakai ToolNode bawaan. Ia cuma
# menjalankan tool call yang belum punya jawaban, jadi aksi yang sudah
# ditolak manusia tidak ikut dijalankan lagi. Seperti ToolNode, ia
# melaporkan argumen yang salah menjadi pesan error bagi model.
#


def unanswered_tool_calls(messages: Sequence[AnyMessage]) -> list[ToolCall]:
    """Tool call di AIMessage terakhir yang belum punya ToolMessage."""
    last_ai_index = max(
        index
        for index, message in enumerate(messages)
        if isinstance(message, AIMessage)
    )
    answered_call_ids = {
        message.tool_call_id
        for message in messages[last_ai_index + 1 :]
        if isinstance(message, ToolMessage)
    }

    return [
        tool_call
        for tool_call in messages[last_ai_index].tool_calls
        if tool_call["id"] not in answered_call_ids
    ]


def make_tool_node(tools: Sequence[BaseTool]):
    """Buat node yang menjalankan tool call yang lolos review."""
    tools_by_name = {tool.name: tool for tool in tools}

    def run_tool(tool_call: ToolCall) -> ToolMessage:
        tool = tools_by_name.get(tool_call["name"])

        if tool is None:
            return ToolMessage(
                content=f"Error: {tool_call['name']} is not a valid tool, "
                f"try one of {sorted(tools_by_name)}.",
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
                status="error",
            )

        # Argumen yang tidak cocok dengan skema tool, baik dari model maupun
        # hasil suntingan manusia, dilaporkan ke model sebagai hasil tool
        # dengan status error. Jadi riwayat tetap utuh dan model dapat
        # memperbaiki argumennya, seperti perilaku ToolNode bawaan.
        try:
            return tool.invoke(tool_call)
        except ValidationError as error:
            problems = "; ".join(
                f"{'.'.join(map(str, problem['loc']))}: {problem['msg']}"
                for problem in error.errors()
            )

            return ToolMessage(
                content=f"Error: invalid arguments for {tool.name}. {problems}",
                name=tool.name,
                tool_call_id=tool_call["id"],
                status="error",
            )

    def tool_node(state: AgentState) -> dict:
        """Jalankan tool call yang tidak ditolak."""
        calls_to_run = unanswered_tool_calls(state["messages"])

        return {"messages": [run_tool(tool_call) for tool_call in calls_to_run]}

    return tool_node
