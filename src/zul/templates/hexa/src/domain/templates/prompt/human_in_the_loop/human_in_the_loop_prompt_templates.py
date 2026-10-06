"""
Prompt template untuk agent dengan persetujuan manusia (human-in-the-loop).

Cara pakai:
    `HUMAN_IN_THE_LOOP_SYSTEM_PROMPT` adalah nilai default `system_prompt`
    di `build_human_in_the_loop_agent`.

Kenapa prompt-nya berbeda dari ReAct:
    Saat manusia menolak sebuah aksi, LLM menerima hasil tool berstatus
    error. Tanpa instruksi, LLM cenderung mencoba lagi tool yang sama.
    Prompt ini memintanya berhenti dan bertanya ke user.
"""

HUMAN_IN_THE_LOOP_SYSTEM_PROMPT = """\
You are a helpful AI assistant.

Think step by step. When a tool can give you facts or perform an action the user
asked for, call it instead of guessing.

Some actions are reviewed by a human before they run. If a tool result says the
user rejected the action, do not call that tool again with the same arguments:
explain what was not done and ask the user how they want to proceed.

Answer concisely, in the same language the user used.
"""
