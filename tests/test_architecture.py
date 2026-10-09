import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src" / "zul"
ADAPTERS_DIR = SOURCE / "adapters"
VENDOR_DIR = ADAPTERS_DIR / "_vendor"

# --------------------------------------------------------------------------
# Library Yang Dipakai Langsung
# --------------------------------------------------------------------------
#
# Library pihak ketiga hanya diimpor di zul/adapters. Library di daftar ini
# ialah pengecualian: dipakai langsung di modul lain karena ia bagian dari
# bahasa Zul sendiri, bukan alat yang bisa diganti di balik satu adapter.
#

EMBEDDED = {
    "numpy": "Tipe data array untuk kotak, titik, dan frame di semua modul.",
    "pydantic": "Kelas config dan respons Zul sendiri adalah model pydantic.",
    "typer": "Perintah `zul` dibangun dengan Typer; CLI adalah aplikasinya.",
    "InquirerPy": "Pertanyaan interaktif `zul build`, bagian dari CLI.",
}

# --------------------------------------------------------------------------
# Adapter Dan Library-nya
# --------------------------------------------------------------------------
#
# Setiap adapter hanya boleh mengimpor library yang ia tangani, NumPy,
# dan adapter lain. Menambah adapter berarti menambah satu baris di
# sini, supaya jelas library mana yang ditangani oleh file mana.
#

ADAPTERS = {
    "docling": {"docling"},
    "gemini": {"google"},
    "langchain_openai": {"langchain_openai"},
    "langchain_text_splitters": {"langchain_core", "langchain_text_splitters"},
    "langgraph": {"langgraph"},
    "markdown": {"markdown"},
    "matplotlib": {"matplotlib"},
    "milvus": {"pymilvus"},
    "opencv": {"cv2"},
    "pandas": {"pandas"},
    "pptx": {"pptx"},
    "pypdf": {"PyPDF2", "pypdf"},
    "redis": {"redis", "redisvl"},
    "scipy": {"scipy"},
    "ultralytics": {"ultralytics"},
    "xhtml2pdf": {"xhtml2pdf"},
    "yaml": {"yaml"},
}

# Modul yang belum dipindahkan ke adapter. Daftar ini harus kosong.
PENDING: dict[str, set[str]] = {}

# --------------------------------------------------------------------------
# Membaca Import
# --------------------------------------------------------------------------


def zul_modules() -> list[Path]:
    """Semua modul Zul, kecuali template proyek dan salinan library di _vendor."""
    return sorted(
        path
        for path in SOURCE.rglob("*.py")
        if "templates" not in path.parts and "_vendor" not in path.parts
    )


def module_name(path: Path) -> str:
    return ".".join(path.relative_to(SOURCE.parent).with_suffix("").parts)


def imported_roots(path: Path) -> set[str]:
    """Nama paket teratas yang diimpor file ini, termasuk import di dalam fungsi."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.partition(".")[0])
    return roots


def third_party(roots: set[str]) -> set[str]:
    return {
        root
        for root in roots
        if root not in sys.stdlib_module_names and root not in {"zul", "__future__"}
    }


def zul_imports(path: Path) -> set[str]:
    """Modul zul yang diimpor file ini, ditulis lengkap, termasuk import relatif."""
    package = module_name(path).rpartition(".")[0]
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level:
                base = package.split(".")[: len(package.split(".")) - node.level + 1]
                target = ".".join(base + ([node.module] if node.module else []))
                found.add(target)
            elif node.module and node.module.startswith("zul"):
                found.add(node.module)
        elif isinstance(node, ast.Import):
            found.update(a.name for a in node.names if a.name.startswith("zul"))
    return found


# --------------------------------------------------------------------------
# Test
# --------------------------------------------------------------------------


@pytest.mark.parametrize("path", zul_modules(), ids=module_name)
def test_third_party_libraries_are_imported_only_in_adapters(path):
    libraries = third_party(imported_roots(path))
    name = module_name(path)

    if path.parent == ADAPTERS_DIR and path.stem in ADAPTERS:
        allowed = ADAPTERS[path.stem] | {"numpy"}
    else:
        allowed = set(EMBEDDED) | PENDING.get(name, set())

    assert libraries <= allowed, (
        f"{name} mengimpor {sorted(libraries - allowed)} langsung. Pindahkan "
        "pemakaiannya ke zul/adapters, atau catat library itu di EMBEDDED."
    )


@pytest.mark.parametrize(
    "path", sorted(ADAPTERS_DIR.glob("*.py")), ids=lambda path: path.stem
)
def test_adapters_import_no_zul_module_outside_adapters(path):
    outside = {m for m in zul_imports(path) if not m.startswith("zul.adapters")}

    assert not outside, f"adapter {path.stem} mengimpor {sorted(outside)}"


def test_every_adapter_file_is_listed():
    files = {path.stem for path in ADAPTERS_DIR.glob("*.py")} - {"__init__"}

    assert files == set(ADAPTERS)


def test_vendored_libraries_keep_their_license():
    copies = VENDOR_DIR.iterdir() if VENDOR_DIR.exists() else []

    for copy in (path for path in copies if path.is_dir()):
        assert list(copy.glob("LICENSE*")), f"{copy.name} butuh file LICENSE aslinya"


def test_nothing_is_left_pending():
    assert not PENDING, f"belum dipindahkan ke adapter: {sorted(PENDING)}"
