import logging
import sys

import pytest

from zul.commands.build import copy_template


@pytest.fixture(scope="session")
def generated_hexa_project(tmp_path_factory):
    """Proyek hexa yang dibuat sekali, lalu dipakai bersama semua test."""
    project_dir = tmp_path_factory.mktemp("hexa") / "my-app"
    copy_template("hexa", project_dir)

    return project_dir


@pytest.fixture
def hexa_project(generated_hexa_project, monkeypatch):
    """Proyek hexa yang root-nya importable sebagai `src.*`."""
    project_dir = generated_hexa_project
    monkeypatch.chdir(project_dir)
    monkeypatch.syspath_prepend(str(project_dir))
    root_logger = logging.getLogger()
    handlers_before = list(root_logger.handlers)

    yield project_dir

    for module_name in [
        name for name in sys.modules if name == "src" or name.startswith("src.")
    ]:
        del sys.modules[module_name]
    # setup_logging() milik proyek memasang file handler pada root
    # logger; lepaskan lagi di sini agar file log-nya tertutup.
    for handler in [h for h in root_logger.handlers if h not in handlers_before]:
        handler.close()
        root_logger.removeHandler(handler)


@pytest.fixture
def http_app(hexa_project):
    """Aplikasi FastAPI proyek hexa; dependency override dibersihkan setelah test."""
    pytest.importorskip("fastapi")
    from src.interface.http.main import app

    yield app
    app.dependency_overrides.clear()
