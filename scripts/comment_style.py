"""
Pemeriksa gaya komentar: pembungkus perintah untuk zul.assistant.comment_style.

Gunanya:
    Logikanya tinggal di paket Zul, supaya MCP server Zul juga bisa
    memeriksa gaya komentar. File ini menjaga perintah lamanya tetap sama.

Cara pakai:
    python scripts/comment_style.py src tests           # periksa saja
    python scripts/comment_style.py src tests --fix     # lipat ulang barisnya
"""

from zul.assistant.comment_style import main

if __name__ == "__main__":
    raise SystemExit(main())
