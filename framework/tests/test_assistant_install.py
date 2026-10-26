"""Tes prompt pasang_zul dan halaman Memasang Zul lewat code assistant."""

import importlib
import re
import tomllib
from pathlib import Path

import pytest

from zul.assistant import knowledge, prompts

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "docs" / "panduan" / "memasang-zul-dengan-code-assistant.md"
INSTALL_GUIDE = ROOT / "docs" / "panduan" / "instalasi-zul.md"
CHECK_LINE = re.compile(r'^- (\w+) \(([^)]+)\): python -c "import ([\w., ]+)"$', re.M)
TABLE_ROW = re.compile(r"^\| `(\w+)` \|.*\| ([\d,]+ [MG]B) \|$", re.M)


def extras_in_pyproject() -> set[str]:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return set(project["project"]["optional-dependencies"]) - {"all"}


def checks() -> dict[str, tuple[str, list[str]]]:
    text = prompts.pasang_zul()
    return {
        name: (size, [part.strip() for part in modules.split(",")])
        for name, size, modules in CHECK_LINE.findall(text)
    }


def test_the_prompt_is_the_block_on_the_docs_page():
    text = PAGE.read_text(encoding="utf-8").replace("\r\n", "\n")
    start = text.index("## Prompt untuk ditempel")
    block = text[start:].split("```text\n", 1)[1].split("\n```", 1)[0]

    assert prompts.pasang_zul().strip() == block.strip()


def test_the_prompt_asks_before_it_installs():
    text = prompts.pasang_zul()

    assert (
        "Jangan menjalankan perintah yang mengubah sistem sebelum aku menjawab" in text
    )
    assert "Langkah 1. Tanyakan apa yang aku butuhkan." in text
    assert "menyetujui rencana" in text
    for choice in ("MCP", "OCR", "Evaluasi retrieval", "Semuanya", "Hanya dasar"):
        assert choice in text


def test_every_extra_has_a_size_and_an_import_check():
    assert set(checks()) == extras_in_pyproject()


def test_sizes_match_the_install_guide():
    guide = INSTALL_GUIDE.read_text(encoding="utf-8").replace("\r\n", "\n")
    table = dict(TABLE_ROW.findall(guide.split("## Memilih extra", 1)[1]))

    for name, (size, _) in checks().items():
        assert table[name] == size, name


@pytest.mark.parametrize("extra", sorted(extras_in_pyproject()))
def test_each_import_check_works_when_the_extra_is_installed(extra):
    for module in checks()[extra][1]:
        try:
            importlib.import_module(module)
        except ModuleNotFoundError as error:
            if (error.name or "").partition(".")[0] == "zul":
                raise
            pytest.skip(f"extra {extra} belum ter-install: {error.name}")


def test_each_check_imports_a_library_and_a_zul_module():
    for extra, (_, modules) in checks().items():
        zul_modules = [m for m in modules if m.partition(".")[0] == "zul"]
        libraries = [m for m in modules if m not in zul_modules]

        assert zul_modules, extra
        if extra != "evaluation":
            assert libraries, extra


def test_the_need_is_added_but_the_questions_stay():
    text = prompts.pasang_zul("saya butuh OCR dan evaluasi retrieval")

    assert "Kebutuhan awal dari pengguna: saya butuh OCR dan evaluasi retrieval" in text
    assert "Tetap tanyakan langkah 1" in text
    assert "Kebutuhan awal" not in prompts.pasang_zul()


def test_without_the_docs_the_prompt_still_asks_first(monkeypatch):
    monkeypatch.setattr(prompts, "_pages", lambda: {})

    text = prompts.pasang_zul()

    assert "tanyakan dulu apa yang ia butuhkan" in text
    assert prompts.INSTALL_URL in text
    assert "jangan memasang apa pun sebelum ia menjawab" in text


def test_the_page_is_part_of_the_docs_that_knowledge_serves():
    assert prompts.INSTALL_PAGE in knowledge._pages()
