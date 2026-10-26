import asyncio
import json
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from zul.assistant import knowledge, prompts
from zul.cli import app
from zul.commands.mcp import client_config, server_command

runner = CliRunner()

# --------------------------------------------------------------------------
# Modul Dan Source Code
# --------------------------------------------------------------------------


def test_list_modules_groups_modules_and_names_their_extra():
    text = knowledge.list_modules()

    assert "## computer_vision" in text
    assert "## adapters" in text
    assert "| `zul.computer_vision.zones` |" in text
    assert "| `zul.adapters.opencv` |" in text
    assert "templates" not in text


def test_module_guide_shows_signatures_and_properties():
    text = knowledge.module_guide("computer_vision.timers")

    assert text.startswith("# zul.computer_vision.timers")
    assert "Gunanya:" in text
    assert "`duration_s` (property)" in text
    assert "duration_s()" not in text


def test_unknown_module_suggests_close_names():
    text = knowledge.module_guide("computer_vision.zone")

    assert "tidak ada di Zul" in text
    assert "zul.computer_vision.zones" in text


def test_evaluation_modules_and_guide_are_reachable():
    modules = knowledge.list_modules()
    hits = knowledge.search_docs("evaluasi retrieval", limit=3)

    assert "## evaluation" in modules
    assert "| `zul.evaluation.judge` |" in modules
    assert "### `evaluate_rag(" in knowledge.module_guide("evaluation.judge")
    assert "panduan/mengevaluasi-retrieval" in hits
    assert "zul.evaluation.retrievers" in prompts.tulis_modul_zul("retriever baru")


def test_projects_list_and_read_the_computer_vision_boilerplate():
    projects = knowledge.list_projects()
    overview = knowledge.read_project("computer_vision")
    pipeline = knowledge.read_project("computer_vision", "src/cctv/pipeline.py")

    assert "`computer_vision`" in projects
    assert overview.startswith("# Boilerplate computer vision CCTV")
    assert "- `src/cctv/analytics.py`" in overview
    assert "__pycache__" not in overview
    assert pipeline.startswith("# computer_vision/src/cctv/pipeline.py\n\n```python\n")
    assert "def run(" in pipeline


def test_read_project_stays_inside_the_boilerplate():
    assert "tidak ada" in knowledge.read_project(
        "computer_vision", "../../src/zul/cli.py"
    )
    assert "tidak ada" in knowledge.read_project("computer_vision", "README-hilang.md")
    assert "Yang tersedia: computer_vision" in knowledge.read_project("hexa")


def test_read_project_skips_secrets_and_outputs(tmp_path, monkeypatch):
    app = tmp_path / "app"
    for name in ("README.md", ".env", ".gitignore", "outputs/hasil.csv", "src/main.py"):
        (app / name).parent.mkdir(parents=True, exist_ok=True)
        (app / name).write_text("# App\n\nIsi.\n", encoding="utf-8")
    monkeypatch.setattr(knowledge, "project_root", lambda: tmp_path)

    overview = knowledge.read_project("app")

    assert "- `src/main.py`" in overview and "- `.gitignore`" in overview
    assert ".env`" not in overview and "outputs/" not in overview
    assert "tidak ada" in knowledge.read_project("app", ".env")
    assert "tidak ada" in knowledge.read_project("app", "outputs/hasil.csv")
    assert knowledge.read_project("app", ".gitignore").startswith("# app/.gitignore")


def test_every_boilerplate_is_listed_file_by_file_in_the_wheel():
    import tomllib

    root = Path(__file__).resolve().parents[2]
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    included = pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]
    for folder in (root / "framework" / "project").iterdir():
        if not (folder / "README.md").is_file():
            continue
        base = f"framework/project/{folder.name}"
        assert base not in included, "folder utuh ikut membawa video dan .env lokal"
        for part in ("README.md", "pyproject.toml", "src", "tests"):
            if (folder / part).exists():
                assert f"{base}/{part}" in included


def test_read_source_returns_the_whole_file():
    text = knowledge.read_source("zul.computer_vision.zones")

    assert "File: `zul/computer_vision/zones.py`" in text
    assert "```python\n" in text
    assert "def " in text


# --------------------------------------------------------------------------
# Dokumentasi
# --------------------------------------------------------------------------


def test_docs_are_found_from_the_repository():
    assert knowledge.docs_root() is not None
    assert "`panduan/berkontribusi`" in knowledge.list_docs()


def test_read_doc_returns_a_page_or_suggests_one():
    page = knowledge.read_doc("panduan/menghitung-dengan-garis-dan-poligon.md")
    missing = knowledge.read_doc("panduan/menghitung-garis")

    assert page.startswith("# ")
    assert "tidak ada" in missing
    assert "panduan/menghitung-dengan-garis-dan-poligon" in missing


def test_search_docs_ranks_pages_and_module_docstrings():
    text = knowledge.search_docs("garis penghitung", limit=3)

    assert text.startswith("# Hasil pencarian: garis penghitung")
    assert text.count("\n## ") == 3
    assert " > " in text


def test_search_docs_without_keywords_or_hits():
    assert "kata kunci" in knowledge.search_docs("  ")
    assert "Tidak ada yang cocok" in knowledge.search_docs("qwxzvbn")


def test_find_examples_returns_dedented_python():
    text = knowledge.find_examples("garis penghitung", limit=2)

    assert "```python\n" in text
    blocks = text.split("```python\n")[1:]
    assert blocks
    assert all(not block.startswith(" ") for block in blocks)


# --------------------------------------------------------------------------
# Aturan Gaya Dan Pemeriksaan Kode
# --------------------------------------------------------------------------


def test_conventions_come_from_the_adapter_docstring_and_contributing_page():
    text = knowledge.conventions()

    assert "## Fungsi kecil, bukan use case" in text
    assert "`numpy`" in text
    assert "## Mengikuti gaya kode" in text
    assert "## Yang boleh dan tidak boleh" in text
    assert "## Berkontribusi dengan bantuan AI" in text
    assert "AGPL" in text


def test_conventions_keep_code_blocks_that_contain_comment_lines():
    text = knowledge.conventions()
    start = text.index("## Menulis komentar dan docstring")
    rules = text[start : text.index("### Mengikuti gaya penulisan")]

    assert "# Batas Langkah" in rules
    assert "anak tangga" in rules
    assert rules.count("```") % 2 == 0


GOOD_MODULE = '''"""
Contoh modul.

Gunanya:
    Menjumlahkan dua angka.

Cara pakai:
    total(1, 2)
"""

import numpy as np


def total(a: float, b: float) -> float:
    return float(np.add(a, b))
'''

BAD_MODULE = """import cv2
import some_new_library

# Komentar pendek,
# lalu baris kedua yang jauh lebih panjang dari baris pertama,
# dan baris ketiga yang juga sangat panjang sampai hampir penuh.
x = 1
"""


def test_check_code_accepts_code_that_follows_the_rules():
    assert knowledge.check_code(GOOD_MODULE).startswith("Tidak ada masalah")


def test_check_code_lists_every_problem():
    text = knowledge.check_code(BAD_MODULE)

    assert "Komentar belum anak tangga" in text
    assert "`Gunanya:`" in text
    assert "`cv2` diimpor langsung" in text
    assert "zul.adapters.opencv" in text
    assert "`some_new_library` diimpor langsung" in text
    assert "Buat adapter baru" in text


def test_check_code_outside_zul_skips_zul_only_rules():
    text = knowledge.check_code(BAD_MODULE, inside_zul=False)

    assert "Komentar belum anak tangga" in text
    assert "diimpor langsung" not in text


def test_check_code_reports_syntax_errors():
    assert knowledge.check_code("def broken(:\n").startswith("Sintaks salah di baris 1")


def test_prompts_name_the_tools_to_call():
    assert "`conventions`" in prompts.tulis_modul_zul("timer baru")
    assert "`check_code`" in prompts.tulis_modul_zul("timer baru")
    assert "`search_docs`" in prompts.pakai_zul("hitung orang")
    template = prompts.evaluasi_retrieval("bandingkan rrf dan hybrid")
    assert "bandingkan rrf dan hybrid" in template
    assert "`evaluate_rag`" in template
    assert "panduan/mengevaluasi-retrieval" in template


# --------------------------------------------------------------------------
# Config Client
# --------------------------------------------------------------------------


def test_server_command_uses_zul_or_uv_in_a_repo(tmp_path):
    assert server_command(None) == ("zul", ["mcp", "serve"])
    command, args = server_command(tmp_path)
    assert command == "uv"
    assert args[:2] == ["--directory", str(tmp_path.resolve())]
    assert args[2:] == ["run", "--no-dev", "--extra", "mcp", "zul", "mcp", "serve"]


@pytest.mark.parametrize("client", ["cursor", "claude-desktop"])
def test_json_clients_use_mcp_servers(client):
    config = json.loads(client_config(client))

    assert config == {
        "mcpServers": {"zul": {"command": "zul", "args": ["mcp", "serve"]}}
    }


def test_vscode_uses_servers_with_a_type():
    config = json.loads(client_config("vscode"))

    assert config["servers"]["zul"]["type"] == "stdio"


def test_claude_code_gets_a_command_and_a_project_file():
    text = client_config("claude-code")

    assert "claude mcp add --scope user zul -- zul mcp serve" in text
    assert '"mcpServers"' in text


def test_cli_config_rejects_unknown_clients():
    good = runner.invoke(app, ["mcp", "config", "cursor"])
    bad = runner.invoke(app, ["mcp", "config", "notepad"])

    assert good.exit_code == 0
    assert json.loads(good.output)["mcpServers"]["zul"]["command"] == "zul"
    assert bad.exit_code == 2


# --------------------------------------------------------------------------
# MCP Server
# --------------------------------------------------------------------------
#
# Test di bawah butuh extra mcp. Client di proses yang sama memeriksa
# isi server, dan satu test menjalankan zul mcp serve sebagai proses
# terpisah, persis seperti saat dijalankan oleh code assistant.
#

EXPECTED_TOOLS = {
    "list_modules",
    "module_guide",
    "read_source",
    "list_docs",
    "read_doc",
    "search_docs",
    "find_examples",
    "list_projects",
    "read_project",
    "conventions",
    "check_code",
    "layout_rules",
    "check_layout",
}


def test_server_registers_every_tool_resource_and_prompt():
    pytest.importorskip("mcp")
    from zul.assistant import server

    result = server.check()

    assert set(result["tools"]) == EXPECTED_TOOLS
    assert set(result["resources"]) == {
        "zul://conventions",
        "zul://modules",
        "zul://layout",
        "zul://docs/{section}/{page}",
        "zul://source/{module}",
    }
    assert set(result["prompts"]) == {
        "tulis_modul_zul",
        "pakai_zul",
        "evaluasi_retrieval",
        "rapikan_arsitektur",
        "pasang_zul",
    }
    assert not result["sample_failed"]
    assert "Hasil pencarian" in result["sample"]


def test_resources_and_prompts_return_text():
    pytest.importorskip("mcp")
    from mcp.client import Client

    from zul.assistant.server import build_server

    async def read():
        async with Client(build_server()) as client:
            doc = await client.read_resource("zul://docs/panduan/berkontribusi")
            source = await client.read_resource(
                "zul://source/zul.computer_vision.zones"
            )
            prompt = await client.get_prompt("pakai_zul", {"tugas": "hitung orang"})
            tools = await client.list_tools()
        return doc, source, prompt, tools

    doc, source, prompt, tools = asyncio.run(read())

    assert doc.contents[0].text.startswith("# ")
    assert "zul/computer_vision/zones.py" in source.contents[0].text
    assert "hitung orang" in prompt.messages[0].content.text
    assert all(tool.annotations.read_only_hint for tool in tools.tools)


def test_cli_check_prints_a_summary():
    pytest.importorskip("mcp")

    result = runner.invoke(app, ["mcp", "check"])

    assert result.exit_code == 0, result.output
    assert "MCP server zul siap: 13 tool, 5 resource, 5 prompt." in result.output


def test_serve_speaks_mcp_over_stdio():
    pytest.importorskip("mcp")
    from mcp.client import Client
    from mcp.client.stdio import StdioServerParameters

    parameters = StdioServerParameters(
        command=sys.executable, args=["-m", "zul.assistant"]
    )

    async def call():
        async with Client(parameters) as client:
            result = await client.call_tool(
                "module_guide", {"module": "computer_vision.zones"}
            )
        return "".join(part.text for part in result.content)

    text = asyncio.run(call())

    assert text.startswith("# zul.computer_vision.zones")
