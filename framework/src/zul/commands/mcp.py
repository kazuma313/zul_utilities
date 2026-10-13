"""
Command untuk MCP server Zul: menjalankan, memeriksa, dan mencetak config client.

Gunanya:
    Code assistant seperti Claude Code, Cursor, atau VS Code tersambung ke
    Zul lewat MCP, lalu bisa membaca modul, dokumentasi, dan aturan gaya Zul.
    Perintah di sini menjalankan server itu dan mencetak config yang perlu
    ditempel di setiap client. `serve` dan `check` butuh extra mcp.

Cara pakai:
    zul mcp serve                          # dijalankan oleh code assistant
    zul mcp check                          # pastikan server berjalan
    zul mcp config claude-code             # config untuk sebuah client
    zul mcp config cursor --repo .         # pakai Zul dari checkout repo ini

Client yang dikenal: claude-code, cursor, vscode, claude-desktop.
"""

import json
from pathlib import Path

import typer

app = typer.Typer(no_args_is_help=True, help="MCP server Zul untuk code assistant")

CLIENTS = ("claude-code", "cursor", "vscode", "claude-desktop")
# Di checkout baru, --no-dev hanya meng-install Zul dan extra mcp.
REPO_RUN = ["run", "--no-dev", "--extra", "mcp", "zul", "mcp", "serve"]
INSTALL_HINT = (
    "MCP server butuh extra mcp:\n"
    '  pip install "zul[mcp] @ git+https://github.com/kazuma313/zul_utilities.git"'
)


def _server():
    try:
        from zul.assistant import server
    except ModuleNotFoundError as error:
        typer.echo(f"{INSTALL_HINT}\n({error})", err=True)
        raise typer.Exit(1) from error
    return server


# --------------------------------------------------------------------------
# Menjalankan Dan Memeriksa Server
# --------------------------------------------------------------------------
#
# Perintah serve tidak mencetak apa pun ke stdout, karena stdout dipakai
# oleh protokol MCP. Pesan untuk manusia hanya ditulis oleh check dan
# config, yang dijalankan di terminal, bukan oleh code assistant.
#


@app.command()
def serve():
    """Jalankan MCP server Zul lewat stdin/stdout (dipanggil oleh code assistant)."""
    _server().serve()


@app.command()
def check():
    """Uji MCP server Zul dengan client di proses yang sama, tanpa code assistant."""
    result = _server().check()
    typer.echo(
        f"MCP server zul siap: {len(result['tools'])} tool, "
        f"{len(result['resources'])} resource, {len(result['prompts'])} prompt."
    )
    typer.echo(f"Tool: {', '.join(result['tools'])}")
    typer.echo(f"Resource: {', '.join(result['resources'])}")
    typer.echo(f"Prompt: {', '.join(result['prompts'])}")
    first_line = result["sample"].strip().splitlines()[2:3]
    typer.echo(f"Contoh search_docs: {first_line[0] if first_line else '-'}")
    if result["sample_failed"]:
        raise typer.Exit(1)


# --------------------------------------------------------------------------
# Config Client
# --------------------------------------------------------------------------
#
# Setiap client menyimpan daftar MCP server di file JSON yang
# bentuknya berbeda-beda. Perintahnya tetap sama: zul mcp
# serve, atau lewat uv dari checkout repo jika --repo
# diisi, supaya kode yang dibaca tidak tertinggal.
#


def server_command(repo: Path | None) -> tuple[str, list[str]]:
    """Perintah dan argumen untuk menjalankan server: zul terpasang, atau uv di repo."""
    if repo is None:
        return "zul", ["mcp", "serve"]
    path = str(repo.expanduser().resolve())
    return "uv", ["--directory", path, *REPO_RUN]


def client_config(client: str, repo: Path | None = None) -> str:
    """Teks config untuk satu client, siap ditempel."""
    command, args = server_command(repo)
    entry = {"command": command, "args": args}
    if client == "claude-code":
        joined = " ".join([command, *args])
        project = json.dumps({"mcpServers": {"zul": entry}}, indent=2)
        return (
            "# Satu perintah, untuk semua proyek:\n"
            f"claude mcp add --scope user zul -- {joined}\n\n"
            f"# Atau simpan sebagai .mcp.json di root proyek:\n{project}"
        )
    if client == "vscode":
        return json.dumps({"servers": {"zul": {"type": "stdio", **entry}}}, indent=2)
    return json.dumps({"mcpServers": {"zul": entry}}, indent=2)


@app.command()
def config(
    client: str = typer.Argument(..., help=f"Salah satu: {', '.join(CLIENTS)}"),
    repo: Path = typer.Option(
        None, "--repo", help="Jalankan server lewat uv dari checkout repo Zul ini"
    ),
):
    """Cetak config MCP untuk sebuah code assistant."""
    if client not in CLIENTS:
        typer.echo(
            f"Client '{client}' tidak dikenal. Pilih: {', '.join(CLIENTS)}", err=True
        )
        raise typer.Exit(2)
    typer.echo(client_config(client, repo))
