"""
Pembuat jawaban (generator) dari pertanyaan dan konteks hasil retrieval.

Gunanya:
    ragas butuh kolom `response` untuk metrik faithfulness dan
    answer_relevancy. `ChatGenerator` menyusun prompt dari konteks dan
    pertanyaan, lalu memanggil method `chat` milik model apa pun, misalnya
    `AIService`. Untuk menilai retrieval saja, generator tidak diperlukan:
    `run_rag` menerima `generator=None`. Hanya butuh library standar.

Cara pakai:
    from zul.evaluation.generation import ChatGenerator

    generator = ChatGenerator(ai)                 # ai punya method chat(prompt)
    answer = generator.answer("Apa itu mistika?", ["Mistika adalah ..."])
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

DEFAULT_PROMPT = """\
Jawab pertanyaan hanya berdasarkan konteks di bawah. Jika jawabannya tidak ada
di konteks, tulis "Tidak ditemukan di dokumen". Jawab ringkas dalam bahasa
Indonesia.

Konteks:
{contexts}

Pertanyaan: {question}
Jawaban:"""


@runtime_checkable
class Generator(Protocol):
    """Antarmuka generator: `name` untuk label hasil, dan method `answer`."""

    name: str

    def answer(self, question: str, contexts: list[str]) -> str: ...


def format_contexts(contexts: list[str]) -> str:
    """Konteks bernomor [1], [2], dan seterusnya, dipisah baris kosong."""
    return "\n\n".join(f"[{i}] {text.strip()}" for i, text in enumerate(contexts, 1))


@dataclass
class ChatGenerator:
    """
    Generator di atas model dengan method `chat(prompt)`.

    Args:
        model: Objek dengan method `chat`, yang mengembalikan teks atau objek
            berisi atribut `content`, misalnya `AIService`.
        prompt_template: Template dengan `{contexts}` dan `{question}`.
        max_context_chars: Batas panjang gabungan konteks, supaya tidak
            melampaui jendela konteks model; 0 berarti tanpa batas.
        name: Label hasil.
    """

    model: Any
    prompt_template: str = DEFAULT_PROMPT
    max_context_chars: int = 24_000
    name: str = "chat"

    def answer(self, question: str, contexts: list[str]) -> str:
        joined = format_contexts(contexts)
        if self.max_context_chars:
            joined = joined[: self.max_context_chars]
        prompt = self.prompt_template.format(contexts=joined, question=question)
        reply = self.model.chat(prompt)
        return str(getattr(reply, "content", reply)).strip()
