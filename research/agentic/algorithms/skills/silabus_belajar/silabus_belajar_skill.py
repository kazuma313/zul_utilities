"""Silabus belajar skill: "I want to learn X" -> a syllabus page (learning path) with a module map, cards and a schedule.

Two ways to fill it:
- a local model through Ollama writes the content as JSON (generate_silabus), constrained by a schema,
- any model (or a person) writes the JSON itself and build_silabus turns it into the page.
Either way, code computes hours and the weekly schedule, draws the module map, checks the skill's rules
(checkable objectives, module order, a risk module for money topics) and writes the HTML.

    from skills.silabus_belajar.silabus_belajar_skill import generate_silabus, build_silabus
    result = generate_silabus("Python untuk analisis data", hours_per_week=4)      # local model
    result = build_silabus(spec_dict, "silabus-python.html")                          # JSON written elsewhere
    result["path"], result["json"], result["warnings"]

The normalised JSON next to the page holds the module cards that materi_belajar uses as contracts.
`create_silabus` is the same as a LangChain tool; it is None without langchain-core.
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


_mods = _load(["build_silabus", "generate_silabus", "local_model"])
_build, _gen, _llm = _mods["build_silabus"], _mods["generate_silabus"], _mods["local_model"]
RECOMMENDED = _gen.RECOMMENDED


def build_silabus(spec, filename: str, sources=None, hours_per_week: int = 4, model: str = "") -> dict:
    """Spec (dict or JSON text) -> page.  Returns {"ok", "path", "json", "warnings", "modules", "hours", "weeks"}."""
    return _build.build_silabus(spec, filename, sources, hours_per_week, model)


def generate_silabus(topic: str = "", output: str = None, level: str = "Pemula", goal: str = "",
                     hours_per_week: int = 4, model: str = None, sources_file: str = None, context: str = "",
                     base_url: str = None, files: list = None) -> dict:
    """A local model writes the content, code builds the page.  `model` None: the first of RECOMMENDED on the server.

    `files`: the learner's material (PDF, images, docx, pptx, xlsx, html, text, folders or links); without a
    topic the model takes it from the material.
    """
    model = model or _llm.choose_model("ollama", base_url, RECOMMENDED)
    settings = _llm.Settings(model=model, base_url=base_url)
    return _gen.generate(topic, output, level, goal, hours_per_week, _build.read_sources(sources_file), context, settings,
                         files=files)


def silabus_text(topic: str = "", level: str = "Pemula", goal: str = "", hours_per_week: int = 4,
                 files: list = None) -> str:
    """The tool's reply: where the page is, what is in it, and what the checks found."""
    folder = Path(os.environ.get(OUTPUT_DIR_ENV) or "belajar")
    output = folder / f"silabus-{_build.slugify(topic or (Path(str(files[0])).stem if files else ''))}.html"
    try:
        res = generate_silabus(topic, str(output), level, goal, hours_per_week, files=files)
    except Exception as error:  # noqa: BLE001 - the reason goes back to the caller as text
        return f"No syllabus for {topic!r}: {error}"
    if not res.get("ok"):
        return f"No syllabus for {topic!r}: {res.get('error')}. Do not write a syllabus yourself; report the reason."
    lines = [f"Syllabus page saved: {Path(res['path']).resolve()}",
             f"{res['modules']} modules, {res['stages']} stages, about {res['hours']} hours over {res['weeks']} weeks.",
             f"Module cards for materi_belajar: {Path(res['json']).resolve()}"]
    lines += [f"Check: {w}" for w in res.get("warnings", [])]
    lines.append("Send the page to the user and offer to write module 1 with materi_belajar.")
    return "\n".join(lines)


def _create_silabus(topic: str = "", level: str = "Pemula", goal: str = "", hours_per_week: int = 4,
                    files: list[str] | None = None) -> str:
    """Create a syllabus (learning path) page for a topic or for the user's own material: final skills, a module
    map, module cards with a main question and objectives, a weekly schedule and a final project.

    Use it whenever the user wants to learn something step by step: "buatkan silabus", "roadmap belajar",
    "rencana belajar", "saya mau belajar X dari nol", "kurikulum", "learning path", or "jadikan PDF/dokumen
    ini rencana belajar".

    Args:
        topic: What the user wants to learn, for example "Python untuk analisis data". May be empty when files
            are given; the topic is then taken from the material.
        level: The learner's starting level, for example "Pemula".
        goal: What the learner wants to be able to do at the end, in the user's words.
        hours_per_week: Hours per week the learner has; 4 when the user did not say.
        files: Paths or links of the user's material: PDF, images, docx, pptx, xlsx, html or text files.
    """
    return silabus_text(topic, level, goal, hours_per_week, files)


try:
    from langchain_core.tools import StructuredTool
except ImportError:  # pragma: no cover - the plain functions above work without LangChain
    create_silabus = None
else:
    create_silabus = StructuredTool.from_function(_create_silabus, name="create_silabus")


__all__ = ["build_silabus", "generate_silabus", "silabus_text", "create_silabus", "RECOMMENDED"]
