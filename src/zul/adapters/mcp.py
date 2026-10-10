"""
Adapter MCP: server, tool, resource, dan prompt, lalu menjalankannya.

Gunanya:
    Satu-satunya file Zul yang mengimpor SDK MCP resmi (paket `mcp`, MIT).
    Fungsi Python biasa didaftarkan apa adanya: nama fungsi menjadi nama
    tool, docstring menjadi deskripsi, dan type hint menjadi skema argumen.
    Butuh extra mcp: `pip install "zul[mcp]"`.

Cara pakai:
    from zul.adapters import mcp as mcp_adapter

    def sapa(nama: str) -> str:
        \"\"\"Menyapa seseorang.\"\"\"
        return f"halo {nama}"

    server = mcp_adapter.create_server("contoh", instructions="Server contoh.")
    mcp_adapter.add_tool(server, sapa)
    mcp_adapter.run_stdio(server)       # menunggu client lewat stdin/stdout

Di SDK MCP versi 2, kelas FastMCP berganti nama menjadi MCPServer. Versi
SDK dikunci ke `>=2.3,<3` di pyproject.toml.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from mcp.client import Client
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

# --------------------------------------------------------------------------
# Server
# --------------------------------------------------------------------------


def create_server(name: str, instructions: str, version: str = "") -> Any:
    """MCP server kosong. Objek yang dikembalikan hanya untuk fungsi di file ini."""
    return MCPServer(name, instructions=instructions, version=version)


def add_tool(server: Any, fn: Callable[..., Any], read_only: bool = True) -> None:
    """Daftarkan fungsi sebagai tool; nama, deskripsi, dan argumennya dari fungsinya."""
    annotations = ToolAnnotations(readOnlyHint=read_only)
    server.add_tool(
        fn, name=fn.__name__, description=_summary(fn), annotations=annotations
    )


def add_resource(
    server: Any, uri: str, fn: Callable[..., str], name: str, description: str
) -> None:
    """Daftarkan resource Markdown. URI boleh bertemplate, misalnya zul://docs/{page}."""
    register = server.resource(
        uri, name=name, description=description, mime_type="text/markdown"
    )
    register(fn)


def add_prompt(server: Any, fn: Callable[..., str], name: str) -> None:
    """Daftarkan fungsi yang mengembalikan teks sebagai prompt."""
    server.prompt(name=name, description=_summary(fn))(fn)


def run_stdio(server: Any) -> None:
    """Jalankan server lewat stdin dan stdout sampai client menutup koneksi."""
    server.run("stdio")


def _summary(fn: Callable[..., Any]) -> str:
    return (fn.__doc__ or "").strip()


# --------------------------------------------------------------------------
# Pemeriksaan Mandiri
# --------------------------------------------------------------------------
#
# Server diuji dengan client MCP asli yang tersambung di proses yang sama,
# tanpa stdin/stdout. Pemeriksaan ini membuktikan semua tool, resource,
# dan prompt terdaftar benar sebelum disambungkan ke code assistant.
#


def self_check(server: Any, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Nama tool, resource, dan prompt server, ditambah hasil satu panggilan tool."""
    return asyncio.run(_self_check(server, tool, arguments))


async def _self_check(server: Any, tool: str, arguments: dict[str, Any]) -> dict:
    async with Client(server) as client:
        tools = await client.list_tools()
        resources = await client.list_resources()
        templates = await client.list_resource_templates()
        prompts = await client.list_prompts()
        result = await client.call_tool(tool, arguments)
    return {
        "tools": [item.name for item in tools.tools],
        "resources": [str(item.uri) for item in resources.resources]
        + [item.uri_template for item in templates.resource_templates],
        "prompts": [item.name for item in prompts.prompts],
        "sample": "".join(getattr(part, "text", "") for part in result.content),
        "sample_failed": bool(result.is_error),
    }
