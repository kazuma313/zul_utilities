"""
Versi ringkas AI service (dataclass + env var).

Gunanya:
    Memanggil LLM dan model embedding lewat endpoint yang kompatibel
    dengan OpenAI, dengan konfigurasi dari environment variable. Kedua
    model dibuat dan dipanggil lewat zul.adapters.langchain_openai.

Cara pakai (`pip install "zul[llm]"`):
    from zul.utilities.script_helper.ai_models import AIService

    service = AIService()             # membaca LLM_* dan EMBEDDING_*
    answer = service.chat("Halo")     # teks jawaban
    vector = service.embed("teks")    # list[float]

Environment variable yang dibaca:
    LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, LLM_TEMPERATURE
    EMBEDDING_BASE_URL, EMBEDDING_API_KEY, EMBEDDING_MODEL

Untuk versi lengkap (validasi Pydantic, config YAML/JSON, response model)
pakai `zul.utilities.embedding_service`.
"""

import os
from dataclasses import dataclass, field

from zul.adapters import langchain_openai as openai_adapter

# --------------------------------------------------------------------------
# Konfigurasi
# --------------------------------------------------------------------------
#
# Nilai bawaan dibaca dari environment variable saat objek dibuat,
# bukan ketika modul diimpor. Jadi load_dotenv() bisa dipanggil
# setelah impor, dan API key yang kosong ditolak sejak awal.
#


@dataclass
class LLMConfig:
    """Configuration for LLM model"""

    base_url: str = field(
        default_factory=lambda: os.getenv("LLM_BASE_URL", "https://llmservice.air.id")
    )
    api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    model: str = field(
        default_factory=lambda: os.getenv("LLM_MODEL", "qwen2-32B-Instruct-resolved")
    )
    temperature: float = field(
        default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.1"))
    )

    def __post_init__(self):
        if not self.api_key or self.api_key == "your-llm-api-key":
            raise ValueError("Valid LLM API key is required")


@dataclass
class EmbeddingConfig:
    """Configuration for Embedding model"""

    base_url: str = field(default_factory=lambda: os.getenv("EMBEDDING_BASE_URL", ""))
    api_key: str = field(default_factory=lambda: os.getenv("EMBEDDING_API_KEY", ""))
    model: str = field(
        default_factory=lambda: os.getenv("EMBEDDING_MODEL", "Qwen3-Embedding-4B")
    )

    def __post_init__(self):
        if not self.api_key or self.api_key == "your-embedding-api-key":
            raise ValueError("Valid Embedding API key is required")


@dataclass
class AIConfig:
    """Main AI Service Configuration"""

    llm_config: LLMConfig = field(default_factory=LLMConfig)
    embedding_config: EmbeddingConfig | None = field(default_factory=EmbeddingConfig)
    enable_embedding: bool = True


# --------------------------------------------------------------------------
# AI Service
# --------------------------------------------------------------------------
#
# Atribut llm dan embedding berisi ChatOpenAI dan OpenAIEmbeddings buatan
# adapter. Keduanya tetap atribut publik agar kode lama yang memakainya
# tidak rusak, tetapi cara yang dianjurkan ialah chat() dan embed().
#


class AIService:
    def __init__(self, config: AIConfig | None = None):
        # Gunakan default config jika tidak diberikan
        self.config = config or AIConfig()

        # Initialize LLM dengan konfigurasi terpisah
        self.llm = openai_adapter.create_chat_model(
            base_url=self.config.llm_config.base_url,
            api_key=self.config.llm_config.api_key,
            model=self.config.llm_config.model,
            temperature=self.config.llm_config.temperature,
        )

        # Initialize embedding dengan konfigurasi terpisah (optional)
        self.embedding = None
        if self.config.enable_embedding and self.config.embedding_config:
            self.embedding = openai_adapter.create_embeddings(
                base_url=self.config.embedding_config.base_url,
                api_key=self.config.embedding_config.api_key,
                model=self.config.embedding_config.model,
            )

    def chat(self, prompt: str) -> str:
        """Generate response text from LLM"""
        try:
            return openai_adapter.chat(self.llm, prompt).content
        except Exception as e:
            raise RuntimeError(f"Chat failed: {e}") from e

    def embed(self, text: str) -> list:
        """Get embedding for text"""
        if not self.embedding:
            raise ValueError("Embedding not enabled or configured")

        try:
            return openai_adapter.embed_query(self.embedding, text)
        except Exception as e:
            raise RuntimeError(f"Embedding failed: {e}") from e

    def is_embedding_enabled(self) -> bool:
        return self.embedding is not None
