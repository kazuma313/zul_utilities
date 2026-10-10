"""
Pengetahuan Zul untuk code assistant: modul, cara pakai, contoh, dan aturan gaya.

Gunanya:
    Fungsi di sini membaca source code dan dokumentasi Zul, lalu
    mengembalikannya sebagai teks Markdown yang siap dibaca code assistant.
    Dengan itu, assistant bisa memakai fungsi Zul yang sudah ada dan menulis
    kode baru dengan cara yang sama. MCP server Zul (zul.assistant.server)
    mendaftarkan fungsi-fungsi ini sebagai tool, tetapi semuanya juga bisa
    dipanggil langsung tanpa MCP. Hanya butuh library standar.

Cara pakai:
    from zul.assistant import knowledge

    print(knowledge.list_modules())
    print(knowledge.module_guide("zul.computer_vision.zones"))
    print(knowledge.search_docs("garis penghitung"))
    print(knowledge.check_code(kode_python_baru))

Kode dibaca dengan ast, bukan diimpor, jadi semua modul bisa dijelaskan
walaupun extra-nya belum ter-install.
"""

from __future__ import annotations

import ast
import re
import sys
import textwrap
from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path

from zul.adapters import EMBEDDED

from .comment_style import check_source, describe

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DOC_SECTIONS = ("tutorial", "panduan", "referensi", "konsep")
SITE_URL = "https://zulkit.my.id"
HEADING = re.compile(r"^#{1,6} ")

# --------------------------------------------------------------------------
# Lokasi Kode Dan Dokumentasi
# --------------------------------------------------------------------------
#
# Saat di-install dari wheel, dokumentasi ikut dibawa sebagai zul/_docs.
# Di repository, termasuk saat Zul ter-install editable, dokumentasi
# dibaca dari folder docs yang sejajar dengan src. Jika tidak ada
# keduanya, tool dokumentasi hanya menyebut situs dokumentasi.
#


def docs_root() -> Path | None:
    """Folder dokumentasi Markdown, atau None jika tidak ikut ter-install."""
    for candidate in (PACKAGE_ROOT / "_docs", PACKAGE_ROOT.parents[1] / "docs"):
        if (candidate / "panduan").is_dir():
            return candidate
    return None


def _module_files() -> dict[str, Path]:
    files = {}
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        parts = path.relative_to(PACKAGE_ROOT).parts
        if parts[0] in {"templates", "_docs"} or "__pycache__" in parts:
            continue
        name = ".".join(("zul", *parts)).removesuffix(".py")
        files[name.removesuffix(".__init__")] = path
    return files


def _resolve_module(module: str) -> tuple[str, Path] | str:
    files = _module_files()
    name = module.strip().removesuffix(".py").replace("/", ".")
    for candidate in (name, f"zul.{name}"):
        if candidate in files:
            return candidate, files[candidate]
    near = get_close_matches(f"zul.{name.removeprefix('zul.')}", files, n=3)
    hint = f" Mungkin maksudnya: {', '.join(near)}." if near else ""
    return f"Modul '{module}' tidak ada di Zul.{hint} Lihat daftar di list_modules."


def _docstring(path: Path) -> str:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return ""
    return ast.get_docstring(tree) or ""


# --------------------------------------------------------------------------
# Modul Dan Source Code
# --------------------------------------------------------------------------


def list_modules() -> str:
    """Semua modul Zul per paket, dengan ringkasan isi dan extra yang dibutuhkan.

    Panggil ini lebih dulu untuk tahu fungsi apa yang sudah tersedia
    sebelum menulis kode baru.
    """
    groups: dict[str, list[str]] = {}
    for name, path in _module_files().items():
        doc = _docstring(path)
        summary = doc.strip().splitlines()[0] if doc.strip() else ""
        extra = re.search(r"zul\[([a-z,]+)\]", doc)
        parts = name.split(".")
        package = len(parts) > 1 and (PACKAGE_ROOT / parts[1]).is_dir()
        group = parts[1] if package else "zul"
        row = f"| `{name}` | {summary} | {extra.group(1) if extra else '-'} |"
        groups.setdefault(group, []).append(row)
    lines = ["# Modul Zul", ""]
    for group, rows in groups.items():
        lines += [f"## {group}", "", "| Modul | Isi | Extra |", "|---|---|---|"]
        lines += rows + [""]
    return "\n".join(lines)


def module_guide(module: str) -> str:
    """Cara memakai satu modul: docstring, signature fungsi publik, dan kelasnya.

    `module` boleh ditulis lengkap atau tanpa awalan zul, misalnya
    `computer_vision.zones`.
    """
    resolved = _resolve_module(module)
    if isinstance(resolved, str):
        return resolved
    name, path = resolved
    tree = ast.parse(path.read_text(encoding="utf-8"))
    lines = [f"# {name}", "", ast.get_docstring(tree) or "(tanpa docstring)", ""]
    public = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
        and not node.name.startswith("_")
    ]
    if public:
        lines += ["## Fungsi dan kelas publik", ""]
    for node in public:
        lines += _describe_node(node)
    return "\n".join(lines).rstrip() + "\n"


def _describe_node(node: ast.AST) -> list[str]:
    if isinstance(node, ast.ClassDef):
        init = next(
            (
                item
                for item in node.body
                if isinstance(item, ast.FunctionDef) and item.name == "__init__"
            ),
            None,
        )
        arguments = _arguments(init, skip_self=True) if init else ""
        lines = [f"### `{node.name}({arguments})`", "", ast.get_docstring(node) or ""]
        methods = [
            item
            for item in node.body
            if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef)
            and not item.name.startswith("_")
        ]
        for method in methods:
            summary = (ast.get_docstring(method) or "").split("\n\n")[0]
            if _is_property(method):
                lines.append(f"- `{method.name}` (property): {summary}")
                continue
            signature = f"{method.name}({_arguments(method, skip_self=True)})"
            lines.append(f"- `{signature}`: {summary}")
        return lines + [""]
    returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    signature = f"{node.name}({_arguments(node)}){returns}"
    return [f"### `{signature}`", "", ast.get_docstring(node) or "", ""]


def _is_property(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(
        isinstance(decorator, ast.Name) and decorator.id == "property"
        for decorator in node.decorator_list
    )


def _arguments(node: ast.FunctionDef | ast.AsyncFunctionDef, skip_self=False) -> str:
    text = ast.unparse(node.args)
    if skip_self:
        text = re.sub(r"^(self|cls)(, )?", "", text)
    return text


def read_source(module: str) -> str:
    """Seluruh source code satu modul Zul, untuk ditiru gaya dan polanya.

    Cocok dibaca sebelum menulis modul baru yang mirip, misalnya
    `zul.computer_vision.zones` untuk alat hitung baru atau
    `zul.adapters.opencv` untuk adapter library baru.
    """
    resolved = _resolve_module(module)
    if isinstance(resolved, str):
        return resolved
    name, path = resolved
    relative = path.relative_to(PACKAGE_ROOT.parent).as_posix()
    body = path.read_text(encoding="utf-8")
    return f"# {name}\n\nFile: `{relative}`\n\n```python\n{body}```\n"


# --------------------------------------------------------------------------
# Dokumentasi
# --------------------------------------------------------------------------
#
# Halaman dipotong per judul bagian. Pencarian menilai setiap bagian dari
# jumlah kata kunci yang muncul di judul dan isinya, jadi hasil teratas
# menunjuk langsung ke bagian yang menjawab, bukan ke seluruh halaman.
#


@dataclass(frozen=True)
class _Section:
    page: str
    heading: str
    text: str


def _pages() -> dict[str, Path]:
    root = docs_root()
    if root is None:
        return {}
    pages = {}
    for section in DOC_SECTIONS:
        for path in sorted((root / section).glob("*.md")):
            pages[f"{section}/{path.stem}"] = path
    return pages


def _sections() -> list[_Section]:
    sections = []
    for page, path in _pages().items():
        heading, buffer, in_code = "", [], False
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.lstrip().startswith("```"):
                in_code = not in_code
            if in_code or not HEADING.match(line):
                buffer.append(line)
                continue
            if "".join(buffer).strip():
                sections.append(_Section(page, heading, "\n".join(buffer).strip("\n")))
            heading, buffer = line.lstrip("#").strip(), []
        if "".join(buffer).strip():
            sections.append(_Section(page, heading, "\n".join(buffer).strip("\n")))
    return sections


def _no_docs() -> str:
    return (
        "Dokumentasi Zul tidak ikut ter-install di sini. "
        f"Baca dokumentasinya di {SITE_URL}, atau pakai module_guide."
    )


def list_docs() -> str:
    """Halaman dokumentasi Zul per bagian: tutorial, panduan, referensi, konsep."""
    pages = _pages()
    if not pages:
        return _no_docs()
    lines = ["# Dokumentasi Zul", ""]
    current = ""
    for page, path in pages.items():
        section = page.split("/")[0]
        if section != current:
            lines += ["", f"## {section}", ""]
            current = section
        first = path.read_text(encoding="utf-8").lstrip().splitlines()[0]
        lines.append(f"- `{page}`: {first.lstrip('# ').strip()}")
    return "\n".join(lines).strip() + "\n"


def read_doc(page: str) -> str:
    """Isi lengkap satu halaman dokumentasi, misalnya `panduan/menggambar-di-frame`."""
    pages = _pages()
    if not pages:
        return _no_docs()
    name = page.strip().removesuffix(".md").removesuffix("/")
    if name in pages:
        return pages[name].read_text(encoding="utf-8")
    near = get_close_matches(name, pages, n=3, cutoff=0.4)
    hint = f" Mungkin maksudnya: {', '.join(near)}." if near else ""
    return f"Halaman '{page}' tidak ada.{hint} Lihat daftar di list_docs."


def _terms(query: str) -> list[str]:
    return [word for word in re.findall(r"\w+", query.lower()) if len(word) > 1]


def _score(terms: list[str], heading: str, text: str) -> int:
    heading, text = heading.lower(), text.lower()
    return sum(text.count(term) + 3 * heading.count(term) for term in terms)


def search_docs(query: str, limit: int = 8) -> str:
    """Cari bagian dokumentasi dan docstring modul yang paling cocok dengan kata kunci.

    Mengembalikan bagian terbaik beserta halaman dan potongan isinya.
    Baca halaman lengkapnya dengan read_doc.
    """
    terms = _terms(query)
    if not terms:
        return "Tulis kata kunci pencarian, misalnya: garis penghitung."
    candidates = [(s.page, s.heading, s.text) for s in _sections()]
    for name, path in _module_files().items():
        candidates.append((name, "docstring modul", _docstring(path)))
    ranked = sorted(
        ((_score(terms, heading, text), page, heading, text)
         for page, heading, text in candidates),
        key=lambda item: -item[0],
    )  # fmt: skip
    hits = [item for item in ranked if item[0] > 0][:limit]
    if not hits:
        return f"Tidak ada yang cocok dengan '{query}'. Coba kata kunci lain."
    lines = [f"# Hasil pencarian: {query}", ""]
    for _, page, heading, text in hits:
        lines += [f"## {page} > {heading}", "", _snippet(text, terms), ""]
    return "\n".join(lines)


def _snippet(text: str, terms: list[str], width: int = 400) -> str:
    lowered = text.lower()
    first = min((lowered.find(t) for t in terms if t in lowered), default=0)
    start = max(0, first - 120)
    snippet = text[start : start + width].strip()
    return ("…" if start else "") + snippet + ("…" if len(text) > start + width else "")


def find_examples(topic: str, limit: int = 5) -> str:
    """Contoh kode Python dari dokumentasi Zul yang cocok dengan sebuah topik.

    Contoh berjudul file, misalnya `garis_penghitung.py`, dijalankan oleh
    test Zul, jadi pasti berjalan dengan versi Zul ini.
    """
    terms = _terms(topic)
    if not terms:
        return "Tulis topik contoh, misalnya: heatmap."
    pattern = re.compile(r"^( *)```python([^\n]*)\n(.*?)^\1```", re.S | re.M)
    ranked = []
    for section in _sections():
        for _, title, code in pattern.findall(section.text):
            context = section.heading + " " + title
            score = _score(terms, context, code)
            if score:
                ranked.append((score, section, title.strip(), code))
    ranked.sort(key=lambda item: -item[0])
    if not ranked:
        return f"Tidak ada contoh untuk '{topic}'. Coba search_docs."
    lines = [f"# Contoh kode: {topic}", ""]
    for _, section, title, code in ranked[:limit]:
        dedented = textwrap.dedent(code)
        named = re.search(r'title="([^"]+)"', title)
        label = f" ({named.group(1) if named else title})" if title else ""
        lines += [f"## {section.page} > {section.heading}{label}", ""]
        lines += ["```python", dedented.rstrip(), "```", ""]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Aturan Gaya
# --------------------------------------------------------------------------
#
# Aturan diambil dari tempat yang sama dengan yang dibaca orang: docstring
# lapisan adapter dan halaman Berkontribusi. Begitu halamannya berubah,
# aturan yang dibaca code assistant ikut berubah juga tanpa disalin.
#

BUILDING_BLOCKS = """\
Setiap modul mengerjakan satu hal kecil yang bisa dirangkai, misalnya teks
di sudut frame, garis penghitung, atau timer. Jangan membuat kelas untuk satu
kasus, seperti "perhatian ke rak"; tunjukkan kasus itu sebagai rangkaian
fungsi yang sudah ada. Nama fungsi dan kelas bersifat umum, tanpa istilah
domain. Setiap nilai masuk lewat argumen, tanpa pengaturan global."""

LICENSE_RULES = """\
Zul berlisensi MIT. Jangan menambah library berlisensi AGPL atau GPL;
test_no_dependency_uses_an_agpl_license gagal jika ada. Library berlisensi
MIT, BSD, atau Apache 2.0 boleh dipakai, lewat adapter."""


def conventions() -> str:
    """Aturan menulis kode seperti Zul: fungsi kecil, adapter, docstring, komentar.

    Baca ini sebelum menulis atau mengubah kode di dalam Zul.
    """
    adapters = _docstring(PACKAGE_ROOT / "adapters" / "__init__.py")
    embedded = "\n".join(f"- `{name}`: {reason}" for name, reason in EMBEDDED.items())
    lines = [
        "# Cara menulis kode seperti Zul",
        "",
        "## Fungsi kecil, bukan use case",
        "",
        BUILDING_BLOCKS,
        "",
        "## Library pihak ketiga hanya lewat adapter",
        "",
        adapters,
        "",
        "Library yang boleh diimpor langsung di modul mana pun:",
        "",
        embedded,
        "",
    ]
    contributing = _pages().get("panduan/berkontribusi")
    if contributing is not None:
        text = contributing.read_text(encoding="utf-8")
        for heading in (
            "## Mengikuti gaya kode",
            "## Menulis komentar dan docstring",
            "### Mengikuti gaya penulisan",
        ):
            lines += [_section_text(text, heading), ""]
    else:
        lines += [
            "## Gaya kode",
            "",
            "Format dengan black dan ruff, panjang baris 88. Setiap modul diawali",
            "docstring dengan bagian Gunanya dan Cara pakai. Paragraf komentar",
            "berbentuk anak tangga; periksa dengan check_code.",
            "",
        ]
    lines += ["## Lisensi", "", LICENSE_RULES, ""]
    return "\n".join(lines)


def _section_text(markdown: str, heading: str) -> str:
    level = len(heading.split(" ")[0])
    lines = markdown.splitlines()
    start = lines.index(heading)
    end, in_code = len(lines), False
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if line.lstrip().startswith("```"):
            in_code = not in_code
        marks = len(line) - len(line.lstrip("#"))
        if not in_code and HEADING.match(line) and marks <= level:
            end = index
            break
    return "\n".join(lines[start:end]).strip()


# --------------------------------------------------------------------------
# Memeriksa Kode Baru
# --------------------------------------------------------------------------


def check_code(code: str, inside_zul: bool = True) -> str:
    """Periksa kode Python terhadap aturan Zul sebelum dipakai.

    Yang diperiksa: sintaks, bentuk anak tangga paragraf komentar, dan
    untuk modul di dalam Zul (`inside_zul`), docstring modul serta
    library pihak ketiga yang diimpor di luar adapter.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        return f"Sintaks salah di baris {error.lineno}: {error.msg}"

    problems = []
    for finding in check_source(code):
        advice = (
            "Pakai baris berikut:\n"
            + "\n".join(f"    # {line}" for line in finding.folded)
            if finding.folded
            else "Ganti satu atau dua kata sampai bisa dilipat."
        )
        problems.append(f"Komentar belum anak tangga.\n{describe(finding)}\n{advice}")

    if inside_zul:
        doc = ast.get_docstring(tree) or ""
        for part in ("Gunanya:", "Cara pakai:"):
            if part not in doc:
                problems.append(f"Docstring modul belum punya bagian `{part}`.")
        owners = _adapter_owners()
        for library in sorted(_third_party_imports(tree)):
            adapter = owners.get(library)
            where = (
                f"Pakai fungsi dari `zul.adapters.{adapter}`, yang sudah membungkusnya."
                if adapter
                else "Buat adapter baru di zul/adapters/, dinamai sesuai library-nya."
            )
            problems.append(
                f"`{library}` diimpor langsung. Di dalam Zul, library pihak ketiga "
                f"hanya diimpor di adapter. {where}"
            )

    if not problems:
        return "Tidak ada masalah: kode ini mengikuti aturan Zul yang diperiksa."
    return "\n\n".join(f"{index}. {text}" for index, text in enumerate(problems, 1))


def _adapter_owners() -> dict[str, str]:
    """Library pihak ketiga dan adapter yang mengimpornya, misalnya cv2 ke opencv."""
    owners = {}
    for path in sorted((PACKAGE_ROOT / "adapters").glob("*.py")):
        if path.stem == "__init__":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for library in _third_party_imports(tree) - {"numpy"}:
            owners.setdefault(library, path.stem)
    return owners


def _third_party_imports(tree: ast.AST) -> set[str]:
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.partition(".")[0])
    allowed = set(sys.stdlib_module_names) | {"zul", "__future__"} | set(EMBEDDED)
    return roots - allowed
