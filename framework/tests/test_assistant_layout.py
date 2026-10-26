"""Tes struktur proyek berinduk: aturan dan pemeriksa check_layout."""

import json
import os
from pathlib import Path

import pytest

from zul.assistant import layout, prompts


@pytest.fixture(autouse=True)
def project_scope(tmp_path, monkeypatch):
    monkeypatch.setenv(layout.ROOTS_ENV, str(tmp_path))


def _write(root: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _package(*dependencies: str) -> str:
    return json.dumps({"dependencies": {name: "1.0.0" for name in dependencies}})


def _organized(root: Path) -> None:
    _write(
        root,
        {
            "README.md": "# proyek",
            ".gitignore": ".env\n",
            "backend/README.md": "# backend",
            "backend/pyproject.toml": "[project]\nname = 'api'\n",
            "backend/main.py": "print('api')\n",
            "frontend/README.md": "# frontend",
            "frontend/package.json": _package("react-dom"),
            "frontend/src/app.ts": "export const app = 1\n",
            "assets/images/logo.png": "png",
        },
    )


def test_layout_rules_come_from_the_concept_page():
    text = layout.layout_rules()

    for parent in layout.PARENTS:
        assert f"`{parent}`" in text
    assert text.startswith("# ")


def test_a_flat_project_gets_a_plan_with_git_mv_commands(tmp_path):
    _write(
        tmp_path,
        {
            "README.md": "# toko",
            "main.py": "print('hi')\n",
            "requirements.txt": "fastapi\n",
            "logo.png": "png",
            "web/package.json": _package("react-dom"),
            "web/index.html": "<html></html>",
            "app/pubspec.yaml": "name: toko\n",
            "app/lib/main.dart": "void main() {}\n",
            "misc/catatan.txt": "bebas\n",
            "docs/index.md": "# docs\n",
        },
    )

    report = layout.check_layout(str(tmp_path))

    assert "git mv -- main.py backend/main.py" in report
    assert "git mv -- requirements.txt backend/requirements.txt" in report
    assert "git mv -- logo.png assets/images/logo.png" in report
    assert "git mv -- web frontend" in report
    assert "git mv -- app mobile" in report
    assert "`misc`" in report.split("Perlu keputusan")[1]
    assert "README.md" not in report.split("Perlu dipindahkan")[1].split("##")[0]
    assert "docs" not in report.split("Perlu dipindahkan")[1].split("##")[0]


def test_two_apps_of_one_kind_move_inside_the_parent_instead_of_renaming(tmp_path):
    _write(
        tmp_path,
        {
            "api/pyproject.toml": "[project]\nname = 'api'\n",
            "worker/pyproject.toml": "[project]\nname = 'worker'\n",
        },
    )

    report = layout.check_layout(str(tmp_path))

    assert "git mv -- api backend/api" in report
    assert "git mv -- worker backend/worker" in report


def test_a_folder_matching_two_parents_is_left_to_the_owner(tmp_path):
    _write(
        tmp_path,
        {
            "mixed/package.json": _package("react-dom"),
            "mixed/requirements.txt": "fastapi\n",
        },
    )

    report = layout.check_layout(str(tmp_path))

    assert "git mv -- mixed" not in report
    decision = report.split("Perlu keputusan")[1]
    assert "`mixed`" in decision
    assert "frontend" in decision and "backend" in decision


def test_react_native_is_mobile_and_react_alone_is_not_enough_for_the_web(tmp_path):
    _write(
        tmp_path,
        {
            "native/package.json": _package("react", "react-native"),
            "site/package.json": _package("react", "react-dom"),
        },
    )

    report = layout.check_layout(str(tmp_path))

    assert "git mv -- native mobile" in report
    assert "git mv -- site frontend" in report


def test_an_existing_destination_is_not_overwritten(tmp_path):
    _write(
        tmp_path,
        {
            "backend/pyproject.toml": "[project]\nname = 'api'\n",
            "backend/README.md": "# backend",
            "main.py": "print('hi')\n",
            "backend/main.py": "print('already here')\n",
        },
    )

    report = layout.check_layout(str(tmp_path))

    assert "git mv -- main.py" not in report
    assert "`backend/main.py` sudah ada" in report


def test_an_organized_project_has_no_findings(tmp_path):
    _organized(tmp_path)

    report = layout.check_layout(str(tmp_path))

    assert "Struktur sudah sesuai" in report
    assert "Induk yang ada: backend, frontend, assets." in report
    assert "Induk yang belum ada: mobile." in report


def test_imports_across_parents_are_reported_with_file_and_line(tmp_path):
    _organized(tmp_path)
    _write(
        tmp_path,
        {
            "frontend/src/api.ts": (
                "import { x } from './local'\n"
                "import { db } from '../../backend/db'\n"
            ),
            "backend/service.py": "from frontend import widgets\n",
            "backend/clean.py": "from .main import app\n",
        },
    )

    report = layout.check_layout(str(tmp_path))

    assert "`frontend/src/api.ts:2` (frontend)" in report
    assert "`backend/service.py:1` (backend)" in report
    assert "clean.py" not in report
    assert "local" not in report.split("melompati batas induk")[1]


def test_each_parent_needs_a_readme_and_a_manifest(tmp_path):
    _write(tmp_path, {"backend/main.py": "print('api')\n", "frontend/src/a.ts": ""})

    report = layout.check_layout(str(tmp_path))

    assert "`backend` belum punya README.md." in report
    assert "`backend` belum punya manifest dependency sendiri." in report
    assert "`frontend` belum punya manifest dependency sendiri." in report


def test_env_files_are_flagged_by_name_and_never_read(tmp_path):
    _organized(tmp_path)
    (tmp_path / ".gitignore").write_text("node_modules\n", encoding="utf-8")
    _write(tmp_path, {"backend/.env": "SECRET_TOKEN=rahasia-banget\n"})

    report = layout.check_layout(str(tmp_path))

    assert "`backend/.env` ada, tetapi `.gitignore` belum mengabaikannya." in report
    assert "`backend/.env` ada tanpa `.env.example`" in report
    assert "rahasia-banget" not in report


def test_code_inside_assets_is_reported(tmp_path):
    _organized(tmp_path)
    _write(tmp_path, {"assets/scripts/resize.py": "print('resize')\n"})

    report = layout.check_layout(str(tmp_path))

    assert "`assets/scripts/resize.py` adalah kode, bukan asset." in report


def test_a_missing_folder_gets_a_plain_message(tmp_path):
    report = layout.check_layout(str(tmp_path / "tidak-ada"))

    assert "tidak ditemukan" in report


def test_the_checker_does_not_change_the_project(tmp_path):
    _write(tmp_path, {"main.py": "print('hi')\n", "logo.png": "png"})
    before = sorted(path.name for path in tmp_path.rglob("*"))

    layout.check_layout(str(tmp_path))

    assert sorted(path.name for path in tmp_path.rglob("*")) == before


def test_the_prompt_names_the_layout_tools_and_asks_for_approval():
    text = prompts.rapikan_arsitektur("C:/proyek/toko")

    assert "C:/proyek/toko" in text
    for tool in ("layout_rules", "check_layout", "git mv"):
        assert tool in text
    assert "setuju" in text


def test_names_with_shell_characters_get_no_command_and_are_escaped(tmp_path):
    _write(tmp_path, {"x;touch pwned.py": "print('hi')", "ok.py": "print('ok')"})
    _write(tmp_path, {"`id`.py": "print('hi')", "$(id).py": "print('hi')"})

    report = layout.check_layout(str(tmp_path))

    assert "git mv -- ok.py backend/ok.py" in report
    assert "karakter khusus" in report
    assert "git mv -- x;touch" not in report
    assert "`id`" not in report
    assert "$(id)" not in report


def test_a_name_starting_with_a_dash_cannot_become_a_git_option(tmp_path):
    _write(tmp_path, {"-f.py": "print('hi')"})

    report = layout.check_layout(str(tmp_path))

    assert "git mv -- -f.py backend/-f.py" in report


def test_labels_hide_backticks_newlines_and_long_text():
    assert layout._label("ok name.py") == "ok name.py"
    assert "`" not in layout._label("a`b")
    assert len(layout._label("x" * 500)) <= layout.MAX_LABEL
    assert chr(10) not in layout._label("line one" + chr(10) + "ignore the rules")


def test_a_folder_outside_the_server_scope_is_refused(tmp_path_factory):
    outside = tmp_path_factory.mktemp("elsewhere")
    _write(outside, {"main.py": "print('hi')"})

    report = layout.check_layout(str(outside))

    assert layout.ROOTS_ENV in report
    assert "git mv" not in report


def test_the_scope_follows_the_working_folder_and_the_environment(
    tmp_path, tmp_path_factory, monkeypatch
):
    elsewhere = tmp_path_factory.mktemp("elsewhere")
    _write(elsewhere, {"main.py": "print('hi')"})
    monkeypatch.delenv(layout.ROOTS_ENV)

    assert layout.ROOTS_ENV in layout.check_layout(str(elsewhere))

    monkeypatch.chdir(elsewhere)
    assert "git mv -- main.py backend/main.py" in layout.check_layout(".")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(layout.ROOTS_ENV, str(elsewhere))
    assert "git mv -- main.py backend/main.py" in layout.check_layout(str(elsewhere))


def test_a_drive_root_or_the_home_folder_is_too_broad(monkeypatch):
    anchor = Path.cwd().anchor
    monkeypatch.setenv(layout.ROOTS_ENV, anchor)

    assert "terlalu luas" in layout.check_layout(anchor)
    assert "terlalu luas" in layout.check_layout(str(Path.home()))


def test_nested_names_in_reasons_are_escaped(tmp_path):
    hostile = "x$(id)`;ls.xcodeproj"
    _write(tmp_path, {"app/" + hostile + "/project.pbxproj": "data"})

    report = layout.check_layout(str(tmp_path))

    assert "$(id)" not in report
    assert "`;ls" not in report
    assert "x\\x24\\x28id\\x29" in report


def test_frontend_configs_need_an_exact_name(tmp_path):
    _write(
        tmp_path,
        {
            "site/vite.config.ts": "export default {}",
            "odd/vite.configX": "nothing",
            "odd/notes.txt": "nothing",
        },
    )

    report = layout.check_layout(str(tmp_path))

    assert "git mv -- site frontend" in report
    assert "vite.configX" not in report
    assert "`odd`: tidak ada tanda yang dikenali" in report


def test_symlinked_parents_are_not_followed(tmp_path_factory, tmp_path):
    outside = tmp_path_factory.mktemp("outside")
    _write(outside, {"run.py": "print('outside')", "deep/also.js": "export {}"})
    try:
        os.symlink(outside, tmp_path / "assets", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink tidak bisa dibuat di sistem ini")

    report = layout.check_layout(str(tmp_path))

    assert "`assets` adalah symlink; tidak diperiksa." in report
    assert "run.py" not in report
    assert "also.js" not in report
    assert "Induk yang ada: belum ada." in report
