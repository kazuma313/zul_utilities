import logging
import os
import subprocess
import sys

import numpy as np
import pytest

from zul.utilities.fake_embedding import FakeEmbeddingModel
from zul.utilities.logger import get_logger
from zul.utilities.script_helper.eval_performance import TimerDecorator, timer_func

# --------------------------------------------------------------------------
# FakeEmbeddingModel
# --------------------------------------------------------------------------


def test_fake_embedding_shape_follows_dimension_and_number_of_texts():
    model = FakeEmbeddingModel(dimension=16, seed=42)

    assert model.encode("hallo").shape == (1, 16)
    assert model.encode(["a", "b", "c"]).shape == (3, 16)


def test_fake_embedding_is_unit_length_by_default():
    vector = FakeEmbeddingModel(dimension=32).encode("hallo")[0]

    assert np.linalg.norm(vector) == pytest.approx(1.0)


def test_fake_embedding_same_text_gives_same_vector():
    model = FakeEmbeddingModel(dimension=16, seed=42)

    assert np.array_equal(model.encode("hallo"), model.encode("hallo"))


def test_fake_embedding_differs_by_text_and_by_seed():
    model = FakeEmbeddingModel(dimension=16, seed=42)
    other_seed = FakeEmbeddingModel(dimension=16, seed=7)

    assert not np.array_equal(model.encode("hallo"), model.encode("hai"))
    assert not np.array_equal(model.encode("hallo"), other_seed.encode("hallo"))


def test_fake_embedding_is_stable_across_python_processes():
    script = (
        "from zul.utilities.fake_embedding import FakeEmbeddingModel;"
        "print(FakeEmbeddingModel(dimension=4, seed=1).encode('hallo')[0].tolist())"
    )

    def run_with_hash_seed(hash_seed: str) -> str:
        env = {**os.environ, "PYTHONHASHSEED": hash_seed}
        return subprocess.check_output(
            [sys.executable, "-c", script], env=env, text=True
        )

    assert run_with_hash_seed("1") == run_with_hash_seed("2")


def test_fake_embedding_does_not_touch_global_numpy_random_state():
    np.random.seed(123)
    expected = np.random.random()

    np.random.seed(123)
    FakeEmbeddingModel(dimension=8, seed=1).encode("hallo")

    assert np.random.random() == expected


# --------------------------------------------------------------------------
# Timer decorators
# --------------------------------------------------------------------------


def test_timer_decorator_records_every_call():
    @TimerDecorator
    def add(a, b):
        return a + b

    assert add(1, 2) == 3
    assert add(3, 4) == 7

    assert add.call_count == 2
    assert len(add.get_all_times()) == 2
    assert add.get_last_time() == add.get_all_times()[-1]
    assert add.get_average_time() == pytest.approx(sum(add.get_all_times()) / 2)


def test_timer_decorator_reset_clears_history():
    @TimerDecorator
    def noop():
        pass

    noop()
    noop.reset_times()

    assert noop.get_last_time() is None
    assert noop.get_average_time() == 0


@pytest.mark.parametrize("decorator", [TimerDecorator, timer_func])
def test_timer_decorators_keep_function_name(decorator):
    @decorator
    def search_documents():
        """Cari dokumen."""

    assert search_documents.__name__ == "search_documents"
    assert search_documents.__doc__ == "Cari dokumen."


def test_old_timer_import_path_still_works():
    from zul.utilities.time import TimerDecorator as OldPathTimerDecorator

    assert OldPathTimerDecorator is TimerDecorator


# --------------------------------------------------------------------------
# Logger
# --------------------------------------------------------------------------


@pytest.fixture
def close_log_handlers():
    """Tutup file handler supaya tmp_path bisa dihapus di Windows."""
    names = []
    yield names
    for name in names:
        logger = logging.getLogger(name)
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)


def test_get_logger_creates_missing_log_directory(tmp_path, close_log_handlers):
    close_log_handlers.append("test_zul_creates_dir")
    log_file = tmp_path / "nested" / "logs" / "app.log"

    logger = get_logger("test_zul_creates_dir", log_file=str(log_file))
    logger.info("halo")

    assert "halo" in log_file.read_text(encoding="utf-8")


def test_get_logger_called_twice_does_not_duplicate_handlers(
    tmp_path, close_log_handlers
):
    close_log_handlers.append("test_zul_no_duplicates")
    log_file = str(tmp_path / "app.log")

    first = get_logger("test_zul_no_duplicates", log_file=log_file)
    second = get_logger("test_zul_no_duplicates", log_file=log_file)

    assert first is second
    assert len(second.handlers) == 2


# --------------------------------------------------------------------------
# AIService config
# --------------------------------------------------------------------------


def test_ai_config_from_env_enables_embedding_when_its_key_is_set(monkeypatch):
    from zul.utilities.embedding_service import AIConfig

    monkeypatch.setenv("LLM_API_KEY", "llm-key")
    monkeypatch.setenv("EMBEDDING_API_KEY", "embedding-key")
    monkeypatch.setenv("EMBEDDING_MODEL", "text-embedding-3-small")

    config = AIConfig.from_env()

    assert config.embedding.model == "text-embedding-3-small"


def test_ai_config_from_env_is_chat_only_without_embedding_key(monkeypatch):
    from zul.utilities.embedding_service import AIConfig

    monkeypatch.setenv("LLM_API_KEY", "llm-key")
    monkeypatch.delenv("EMBEDDING_API_KEY", raising=False)

    assert AIConfig.from_env().embedding is None


def test_ai_config_requires_an_llm_api_key(monkeypatch):
    from zul.utilities.embedding_service import AIConfig

    monkeypatch.delenv("LLM_API_KEY", raising=False)

    with pytest.raises(ValueError, match="LLM_API_KEY"):
        AIConfig.from_env()


@pytest.fixture
def no_ai_env(monkeypatch):
    """Hapus environment variable AI supaya hanya isi file config yang dibaca."""
    for name in list(os.environ):
        if name.startswith(("LLM_", "EMBEDDING_", "SERVICE_")):
            monkeypatch.delenv(name)


def test_ai_config_from_file_reads_yaml(tmp_path, no_ai_env):
    from zul.utilities.embedding_service import AIConfig

    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "llm:\n  api_key: file-key\n  model: qwen-kecil\n"
        "embedding:\n  api_key: embed-key\n  model: embed-kecil\n",
        encoding="utf-8",
    )

    config = AIConfig.from_file(config_file)

    assert config.llm.api_key.get_secret_value() == "file-key"
    assert config.llm.model == "qwen-kecil"
    assert config.embedding.model == "embed-kecil"


def test_ai_config_from_empty_yaml_uses_defaults_and_env(
    tmp_path, no_ai_env, monkeypatch
):
    from zul.utilities.embedding_service import AIConfig

    monkeypatch.setenv("LLM_API_KEY", "llm-key")
    config_file = tmp_path / "config.yml"
    config_file.write_text("", encoding="utf-8")

    config = AIConfig.from_file(config_file)

    assert config.llm.model == "qwen2-32B-Instruct-resolved"
    assert config.embedding is None


def test_ai_config_from_file_rejects_invalid_yaml(tmp_path, no_ai_env):
    from zul.adapters.yaml import YamlError
    from zul.utilities.embedding_service import AIConfig

    config_file = tmp_path / "config.yaml"
    config_file.write_text("llm:\n  api_key: [belum ditutup\n", encoding="utf-8")

    with pytest.raises(YamlError, match="YAML tidak valid") as error:
        AIConfig.from_file(config_file)

    assert isinstance(error.value, ValueError)
