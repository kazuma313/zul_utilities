import json
import subprocess
import sys
import tomllib
from importlib.metadata import (
    PackageNotFoundError,
    distribution,
    packages_distributions,
)
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
PROJECT = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]

# --------------------------------------------------------------------------
# Modul Per Extra
# --------------------------------------------------------------------------
#
# Setiap modul di src/zul, selain template, tercatat di salah satu daftar
# ini. Modul inti jalan dengan `pip install zul` saja, dan modul lain
# cukup dengan dependency utama ditambah extra-nya. Tabel extra
# di docs/panduan/instalasi-zul.md mengikuti daftar yang sama.
#

CORE_MODULES = [
    "zul.cli",
    "zul.commands.build",
    "zul.commands.install",
    "zul.computer_vision.config",
    "zul.computer_vision.distance",
    "zul.computer_vision.geometry",
    "zul.computer_vision.pose",
    "zul.computer_vision.report",
    "zul.computer_vision.timers",
    "zul.computer_vision.zones",
    "zul.utilities.fake_embedding",
    "zul.utilities.logger",
    "zul.utilities.time",
    "zul.utilities.Prompts.ocr",
    "zul.utilities.script_helper.eval_performance",
    "zul.utilities.script_helper.json_helper",
    "zul.utilities.vector_DB.config.config_file",
    "zul.utilities.vector_DB.config.config_loader",
    "zul.utilities.vector_DB.config.config_loader_redis",
    "zul.utilities.vector_DB.config.config_schema",
    "zul.utilities.vector_DB.config.config_schema_redis",
]

EXTRA_MODULES = {
    "milvus": ["zul.utilities.vector_DB.milvus_helper"],
    "redis": [
        "zul.utilities.vector_DB.redis_helper",
        "zul.utilities.redis_vector_helper",
    ],
    "converter": [
        "zul.utilities.markdown_converter.md_to_pdf",
        "zul.utilities.markdown_converter.md_to_ppt",
        "zul.utilities.md_to_pdf",
        "zul.utilities.md_to_ppt",
    ],
    "analysis": [
        "zul.utilities.analysis",
        "zul.utilities.script_helper.save_file",
    ],
    "pdf": ["zul.utilities.script_helper.read_pdf2"],
    "ocr": [
        "zul.utilities.OCR.docling_OCR",
        "zul.utilities.docling_OCR",
    ],
    "llm": [
        "zul.utilities.embedding_service",
        "zul.utilities.script_helper.ai_models",
        "zul.utilities.react_graph",
    ],
    "gemini": ["zul.utilities.OCR.gemini_ocr"],
    "vision": [
        "zul.computer_vision.draw",
        "zul.computer_vision.masks",
        "zul.computer_vision.video",
    ],
    "yolo": [
        "zul.computer_vision.detection",
        "zul.computer_vision.weights",
    ],
}

# --------------------------------------------------------------------------
# Distribusi Yang Diizinkan
# --------------------------------------------------------------------------
#
# Distribusi yang ter-install dihitung dari metadata paket di environment
# ini, termasuk dependency dari dependency. Hasilnya sama dengan yang
# di-install pip untuk zul atau zul[EXTRA] di platform yang sama.
#


def zul_requirements(extra: str = "") -> list[Requirement]:
    raw = PROJECT["optional-dependencies"][extra] if extra else PROJECT["dependencies"]
    return [Requirement(line) for line in raw]


def installed_closure(requirements: list[Requirement]) -> set[str]:
    found: set[str] = set()
    pending = list(requirements)

    while pending:
        requirement = pending.pop()
        name = canonicalize_name(requirement.name)

        if name == "zul":
            for extra in requirement.extras:
                pending.extend(zul_requirements(extra))
            continue
        if name in found:
            continue
        found.add(name)

        try:
            requires = distribution(name).requires or []
        except PackageNotFoundError:
            continue

        for line in requires:
            sub = Requirement(line)
            extras = [""] + sorted(requirement.extras)
            if sub.marker is None or any(
                sub.marker.evaluate({"extra": e}) for e in extras
            ):
                pending.append(sub)

    return found


def allowed_distributions(extra: str = "") -> set[str]:
    allowed = installed_closure(zul_requirements())
    if extra:
        allowed |= installed_closure(zul_requirements(extra))
    return allowed | {"zul"}


def blocked_modules(allowed: set[str]) -> list[str]:
    blocked = []
    for module, dists in packages_distributions().items():
        if not {canonicalize_name(dist) for dist in dists} & allowed:
            blocked.append(module)
    return sorted(blocked)


# --------------------------------------------------------------------------
# Mengimpor Dengan Library Terbatas
# --------------------------------------------------------------------------
#
# Environment development berisi semua extra, jadi test ini memakai Python
# baru yang menolak import library di luar daftar. Penolakannya berupa
# ModuleNotFoundError, seperti yang dilihat pengguna tanpa extra itu.
#

IMPORT_SCRIPT = """
import importlib
import json
import sys

job = json.load(sys.stdin)
blocked = set(job["blocked"])


class Blocker:
    def find_spec(self, name, path=None, target=None):
        if name.partition(".")[0] in blocked:
            raise ModuleNotFoundError(f"No module named {name!r}", name=name)
        return None


sys.meta_path.insert(0, Blocker())
for module in job["modules"]:
    importlib.import_module(module)
"""


def import_with_only(modules: list[str], allowed: set[str]) -> None:
    job = {"blocked": blocked_modules(allowed), "modules": modules}
    result = subprocess.run(
        [sys.executable, "-c", IMPORT_SCRIPT],
        input=json.dumps(job),
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr[-3000:]


# --------------------------------------------------------------------------
# Test
# --------------------------------------------------------------------------


def test_core_modules_import_without_any_extra():
    import_with_only(CORE_MODULES, allowed_distributions())


@pytest.mark.parametrize("extra", sorted(EXTRA_MODULES))
def test_each_extra_is_enough_for_its_modules(extra):
    import_with_only(EXTRA_MODULES[extra], allowed_distributions(extra))


def test_every_extra_has_modules_and_is_part_of_all():
    extras = set(PROJECT["optional-dependencies"]) - {"all"}
    (all_requirement,) = zul_requirements("all")

    assert extras == set(EXTRA_MODULES)
    assert set(all_requirement.extras) == extras


def test_every_module_is_assigned_to_core_or_an_extra():
    source = ROOT / "src"
    found = {
        ".".join(path.relative_to(source).with_suffix("").parts)
        for path in (source / "zul").rglob("*.py")
        if "templates" not in path.parts and path.name != "__init__.py"
    }
    listed = set(CORE_MODULES) | {
        m for modules in EXTRA_MODULES.values() for m in modules
    }

    assert found == listed
