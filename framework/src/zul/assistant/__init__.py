"""
Zul untuk code assistant: pengetahuan tentang Zul, disajikan lewat MCP.

Gunanya:
    Code assistant membaca modul, cara pakai, contoh, dan aturan gaya Zul,
    lalu meniru cara Zul ditulis. Isinya:

    knowledge       daftar modul, cara pakai, source, dokumentasi, aturan,
                    dan pemeriksa kode                       tanpa extra
    prompts         prompt urutan kerja untuk assistant       tanpa extra
    comment_style   pemeriksa paragraf komentar anak tangga   tanpa extra
    server          MCP server yang menyajikan semua di atas  zul[mcp]

Cara pakai:
    zul mcp serve                    # untuk code assistant
    zul mcp config claude-code       # cetak config untuk sebuah client

    python -m zul.assistant          # sama dengan zul mcp serve
"""
