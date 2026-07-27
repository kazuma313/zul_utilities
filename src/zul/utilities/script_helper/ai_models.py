from dataclasses import dataclass, field
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from typing import Optional
import os

@dataclass
class LLMConfig:
    """Configuration for LLM model"""
    base_url: str = field(default_factory=lambda: os.getenv("LLM_BASE_URL", "https://llmservice.air.id"))
    api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "qwen2-32B-Instruct-resolved"))
    temperature: float = field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.1")))
    def __post_init__(self):
        if not self.api_key or self.api_key == "your-llm-api-key":
            raise ValueError("Valid LLM API key is required")

@dataclass
class EmbeddingConfig:
    """Configuration for Embedding model"""
    base_url: str = field(default_factory=lambda: os.getenv("EMBEDDING_BASE_URL", ""))
    api_key: str = field(default_factory=lambda: os.getenv("EMBEDDING_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "Qwen3-Embedding-4B"))
    
    def __post_init__(self):
        if not self.api_key or self.api_key == "your-embedding-api-key":
            raise ValueError("Valid Embedding API key is required")

@dataclass
class AIConfig:
    """Main AI Service Configuration"""
    llm_config: LLMConfig = field(default_factory=LLMConfig)
    embedding_config: Optional[EmbeddingConfig] = field(default_factory=EmbeddingConfig)
    enable_embedding: bool = True


class AIService:
    def __init__(self, config: Optional[AIConfig] = None):
        # Gunakan default config jika tidak diberikan
        self.config = config or AIConfig()
        
        # Initialize LLM dengan konfigurasi terpisah
        self.llm = ChatOpenAI(
            base_url=self.config.llm_config.base_url,
            api_key=self.config.llm_config.api_key,
            model=self.config.llm_config.model,
            temperature=self.config.llm_config.temperature
        )
        
        # Initialize embedding dengan konfigurasi terpisah (optional)
        self.embedding = None
        if self.config.enable_embedding and self.config.embedding_config:
            self.embedding = OpenAIEmbeddings(
                base_url=self.config.embedding_config.base_url,
                api_key=self.config.embedding_config.api_key,
                model=self.config.embedding_config.model
            )
    
    def chat(self, prompt: str) -> str:
        """Generate response from LLM"""
        try:
            response = self.llm.invoke(prompt)
            return response
        except Exception as e:
            raise RuntimeError(f"Chat failed: {e}")
    
    def embed(self, text: str) -> list:
        """Get embedding for text"""
        if not self.embedding:
            raise ValueError("Embedding not enabled or configured")
        
        try:
            return self.embedding.embed_query(text)
        except Exception as e:
            raise RuntimeError(f"Embedding failed: {e}")
    
    def is_embedding_enabled(self) -> bool:
        return self.embedding is not None
    
