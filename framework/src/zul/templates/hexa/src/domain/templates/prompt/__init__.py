"""
System prompt statis, satu subfolder per agent.

Gunanya:
    Prompt adalah aturan perilaku agent, jadi disimpan di domain sebagai
    string Python murni. Mengubah perilaku agent cukup dengan mengedit file
    di sini, tanpa menyentuh graph.

Cara pakai:
    from src.domain.templates.prompt.react.react_prompt_templates import (
        REACT_SYSTEM_PROMPT,
    )

    agent = build_react_agent(llm=llm, tools=tools, system_prompt=REACT_SYSTEM_PROMPT)

Prompt yang perlu dirakit dari data runtime tempatnya di
`src/application/prompts/`.
"""
