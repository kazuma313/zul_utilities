"""
Adapter LLM: OpenAI atau endpoint OpenAI-compatible (vLLM, LiteLLM, Ollama).

Gunanya:
    Satu-satunya tempat yang tahu provider LLM mana yang dipakai. Layer
    application hanya menerima chat model yang sudah jadi, jadi mengganti
    provider cukup dilakukan di file ini atau lewat environment variable.

Cara pakai:
    from src.infrastructure.AI.llm.openai import get_llm_model

    llm = get_llm_model()                          # model dari LLM_MODEL
    llm = get_llm_model(model="gpt-4o")            # model tertentu
    llm = get_llm_model(temperature=0.7)           # jawaban lebih bervariasi

Contoh memakai provider lain (buat file `anthropic.py` di folder ini):
    from langchain_anthropic import ChatAnthropic

    def get_llm_model(temperature: float = 0.0) -> ChatAnthropic:
        return ChatAnthropic(model="claude-sonnet-5-5", temperature=temperature)
"""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# --------------------------------------------------------------------------
# Model Bawaan
# --------------------------------------------------------------------------
#
# Model ini dipakai kalau environment variable LLM_MODEL tidak diisi dan
# pemanggil tidak menyebut nama model. Pilih model yang mendukung tool
# calling, karena semua agent di template ini bergantung padanya.
#

DEFAULT_MODEL = "gpt-4o-mini"


def get_llm_model(temperature: float = 0.0, model: str | None = None) -> ChatOpenAI:
    """
    Buat chat model.

    Environment variables:
        OPENAI_API_KEY  wajib
        LLM_MODEL       nama model (default: gpt-4o-mini)
        LLM_BASE_URL    endpoint custom (opsional)

    Raises:
        ValueError: Jika OPENAI_API_KEY belum diisi.
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError(
            "OPENAI_API_KEY not found! "
            "Please set it in .env file or environment variables"
        )

    return ChatOpenAI(
        model=model or os.getenv("LLM_MODEL", DEFAULT_MODEL),
        temperature=temperature,
        base_url=os.getenv("LLM_BASE_URL") or None,
    )
