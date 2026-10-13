"""
Prompt yang dirakit dari data saat runtime.

Gunanya:
    Tempat fungsi yang menyusun prompt dari data, misalnya menyisipkan
    dokumen hasil pencarian atau contoh few-shot. Prompt statis (teks
    tetap) tempatnya di `src/domain/templates/prompt/`.

Contoh:
    # application/prompts/rag.py
    def build_rag_prompt(question: str, documents: list[str]) -> str:
        context = "\n\n".join(documents)
        return f"Jawab berdasarkan konteks.\n\n{context}\n\nPertanyaan: {question}"
"""
