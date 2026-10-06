"""
Pola subagents: satu supervisor dan beberapa agent spesialis.

File:
    subagents.py   `SubagentSpec`, `build_supervisor_agent(...)`

Contoh:
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
    )
"""
