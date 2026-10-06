"""
Contoh tool baca data: cuaca di suatu lokasi.

Gunanya:
    Placeholder untuk menunjukkan bentuk tool. Ganti isi fungsi dengan
    pemanggilan API cuaca sungguhan.

Cara pakai:
    from src.infrastructure.AI.tools.weather_tool import get_weather, tools

    agent = build_react_agent(llm=llm, tools=tools)

    get_weather.invoke({"location": "sf"})    # memanggil tool tanpa agent

`tools` adalah daftar tool di file ini, siap diberikan ke perakit agent.
"""

from langchain.tools import tool


@tool
def get_weather(location: str):
    """Call to get the weather from a specific location."""
    # Ini baru tempat penampung dengan jawaban tetap, hanya supaya alur
    # agent bisa dicoba tanpa layanan luar. Ganti isi fungsi dengan
    # pemanggilan API cuaca sungguhan saat tool mulai dipakai.
    if any(city in location.lower() for city in ["sf", "san francisco"]):
        return (
            "It's sunny in San Francisco, "
            "but you better look out if you're a Gemini 😈."
        )

    return f"I am not sure what the weather is in {location}"


tools = [get_weather]
