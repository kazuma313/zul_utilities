"""
Menjalankan MCP server Zul dengan `python -m zul.assistant`.

Gunanya:
    Cara lain menjalankan `zul mcp serve`, untuk client yang lebih mudah
    diberi path Python daripada nama perintah. Butuh extra mcp.

Cara pakai:
    python -m zul.assistant
"""

from zul.assistant.server import serve

if __name__ == "__main__":
    serve()
