"""
Helper murni yang dipakai lintas layer.

Gunanya:
    Fungsi kecil tanpa logika bisnis dan tanpa dependensi ke layer lain:
    format tanggal, pemotong teks, pembuat id.

Contoh:
    # utils/text.py
    def truncate(text: str, max_chars: int = 200) -> str:
        return text if len(text) <= max_chars else text[: max_chars - 1] + "…"
"""
