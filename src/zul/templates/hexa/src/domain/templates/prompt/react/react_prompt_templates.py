"""
Prompt template untuk ReAct agent (string murni, tanpa dependensi framework).

Cara pakai:
    `REACT_SYSTEM_PROMPT` adalah nilai default `system_prompt` di
    `build_react_agent`. Edit teksnya untuk mengubah perilaku agent, atau
    kirim prompt lain saat merakit agent:

    agent = build_react_agent(llm=llm, tools=tools, system_prompt=MY_PROMPT)

Tips menulis system prompt:
    - Sebutkan peran agent dan batasannya.
    - Jelaskan kapan harus memakai tool dan kapan menjawab langsung.
    - Tentukan bahasa dan gaya jawaban.
"""

REACT_SYSTEM_PROMPT = """\
You are a helpful AI assistant.

Think step by step. When a tool can give you facts you do not have, call it
instead of guessing. Once you have enough information, answer the user directly
and concisely, in the same language the user used.
"""
