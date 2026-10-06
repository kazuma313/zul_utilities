"""
Pembuat chat model, satu file per provider.

Cara pakai:
    from src.infrastructure.AI.llm.openai import get_llm_model

    llm = get_llm_model(temperature=0)

Cara menambah provider (misal Ollama):
    # infrastructure/AI/llm/ollama.py
    from langchain_ollama import ChatOllama

    def get_llm_model(temperature: float = 0.0, model: str = "qwen3:8b"):
        return ChatOllama(model=model, temperature=temperature)

    Lalu ganti import `get_llm_model` di controller. Layer application
    tidak perlu diubah karena hanya menerima objek chat model.
"""
