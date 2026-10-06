import json
import os
import subprocess
import sys
from importlib.metadata import version

import pytest
import yaml
from typer.testing import CliRunner

from zul.cli import app
from zul.utilities.vector_DB.config.config_loader import (
    ConfigLoader as MilvusConfigLoader,
)
from zul.utilities.vector_DB.config.config_loader_redis import (
    ConfigLoader as RedisConfigLoader,
)

runner = CliRunner()

HEXA_TOP_LEVEL = {"src", "data", "dockerfile", "logs", "notebooks", "test"}


@pytest.fixture
def project_root(tmp_path, monkeypatch):
    """Jalankan command di folder kosong, seperti user di folder kerjanya."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


# --------------------------------------------------------------------------
# version
# --------------------------------------------------------------------------


@pytest.mark.parametrize("args", [["version"], ["--version"]])
def test_version_matches_installed_package(args):
    result = runner.invoke(app, args)

    assert result.exit_code == 0
    assert version("zul") in result.output


# --------------------------------------------------------------------------
# build hexa
# --------------------------------------------------------------------------


def test_build_hexa_copies_src_and_its_sibling_folders(project_root):
    result = runner.invoke(app, ["build", "hexa", "--name", "my-app", "--yes"])

    assert result.exit_code == 0, result.output
    created = {
        path.name for path in (project_root / "my-app").iterdir() if path.is_dir()
    }
    assert created >= HEXA_TOP_LEVEL


def test_build_hexa_ships_files_needed_to_run_the_project(project_root):
    runner.invoke(app, ["build", "hexa", "--name", "my-app", "--yes"])

    project = project_root / "my-app"
    for file_name in ["README.md", "requirements.txt", ".env.example", ".gitignore"]:
        assert (project / file_name).is_file(), file_name
    assert (project / "src" / "interface" / "http" / "main.py").read_text(
        encoding="utf-8"
    )


def test_build_hexa_writes_project_name_into_readme(project_root):
    runner.invoke(app, ["build", "hexa", "--name", "my-app", "--yes"])

    readme = (project_root / "my-app" / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# my-app")
    assert "{{" not in readme


def test_build_hexa_does_not_copy_python_cache(project_root):
    runner.invoke(app, ["build", "hexa", "--name", "my-app", "--yes"])

    assert not list((project_root / "my-app").rglob("__pycache__"))


def test_build_hexa_refuses_existing_directory(project_root):
    (project_root / "my-app").mkdir()
    (project_root / "my-app" / "keep.txt").write_text("data penting", encoding="utf-8")

    result = runner.invoke(app, ["build", "hexa", "--name", "my-app", "--yes"])

    assert result.exit_code == 1
    assert "sudah ada" in result.output
    assert (project_root / "my-app" / "keep.txt").read_text(
        encoding="utf-8"
    ) == "data penting"


# --------------------------------------------------------------------------
# install
# --------------------------------------------------------------------------


@pytest.mark.parametrize("command", ["milvus-helper", "milvus_helper"])
def test_install_milvus_helper_writes_config_the_helper_can_load(project_root, command):
    result = runner.invoke(app, ["install", command])

    assert result.exit_code == 0, result.output
    config = MilvusConfigLoader.load(project_root / "milvus_config.json")
    assert config.connection.port == 19530
    assert config.collections[0].collection_name == "my_collection"


def test_install_milvus_helper_supports_yaml(project_root):
    result = runner.invoke(
        app, ["install", "milvus-helper", "--config-name", "milvus.yaml"]
    )

    assert result.exit_code == 0, result.output
    assert yaml.safe_load((project_root / "milvus.yaml").read_text(encoding="utf-8"))
    assert MilvusConfigLoader.load(project_root / "milvus.yaml").collections


def test_install_rejects_unsupported_config_format(project_root):
    result = runner.invoke(
        app, ["install", "milvus-helper", "--config-name", "milvus.toml"]
    )

    assert result.exit_code != 0
    assert not (project_root / "milvus.toml").exists()


def test_install_keeps_existing_config_when_user_declines(project_root):
    existing = project_root / "milvus_config.json"
    existing.write_text(json.dumps({"mine": True}), encoding="utf-8")

    result = runner.invoke(app, ["install", "milvus-helper"], input="n\n")

    assert result.exit_code == 0
    assert json.loads(existing.read_text(encoding="utf-8")) == {"mine": True}


def test_install_force_overwrites_existing_config(project_root):
    existing = project_root / "milvus_config.json"
    existing.write_text(json.dumps({"mine": True}), encoding="utf-8")

    result = runner.invoke(app, ["install", "milvus-helper", "--force"])

    assert result.exit_code == 0, result.output
    assert "connection" in json.loads(existing.read_text(encoding="utf-8"))


def test_install_redis_helper_writes_config_the_helper_can_load(project_root):
    result = runner.invoke(app, ["install", "redis-helper"])

    assert result.exit_code == 0, result.output
    config = RedisConfigLoader.load(project_root / "redis_config.yaml")
    assert config.connection.host == "localhost"
    assert config.hybrid_search.vector_field_name == "content_embedding_vector"


@pytest.mark.parametrize(
    "args",
    [
        ["--help"],
        ["install", "milvus-helper"],
        ["build", "hexa", "--name", "my-app", "--yes"],
    ],
)
def test_commands_survive_output_that_cannot_encode_emoji(project_root, args):
    environment = {**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}

    result = subprocess.run(
        [sys.executable, "-m", "zul.cli", *args],
        cwd=project_root,
        env=environment,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr.decode("cp1252", "replace")


def test_generated_project_ships_passing_example_tests(project_root):
    runner.invoke(app, ["build", "hexa", "--name", "my-app", "--yes"])

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
        cwd=project_root / "my-app",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "4 passed" in result.stdout
