"""
MCP server Zul: kode, dokumentasi, dan aturan gaya Zul untuk code assistant.

Gunanya:
    Code assistant seperti Claude Code, Cursor, atau VS Code tersambung ke
    server ini lewat MCP, lalu bisa membaca daftar modul, cara pakai setiap
    fungsi, source code, contoh dari dokumentasi, dan aturan gaya Zul. Hasilnya,
    assistant memakai fungsi Zul yang sudah ada dan menulis kode baru dengan
    cara yang sama. Server dibangun lewat zul.adapters.mcp. Butuh extra mcp:
    `pip install "zul[mcp]"`.

Cara pakai:
    zul mcp serve          # dijalankan oleh code assistant, lewat stdin/stdout
    zul mcp check          # periksa server tanpa code assistant

    from zul.assistant.server import build_server
    server = build_server()

Isinya: 9 tool baca-saja (lihat TOOLS), 4 resource Markdown, dan 2 prompt.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from zul.adapters import mcp as mcp_adapter

from . import knowledge, prompts

INSTRUCTIONS = """\
Server ini menjelaskan paket Python Zul: wrapper berbagai library (OpenCV,
RF-DETR, LangChain, Docling, pymilvus, redisvl, dan lainnya) menjadi fungsi
kecil yang bisa dirangkai, dengan dokumentasi berbahasa Indonesia.

Untuk memakai Zul di proyek: search_docs, lalu find_examples, lalu
module_guide untuk setiap modul yang dipakai.
Untuk menulis kode di dalam Zul: conventions, list_modules, read_source
modul yang mirip, lalu check_code untuk setiap file baru."""

TOOLS = [
    knowledge.list_modules,
    knowledge.module_guide,
    knowledge.read_source,
    knowledge.list_docs,
    knowledge.read_doc,
    knowledge.search_docs,
    knowledge.find_examples,
    knowledge.conventions,
    knowledge.check_code,
]

# --------------------------------------------------------------------------
# Resource
# --------------------------------------------------------------------------
#
# Resource berisi teks yang sama dengan tool di atas, untuk client
# yang lebih suka melampirkan konteks lewat resource, misalnya
# menyebut @zul:zul://conventions di prompt Claude Code.
#


def _doc_resource(section: str, page: str) -> str:
    return knowledge.read_doc(f"{section}/{page}")


def _source_resource(module: str) -> str:
    return knowledge.read_source(module)


RESOURCES = [
    ("zul://conventions", knowledge.conventions, "conventions", "Aturan gaya Zul."),
    ("zul://modules", knowledge.list_modules, "modules", "Daftar semua modul Zul."),
    (
        "zul://docs/{section}/{page}",
        _doc_resource,
        "docs",
        "Satu halaman dokumentasi, misalnya zul://docs/panduan/mengukur-durasi.",
    ),
    (
        "zul://source/{module}",
        _source_resource,
        "source",
        "Source code satu modul, misalnya zul://source/zul.computer_vision.zones.",
    ),
]

PROMPTS = [prompts.tulis_modul_zul, prompts.pakai_zul]


def _version() -> str:
    try:
        return version("zul")
    except PackageNotFoundError:
        return ""


def build_server():
    """MCP server Zul dengan semua tool, resource, dan prompt sudah terdaftar."""
    server = mcp_adapter.create_server("zul", INSTRUCTIONS, _version())
    for tool in TOOLS:
        mcp_adapter.add_tool(server, tool)
    for uri, fn, name, description in RESOURCES:
        mcp_adapter.add_resource(server, uri, fn, name, description)
    for prompt in PROMPTS:
        mcp_adapter.add_prompt(server, prompt, prompt.__name__)
    return server


def serve() -> None:
    """Jalankan MCP server Zul lewat stdin dan stdout."""
    mcp_adapter.run_stdio(build_server())


def check() -> dict:
    """Uji server dengan client MCP di proses yang sama; kembalikan ringkasannya."""
    return mcp_adapter.self_check(
        build_server(), "search_docs", {"query": "garis penghitung", "limit": 1}
    )
