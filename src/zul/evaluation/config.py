"""
Pengaturan evaluasi dari environment variable: model penilai, Redis, Milvus.

Gunanya:
    Kunci, kata sandi, dan alamat server dibaca dari environment, tidak
    ditulis di kode atau notebook. Model penilai ragas sengaja dipisah dari
    model yang dinilai: penilai sebaiknya lebih kuat, karena skor dari model
    yang menilai dirinya sendiri tidak berarti apa-apa. Ringkasan setiap
    pengaturan menyamarkan kuncinya, jadi aman dicetak. Hanya butuh library
    standar.

Cara pakai:
    from zul.evaluation.config import JudgeConfig, RedisSettings

    judge = JudgeConfig.from_env()
    print(judge.safe_summary())          # kunci tampil sebagai …1234
    db = RedisSettings.from_env().connect()

Environment variable yang dibaca:
    RAGAS_JUDGE_MODEL, RAGAS_JUDGE_API_KEY (atau OPENAI_API_KEY),
    RAGAS_JUDGE_BASE_URL, RAGAS_EMBEDDING_MODEL, RAGAS_EMBEDDING_API_KEY,
    RAGAS_EMBEDDING_BASE_URL, REDIS_URL atau REDIS_HOST, REDIS_PORT,
    REDIS_PASSWORD, REDIS_USERNAME, REDIS_DB, MILVUS_URI, MILVUS_PORT,
    MILVUS_DB.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote, urlparse

OPENAI_BASE_URL = "https://api.openai.com/v1"


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def mask(secret: str | None) -> str:
    """Empat karakter terakhir sebuah kunci, cukup untuk mengenali kunci mana."""
    if not secret:
        return "(kosong)"
    return f"…{secret[-4:]}"


# --------------------------------------------------------------------------
# Model Penilai
# --------------------------------------------------------------------------
#
# Embedding penilai dipakai answer_relevancy dan boleh memakai endpoint
# yang berbeda dari LLM penilai, misalnya embedding lokal. Kunci dan
# alamatnya jatuh ke milik LLM penilai jika tidak diisi terpisah.
#


@dataclass(frozen=True)
class JudgeConfig:
    """Model penilai ragas: LLM untuk semua metrik, embedding untuk answer_relevancy."""

    model: str = "gpt-4o-mini"
    api_key: str = ""
    base_url: str | None = None
    embedding_model: str = "text-embedding-3-small"
    embedding_api_key: str = ""
    embedding_base_url: str | None = None

    @classmethod
    def from_env(cls) -> JudgeConfig:
        api_key = _env("RAGAS_JUDGE_API_KEY") or _env("OPENAI_API_KEY")
        base_url = _env("RAGAS_JUDGE_BASE_URL") or None
        return cls(
            model=_env("RAGAS_JUDGE_MODEL", "gpt-4o-mini"),
            api_key=api_key,
            base_url=base_url,
            embedding_model=_env("RAGAS_EMBEDDING_MODEL", "text-embedding-3-small"),
            embedding_api_key=_env("RAGAS_EMBEDDING_API_KEY") or api_key,
            embedding_base_url=_env("RAGAS_EMBEDDING_BASE_URL") or base_url,
        )

    def validate(self) -> JudgeConfig:
        """Kembalikan dirinya sendiri, atau ValueError jika kunci penilai kosong."""
        if not self.api_key:
            raise ValueError(
                "Kunci model penilai kosong. "
                "Isi RAGAS_JUDGE_API_KEY atau OPENAI_API_KEY di environment."
            )
        return self

    def safe_summary(self) -> dict[str, Any]:
        """Pengaturan untuk dicetak atau disimpan, dengan kunci yang disamarkan."""
        return {
            "model": self.model,
            "base_url": self.base_url or OPENAI_BASE_URL,
            "api_key": mask(self.api_key),
            "embedding_model": self.embedding_model,
            "embedding_base_url": self.embedding_base_url or OPENAI_BASE_URL,
        }


# --------------------------------------------------------------------------
# Redis Dan Milvus
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class RedisSettings:
    """Koneksi Redis Stack. `REDIS_URL` dipakai jika diisi."""

    host: str = "localhost"
    port: int = 6379
    password: str | None = None
    username: str | None = None
    db: int = 0

    @classmethod
    def from_env(cls) -> RedisSettings:
        url = _env("REDIS_URL")
        if url:
            parsed = urlparse(url)
            return cls(
                host=parsed.hostname or "localhost",
                port=parsed.port or 6379,
                password=unquote(parsed.password) if parsed.password else None,
                username=unquote(parsed.username) if parsed.username else None,
                db=int(parsed.path.lstrip("/") or 0),
            )
        return cls(
            host=_env("REDIS_HOST", "localhost"),
            port=int(_env("REDIS_PORT", "6379")),
            password=_env("REDIS_PASSWORD") or None,
            username=_env("REDIS_USERNAME") or None,
            db=int(_env("REDIS_DB", "0")),
        )

    def connect(self) -> Any:
        """`RedisVectorDB` yang tersambung ke server ini. Butuh extra redis."""
        from zul.utilities.vector_DB.redis_helper import RedisVectorDB

        return RedisVectorDB(
            host=self.host,
            port=self.port,
            password=self.password,
            username=self.username,
            db=self.db,
        )

    def safe_summary(self) -> dict[str, Any]:
        """Pengaturan untuk dicetak, dengan kata sandi yang disamarkan."""
        return {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "password": mask(self.password),
        }


@dataclass(frozen=True)
class MilvusSettings:
    """Koneksi Milvus dan nama database yang dipakai."""

    uri: str = "http://localhost"
    port: int = 19530
    db_name: str = "rag_eval"

    @classmethod
    def from_env(cls) -> MilvusSettings:
        return cls(
            uri=_env("MILVUS_URI", "http://localhost"),
            port=int(_env("MILVUS_PORT", "19530")),
            db_name=_env("MILVUS_DB", "rag_eval"),
        )

    @property
    def address(self) -> str:
        """Alamat lengkap untuk `MilvusClient`, misalnya `http://localhost:19530`."""
        return f"{self.uri}:{self.port}"
