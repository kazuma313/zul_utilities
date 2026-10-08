"""Ask a local model (Ollama, or an OpenAI-compatible server such as LM Studio) for one JSON answer.

Shared by silabus_belajar and materi_belajar (each skill keeps its own copy, the pool loads skills
in isolation).  Standard library only.

    model = choose_model("ollama", None, ("qwen3:8b", "gemma3:4b"))
    raw, stats = ask_model(settings, system, user, schema)
    spec = parse_json(raw)

The schema goes to the server as `format` (Ollama) or `response_format` (OpenAI style), so even a 4B
model can only write JSON of the right shape.  With a schema, reasoning is switched off first: qwen3:4b
otherwise spends its whole token budget reasoning and returns nothing (see the pool's REQUIREMENTS.md).
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class Settings:
    model: str
    api: str = "ollama"                  # "ollama" or "openai"
    base_url: str | None = None
    api_key: str = "local"
    temperature: float = 0.3
    num_ctx: int = 0                     # 0: just enough for the request plus max_tokens (context_size)
    max_tokens: int = 4096
    think: str = "auto"                  # auto / on / off (Ollama only)
    timeout: int = 1800

    @property
    def base(self) -> str:
        default = "http://localhost:11434" if self.api == "ollama" else "http://localhost:1234/v1"
        return (self.base_url or default).rstrip("/")


def _same_model(installed: str, wanted: str) -> bool:
    """qwen3:8b is qwen3:8b, qwen3:8b-q4_K_M, library/qwen3:8b and LM Studio's qwen/qwen3-8b."""
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())  # noqa: E731
    return norm(installed.split("/")[-1]).startswith(norm(wanted))


def choose_model(api: str, base_url: str | None, recommended: tuple, api_key: str = "local") -> str:
    """The first of `recommended` that the server has; SKILL_MODEL in the environment wins.

    Without the recommended models the first installed chat model is used, and without a server the
    first recommended name is returned, so the request that follows reports what is missing.
    """
    if os.environ.get("SKILL_MODEL"):
        return os.environ["SKILL_MODEL"]
    base = Settings(model="", api=api, base_url=base_url).base
    req = urllib.request.Request(base + ("/api/tags" if api == "ollama" else "/models"),
                                 headers={"Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            listing = json.loads(resp.read().decode("utf-8"))
    except (OSError, ValueError):
        return recommended[0]
    names = [m.get("name") or m.get("id") or "" for m in listing.get("models") or listing.get("data") or []]
    names = [n for n in names if n and "embed" not in n.lower()]
    return next((n for want in recommended for n in names if _same_model(n, want)), names[0] if names else recommended[0])


def context_size(s: Settings, system: str, user: str) -> int:
    """num_ctx for one request: the prompt, counted generously at 2.5 characters a token, plus the answer.

    The context's cache takes GPU memory from the model's layers.  On a 6 GB GPU, qwen3:8b kept 22 of its
    37 layers on the GPU at num_ctx 12288 (about 7 tokens a second) and 25-26 at the 6144-7168 that a
    request of these skills needs (about 10 tokens a second).
    """
    if s.num_ctx:
        return s.num_ctx
    need = int((len(system) + len(user)) / 2.5) + s.max_tokens + 256
    return -(-need // 1024) * 1024


def _post(url: str, payload: dict, api_key: str, timeout: int) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ask_model(s: Settings, system: str, user: str, schema: dict | None) -> tuple[str, dict]:
    """(answer text, stats) for one request; stats has seconds, and tokens/eval_seconds when the server says."""
    started = time.perf_counter()
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    if s.api == "ollama":
        payload = {"model": s.model, "stream": False, "messages": messages,
                   "options": {"temperature": s.temperature, "num_ctx": context_size(s, system, user),
                               "num_predict": s.max_tokens}}
        if schema:
            payload["format"] = schema
        # With a schema the server lets the model write JSON only, so reasoning adds nothing but tokens.
        # Some Ollama versions drop the schema when think=false is sent; an answer that is not JSON is
        # asked for again with the model's own default.
        fast = s.think == "auto" and bool(schema)
        if s.think != "auto" or fast:
            payload["think"] = s.think == "on"
        url = s.base + "/api/chat"
        try:
            data = _post(url, payload, s.api_key, s.timeout)
        except urllib.error.HTTPError as error:
            if error.code != 400:
                raise
            payload.pop("think", None)            # older Ollama, or a model without a reasoning switch
            data = _post(url, payload, s.api_key, s.timeout)
        content = data.get("message", {}).get("content", "")
        if fast and "think" in payload and not content.lstrip().startswith(("{", "[")):
            payload.pop("think")
            data = _post(url, payload, s.api_key, s.timeout)
            content = data.get("message", {}).get("content", "")
        stats = {"seconds": round(time.perf_counter() - started, 1), "tokens": data.get("eval_count"),
                 "eval_seconds": round((data.get("eval_duration") or 0) / 1e9, 1) or None,
                 "prompt_tokens": data.get("prompt_eval_count"), "num_ctx": payload["options"]["num_ctx"]}
        return content, stats

    payload = {"model": s.model, "temperature": s.temperature, "max_tokens": s.max_tokens, "messages": messages}
    if schema:
        payload["response_format"] = {"type": "json_schema",
                                      "json_schema": {"name": "spec", "strict": False, "schema": schema}}
    url = s.base + "/chat/completions"
    try:
        data = _post(url, payload, s.api_key, s.timeout)
    except urllib.error.HTTPError as error:
        if error.code not in (400, 422) or not schema:
            raise
        payload["response_format"] = {"type": "json_object"}   # server without json_schema support
        data = _post(url, payload, s.api_key, s.timeout)
    usage = data.get("usage") or {}
    return (data["choices"][0]["message"].get("content") or "",
            {"seconds": round(time.perf_counter() - started, 1), "tokens": usage.get("completion_tokens"),
             "eval_seconds": None, "prompt_tokens": usage.get("prompt_tokens")})


def parse_json(raw: str):
    """The JSON object in a model's answer: code fences and text around the object are ignored."""
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        return json.loads(text)
    except ValueError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("answer has no JSON object")
    return json.loads(text[start:end + 1])


def server_error_hint(error: Exception, model: str) -> str:
    """A sentence that says what to do when the model server cannot be used."""
    if isinstance(error, urllib.error.HTTPError):
        body = error.read().decode("utf-8", errors="replace")[:300]
        return (f"the model server answered HTTP {error.code}: {body}. "
                f"Check that {model!r} is downloaded (ollama pull {model}) and --api / --base-url.")
    return (f"cannot reach the model server ({error}). Is it running? ollama: `ollama serve`; "
            "LM Studio: start the local server; check --base-url.")


def cut_fields(value, schema: dict, path: str = "") -> list:
    """Paths of strings that stopped exactly at their schema's maxLength: the server cut them there."""
    if isinstance(value, str):
        limit = schema.get("maxLength")
        return [path] if limit and len(value) >= limit else []
    if isinstance(value, dict):
        props = schema.get("properties", {})
        return [p for k, v in value.items() if k in props for p in cut_fields(v, props[k], f"{path}.{k}".lstrip("."))]
    if isinstance(value, list):
        return [p for i, v in enumerate(value, 1) for p in cut_fields(v, schema.get("items", {}), f"{path}[{i}]")]
    return []
