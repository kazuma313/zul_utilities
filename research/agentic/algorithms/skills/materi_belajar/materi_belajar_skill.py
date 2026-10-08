"""Materi belajar skill: one module (or one topic) -> a lesson page with chapters, diagrams, a demo, quiz and exercises.

Two ways to fill it:
- a local model through Ollama writes the content as JSON (generate_materi), constrained by a schema,
- any model (or a person) writes the JSON itself and build_materi turns it into the page.
With a module card from a silabus_belajar JSON, the card is the contract: title, question, objectives
and terms are taken word for word.  Code draws the step diagrams and the demo, places the quiz answers,
checks that every objective is taught and tested, and writes the HTML.

    from skills.materi_belajar.materi_belajar_skill import generate_materi, build_materi
    result = generate_materi(silabus_json="silabus-python.json", module=1)    # local model
    result = generate_materi("Cara kerja bunga majemuk")                       # a lesson on its own
    result = build_materi(spec_dict, "python-modul-1.html", "silabus-python.json", 1)

`create_materi` is the same as a LangChain tool; it is None without langchain-core.
"""

import importlib
import os
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent / "scripts"
OUTPUT_DIR_ENV = "LEARNING_OUTPUT_DIR"      # where the tool saves pages; default ./belajar


def _load(required, optional=()):
    """Import this skill's scripts without leaving their names behind (the other skills share module names)."""
    own = {p.stem for p in _SCRIPTS.glob("*.py")}
    aside = {name: sys.modules.pop(name) for name in own if name in sys.modules}
    sys.path.insert(0, str(_SCRIPTS))
    loaded = {}
    try:
        for name in required:
            loaded[name] = importlib.import_module(name)
        for name in optional:
            try:
                loaded[name] = importlib.import_module(name)
            except ImportError:
                loaded[name] = None
    finally:
        for name in own:
            sys.modules.pop(name, None)
        sys.modules.update(aside)
        while str(_SCRIPTS) in sys.path:
            sys.path.remove(str(_SCRIPTS))
    return loaded


_mods = _load(["build_materi", "generate_materi", "local_model"])
_build, _gen, _llm = _mods["build_materi"], _mods["generate_materi"], _mods["local_model"]
RECOMMENDED = _gen.RECOMMENDED


def build_materi(spec, filename: str, silabus_json: str = None, module: int = None, sources=None, model: str = "") -> dict:
    """Spec (dict or JSON text) -> lesson page.  Returns {"ok", "path", "warnings", "chapters", "questions", ...}."""
    contract = _build.load_contract(silabus_json, module) if silabus_json else None
    return _build.build_materi(spec, filename, contract, sources, model)


def generate_materi(topic: str = "", silabus_json: str = None, module: int = None, output: str = None,
                    model: str = None, sources_file: str = None, context: str = "", base_url: str = None) -> dict:
    """A local model writes the lesson, code builds the page.  `model` None: the first of RECOMMENDED on the server."""
    contract = _build.load_contract(silabus_json, module) if silabus_json else None
    model = model or _llm.choose_model("ollama", base_url, RECOMMENDED)
    settings = _llm.Settings(model=model, base_url=base_url, max_tokens=_gen.MAX_TOKENS)
    return _gen.generate(topic, output, contract, _build.read_sources(sources_file), context, settings)


def materi_text(topic: str = "", silabus_json: str = "", module: int = 0) -> str:
    """The tool's reply: where the page is, what is in it, and what the checks found."""
    folder = Path(os.environ.get(OUTPUT_DIR_ENV) or "belajar")
    try:
        contract = _build.load_contract(silabus_json, module) if silabus_json else None
        name = (f"{_build.slugify(contract['topic'])}-modul-{module}.html" if contract
                else f"materi-{_build.slugify(topic)}.html")
        res = generate_materi(topic, silabus_json or None, module or None, str(folder / name))
    except Exception as error:  # noqa: BLE001 - the reason goes back to the caller as text
        return f"No lesson: {error}"
    if not res.get("ok"):
        return f"No lesson: {res.get('error')}. Do not write the lesson yourself; report the reason."
    lines = [f"Lesson page saved: {Path(res['path']).resolve()}",
             f"{res['chapters']} chapters, {res['diagrams']} diagrams, {'a demo' if res['demo'] else 'no demo'}, "
             f"{res['questions']} quiz questions, {res['exercises']} exercises."]
    lines += [f"Check: {w}" for w in res.get("warnings", [])]
    lines.append("Send the page to the user; for the next module, call again with module + 1.")
    return "\n".join(lines)


def _create_materi(topic: str = "", silabus_json: str = "", module: int = 0) -> str:
    """Write the lesson page of one module: objectives, chapters (what / how / why) with term boxes and diagrams,
    an interactive demo, summary, multiple-choice quiz, exercises and glossary.

    Use it whenever the user wants the material to study: "buatkan materi modul 2", "lanjut modul berikutnya",
    "bahan ajar", "pelajaran tentang X", "ajari saya X lengkap dengan kuis".

    Args:
        topic: Topic of a lesson without a syllabus. Leave empty when silabus_json is given.
        silabus_json: Path of the syllabus JSON written by create_silabus; its module card is the contract.
        module: Module number in that syllabus, starting at 1.
    """
    return materi_text(topic, silabus_json, module)


try:
    from langchain_core.tools import StructuredTool
except ImportError:  # pragma: no cover - the plain functions above work without LangChain
    create_materi = None
else:
    create_materi = StructuredTool.from_function(_create_materi, name="create_materi")


__all__ = ["build_materi", "generate_materi", "materi_text", "create_materi", "RECOMMENDED"]
