"""--model auto in the generators: the recommended model of each use case that the server has.

    python -m pytest research/agentic/algorithms/skills/evals -q -p no:cacheprovider
"""

import argparse
import importlib.util
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

POOL = Path(__file__).resolve().parent.parent
GENERATORS = {
    "slides": "pptx_claude/scripts/generate_deck.py",
    "proposal": "pptx_research/scripts/generate_deck.py",
    "poster": "resaerch_poster/scripts/generate_poster.py",
    "mind_map": "mind_map/scripts/generate_mindmap.py",
}


def load(name: str):
    path = POOL / GENERATORS[name]
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location(f"choice_{name}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(path.parent))
        for shared in ("spec_normalizer", "build_poster", "build_deck", "create_pptx", "charts", "icons", "font_metrics",
                       "build_mindmap", "extract_text", "outline_from_text", "outline_parser", "outline_repair"):
            sys.modules.pop(shared, None)


@pytest.fixture
def server():
    """A model server that lists the models in `server.models`, the Ollama way and the OpenAI way."""
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            listing = ({"models": [{"name": n} for n in Handler.models]} if self.path == "/api/tags"
                       else {"data": [{"id": n} for n in Handler.models]})
            body = json.dumps(listing).encode()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    httpd = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    httpd.models, httpd.url = [], f"http://127.0.0.1:{httpd.server_port}"
    Handler.models = httpd.models
    yield httpd
    httpd.shutdown()


def options(url: str, api: str = "ollama"):
    return argparse.Namespace(api=api, base_url=url, api_key="local")


@pytest.mark.parametrize("name, best", [("slides", "qwen3:8b"), ("proposal", "qwen3:8b"), ("poster", "qwen3:8b"),
                                        ("mind_map", "gemma3:4b")])
def test_each_use_case_takes_its_recommended_model(server, monkeypatch, name, best):
    monkeypatch.delenv("SKILL_MODEL", raising=False)
    server.models[:] = ["nomic-embed-text:latest", "qwen3:4b", "gemma3:4b", "qwen3:8b"]
    assert load(name).choose_model(options(server.url)) == best


def test_a_missing_model_falls_back_to_the_next_recommended_one(server, monkeypatch):
    monkeypatch.delenv("SKILL_MODEL", raising=False)
    deck, maps = load("slides"), load("mind_map")
    server.models[:] = ["nomic-embed-text:latest", "gemma3:4b"]
    assert deck.choose_model(options(server.url)) == "gemma3:4b"
    server.models[:] = ["qwen3:8b-q4_K_M"]
    assert maps.choose_model(options(server.url)) == "qwen3:8b-q4_K_M"
    server.models[:] = ["nomic-embed-text:latest", "llama3.1:8b"]          # none recommended: any chat model
    assert deck.choose_model(options(server.url)) == "llama3.1:8b"


def test_lm_studio_names_and_the_environment(server, monkeypatch):
    monkeypatch.delenv("SKILL_MODEL", raising=False)
    deck = load("slides")
    server.models[:] = ["google/gemma-3-4b", "qwen/qwen3-8b"]
    assert deck.choose_model(options(server.url, api="openai")) == "qwen/qwen3-8b"
    monkeypatch.setenv("SKILL_MODEL", "my-model")
    assert deck.choose_model(options(server.url)) == "my-model"


def test_without_a_server_the_first_recommended_name_is_used(monkeypatch):
    monkeypatch.delenv("SKILL_MODEL", raising=False)
    assert load("poster").choose_model(options("http://127.0.0.1:9")) == "qwen3:8b"
    assert not load("mind_map")._same_model("qwen3:80b", "qwen3:8b")
