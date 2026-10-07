import importlib.util
import tomllib
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent

# scripts/ bukan package, jadi modulnya dimuat langsung dari path filenya.
spec = importlib.util.spec_from_file_location(
    "docs_hooks", ROOT / "scripts" / "docs_hooks.py"
)
docs_hooks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(docs_hooks)


def test_header_version_comes_from_pyproject():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    config = SimpleNamespace(config_file_path=str(ROOT / "mkdocs.yml"), extra={})

    docs_hooks.on_config(config)

    assert config.extra["zul_version"] == pyproject["project"]["version"]


def test_read_version_reads_the_project_table(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "contoh"\nversion = "1.2.3"\n')

    assert docs_hooks.read_version(pyproject) == "1.2.3"
