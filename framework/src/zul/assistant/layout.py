"""
Aturan dan pemeriksa struktur proyek berinduk: backend, frontend, mobile, assets.

Gunanya:
    Satu proyek dibagi menjadi empat induk di root-nya: `backend`, `frontend`,
    `mobile`, dan `assets`. Modul ini menjelaskan aturannya dan memeriksa
    sebuah folder proyek terhadap aturan itu: file mana yang belum berada di
    induknya, impor yang melompati batas induk, dan induk yang kekurangan
    README atau manifest. Hasilnya berupa rencana pemindahan dengan perintah
    `git mv`. Modul ini hanya membaca; code assistant yang memindahkan file,
    setelah kamu setuju. Aturan lengkapnya ada di halaman konsep Struktur
    proyek berinduk. Hanya butuh library standar.

Cara pakai:
    from zul.assistant import layout

    print(layout.layout_rules())
    print(layout.check_layout("C:/proyek/toko"))

Yang dibaca:
    Nama file dan folder, isi `package.json` (hanya nama dependency), dan
    baris impor di file kode. Isi `.env` tidak pernah dibaca; hanya
    keberadaannya yang diperiksa. Symlink tidak diikuti.

Batasnya:
    Hanya folder di dalam folder kerja server, atau di dalam folder yang
    terdaftar di environment variable ZUL_PROJECT_ROOTS (dipisah `os.pathsep`),
    yang diperiksa. Root drive dan folder home ditolak. Nama file dianggap
    data tidak tepercaya: nama berkarakter khusus tidak dibuatkan perintah
    `git mv` dan ditampilkan ber-escape.
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from .knowledge import _pages

# --------------------------------------------------------------------------
# Aturan Induk
# --------------------------------------------------------------------------

PARENTS = ("backend", "frontend", "mobile", "assets")
CODE_PARENTS = ("backend", "frontend", "mobile")
DOC_PAGE = "konsep/struktur-proyek-berinduk"

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    ".dart_tool",
    ".next",
    ".nuxt",
    "dist",
    "build",
    "Pods",
}

# File dan folder yang boleh tinggal di root, di luar keempat induk.
ROOT_NAMES = {
    "docs",
    "scripts",
    "infra",
    "Makefile",
    "justfile",
    "LICENSE",
}
ROOT_PREFIXES = ("README", "CONTRIBUTING", "CHANGELOG", "LICENSE", "docker-compose")

ASSET_FOLDERS = {
    "images": {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".bmp"},
    "fonts": {".ttf", ".otf", ".woff", ".woff2"},
    "videos": {".mp4", ".mov", ".avi", ".mkv", ".webm"},
    "audio": {".mp3", ".wav", ".ogg", ".m4a"},
    "data": {".csv", ".parquet"},
    "design": {".psd", ".fig", ".sketch", ".ai"},
    "documents": {".pdf", ".docx", ".pptx", ".xlsx"},
}
ASSET_EXTENSIONS = {ext for group in ASSET_FOLDERS.values() for ext in group}
CODE_IN_ASSETS = {".py", ".js", ".ts", ".tsx", ".jsx", ".sh", ".dart", ".java"}
CODE_IN_ASSETS |= {".kt", ".swift", ".php", ".rb", ".go", ".rs"}

# --------------------------------------------------------------------------
# Tanda Pengenal Isi Folder
# --------------------------------------------------------------------------
#
# Setiap tanda memilih satu induk. Folder yang cocok dengan lebih dari
# satu induk tidak ditebak: ia dilaporkan sebagai perlu keputusan.
#

BACKEND_FILES = {
    "pyproject.toml",
    "requirements.txt",
    "Pipfile",
    "manage.py",
    "alembic.ini",
    "go.mod",
    "pom.xml",
    "Cargo.toml",
    "composer.json",
    "Gemfile",
}
MOBILE_FILES = {"pubspec.yaml", "AndroidManifest.xml", "Podfile"}
FRONTEND_CONFIG = re.compile(
    r"(?:vite|next|nuxt|astro|svelte)\.config\.(?:js|ts|mjs|cjs|mts|cts)|angular\.json"
)
MOBILE_PACKAGES = {"react-native", "expo", "@capacitor/core", "nativescript"}
FRONTEND_PACKAGES = {
    "react-dom",
    "next",
    "vue",
    "nuxt",
    "svelte",
    "@sveltejs/kit",
    "@angular/core",
    "astro",
    "solid-js",
    "vite",
}
BACKEND_PACKAGES = {"express", "fastify", "@nestjs/core", "koa", "hono"}
EXTENSION_PARENT = {
    ".py": "backend",
    ".dart": "mobile",
    ".swift": "mobile",
    ".js": "frontend",
    ".jsx": "frontend",
    ".ts": "frontend",
    ".tsx": "frontend",
    ".vue": "frontend",
    ".svelte": "frontend",
}

MAX_FILES = 4000
MAX_FILE_BYTES = 500_000
MAX_LISTED = 20
SCANNED_CODE = {".py", ".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".dart"}
IMPORT_PATH = re.compile(r"""(?:from|import|require\()\s*['"](\.{1,2}/[^'"]+)['"]""")
PYTHON_IMPORT = re.compile(r"^\s*(?:from|import)\s+(backend|frontend|mobile)\b")

# --------------------------------------------------------------------------
# Batas Aman
# --------------------------------------------------------------------------
#
# Nama file berasal dari folder yang diperiksa, jadi dianggap data yang
# tidak tepercaya. Nama berkarakter khusus tidak dibuatkan perintah
# `git mv` dan ditampilkan ber-escape. Yang aman hanya huruf,
# angka, spasi, titik, minus, garis bawah, dan garis miring.
#
# Folder yang boleh diperiksa dibatasi ke folder kerja server,
# ditambah daftar di environment variable ZUL_PROJECT_ROOTS.
#

SAFE_TEXT = re.compile(r"[\w ./-]{1,200}")
MAX_LABEL = 80
ROOTS_ENV = "ZUL_PROJECT_ROOTS"


def layout_rules() -> str:
    """Aturan struktur proyek berinduk: backend, frontend, mobile, dan assets.

    Baca ini sebelum membuat proyek baru atau merapikan proyek yang sudah ada.
    """
    page = _pages().get(DOC_PAGE)
    if page is not None:
        return page.read_text(encoding="utf-8")
    return "\n".join(
        [
            "# Struktur proyek berinduk",
            "",
            "Root proyek hanya berisi empat induk: `backend`, `frontend`,",
            "`mobile`, dan `assets`, ditambah README, docs, dan konfigurasi.",
            "Setiap induk punya manifest, README, dan test sendiri.",
            "`frontend` dan `mobile` memanggil `backend` hanya lewat HTTP API.",
            "`backend` tidak mengimpor induk lain. `assets` tidak berisi kode.",
            "",
            "Halaman lengkap: https://zulkit.my.id/konsep/struktur-proyek-berinduk/",
        ]
    )


# --------------------------------------------------------------------------
# Mengenali Isi Sebuah File Atau Folder
# --------------------------------------------------------------------------


@dataclass
class Verdict:
    """Induk yang cocok dengan sebuah file atau folder, dan alasannya."""

    candidates: dict[str, str] = field(default_factory=dict)

    @property
    def parent(self) -> str | None:
        return next(iter(self.candidates)) if len(self.candidates) == 1 else None

    def reason(self) -> str:
        return "; ".join(f"{p}: {why}" for p, why in self.candidates.items())


def _walk(folder: Path, depth: int = 3):
    base = len(folder.parts)
    for current, dirs, files in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS)
        if len(Path(current).parts) - base >= depth:
            dirs[:] = []
        yield Path(current), dirs, sorted(files)


def _package_parent(path: Path) -> tuple[str, str] | None:
    try:
        if path.is_symlink() or path.stat().st_size > MAX_FILE_BYTES:
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    names = set()
    for key in ("dependencies", "devDependencies"):
        section = data.get(key)
        if isinstance(section, dict):
            names |= set(section)
    for parent, packages in (
        ("mobile", MOBILE_PACKAGES),
        ("frontend", FRONTEND_PACKAGES),
        ("backend", BACKEND_PACKAGES),
    ):
        found = sorted(names & packages)
        if found:
            return parent, f"package.json memakai {found[0]}"
    return None


def _file_verdict(path: Path) -> Verdict:
    name, extension = path.name, path.suffix.lower()
    verdict = Verdict()
    if name in BACKEND_FILES:
        verdict.candidates["backend"] = f"file {name}"
    elif name in MOBILE_FILES:
        verdict.candidates["mobile"] = f"file {name}"
    elif name == "package.json" and (found := _package_parent(path)):
        verdict.candidates[found[0]] = found[1]
    elif FRONTEND_CONFIG.fullmatch(name):
        verdict.candidates["frontend"] = f"file {name}"
    elif extension in EXTENSION_PARENT:
        verdict.candidates[EXTENSION_PARENT[extension]] = f"file {extension}"
    elif extension in ASSET_EXTENSIONS:
        verdict.candidates["assets"] = f"file {extension}"
    return verdict


def _folder_verdict(folder: Path) -> Verdict:
    found: dict[str, str] = {}
    votes: Counter[str] = Counter()
    seen = 0
    for current, dirs, files in _walk(folder):
        for name in dirs:
            if name in {"android", "ios"} or name.endswith(".xcodeproj"):
                found.setdefault("mobile", f"folder {_label(name)}")
        for name in files:
            seen += 1
            if seen > MAX_FILES:
                break
            path = current / name
            extension = path.suffix.lower()
            if _is_marker(name):
                found.update(_file_verdict(path).candidates)
            elif extension in EXTENSION_PARENT:
                votes[EXTENSION_PARENT[extension]] += 1
            elif extension in ASSET_EXTENSIONS:
                votes["assets"] += 1
    verdict = Verdict(found)
    if verdict.candidates:
        return verdict
    code = Counter({parent: n for parent, n in votes.items() if parent != "assets"})
    if code:
        top, count = code.most_common(1)[0]
        if count / sum(code.values()) >= 0.6:
            verdict.candidates[top] = f"{count} file kode {top}"
    elif votes["assets"]:
        verdict.candidates["assets"] = f"{votes['assets']} file asset, tanpa kode"
    return verdict


def _is_marker(name: str) -> bool:
    return (
        name == "package.json"
        or name in BACKEND_FILES | MOBILE_FILES
        or bool(FRONTEND_CONFIG.fullmatch(name))
    )


def _classify(entry: Path) -> Verdict:
    return _file_verdict(entry) if entry.is_file() else _folder_verdict(entry)


# --------------------------------------------------------------------------
# Pemeriksaan Satu Proyek
# --------------------------------------------------------------------------


def _is_root_allowed(name: str) -> bool:
    return name.startswith(".") or name in ROOT_NAMES or name.startswith(ROOT_PREFIXES)


def _is_safe(text: str) -> bool:
    return bool(SAFE_TEXT.fullmatch(text))


def _label(text: str) -> str:
    """Nama untuk ditampilkan: nama asli jika aman, jika tidak versi ber-escape."""
    if _is_safe(text):
        return text
    parts = []
    for char in text:
        code = ord(char)
        if SAFE_TEXT.fullmatch(char):
            parts.append(char)
        elif code < 0x100:
            parts.append(f"\\x{code:02x}")
        elif code < 0x10000:
            parts.append(f"\\u{code:04x}")
        else:
            parts.append(f"\\U{code:08x}")
    return "".join(parts)[:MAX_LABEL]


def _quote(name: str) -> str:
    return f'"{name}"' if " " in name else name


def _asset_destination(entry: Path) -> str:
    if entry.is_dir():
        return f"assets/{entry.name}"
    for folder, extensions in ASSET_FOLDERS.items():
        if entry.suffix.lower() in extensions:
            return f"assets/{folder}/{entry.name}"
    return f"assets/{entry.name}"


def _is_app_root(folder: Path) -> bool:
    names = {path.name for path in folder.iterdir() if path.is_file()}
    return any(_is_marker(name) for name in names)


def _target(root: Path, parent: str, entry: Path, group: list) -> str:
    if parent == "assets":
        return _asset_destination(entry)
    alone = len(group) == 1 and entry.is_dir() and _is_app_root(entry)
    if alone and not (root / parent).exists():
        return parent
    return f"{parent}/{entry.name}"


def _misplaced(root: Path) -> tuple[list[str], list[str]]:
    planned: dict[str, list[tuple[Path, Verdict]]] = {}
    decisions = []
    for entry in sorted(root.iterdir(), key=lambda path: path.name.lower()):
        name = entry.name
        if name in PARENTS or name in IGNORED_DIRS or _is_root_allowed(name):
            continue
        if not _is_safe(name):
            decisions.append(
                f"`{_label(name)}`: nama mengandung karakter khusus atau terlalu "
                "panjang, jadi tidak dibuatkan perintah. Ganti namanya dulu."
            )
            continue
        if entry.is_symlink():
            decisions.append(f"`{name}` adalah symlink; tidak diperiksa.")
            continue
        verdict = _classify(entry)
        if verdict.parent is None:
            why = verdict.reason() or "tidak ada tanda yang dikenali"
            decisions.append(f"`{name}`: {why}.")
            continue
        planned.setdefault(verdict.parent, []).append((entry, verdict))

    moves = []
    for parent in PARENTS:
        group = planned.get(parent, [])
        for entry, verdict in group:
            target = _target(root, parent, entry, group)
            if (root / target).exists():
                decisions.append(
                    f"`{entry.name}` cocok dengan {parent}, "
                    f"tetapi `{target}` sudah ada."
                )
                continue
            moves.append(
                f"`{entry.name}` termasuk {parent} ({verdict.reason()}).\n"
                f"   `git mv -- {_quote(entry.name)} {_quote(target)}`"
            )
    return moves, decisions


def _code_files(folder: Path):
    seen = 0
    for current, _, files in _walk(folder, depth=8):
        for name in files:
            path = current / name
            if path.suffix.lower() not in SCANNED_CODE or path.is_symlink():
                continue
            seen += 1
            if seen > MAX_FILES:
                return
            yield path


def _crossings(root: Path, present: list[str]) -> list[str]:
    findings = []
    for parent in (p for p in present if p in CODE_PARENTS):
        for path in _code_files(root / parent):
            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    continue
                lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                continue
            for number, line in enumerate(lines, 1):
                target = _crossed_parent(root, parent, path, line)
                if target:
                    where = _label(path.relative_to(root).as_posix())
                    findings.append(
                        f"`{where}:{number}` ({parent}) mengimpor {target}."
                    )
    return findings


def _crossed_parent(root: Path, parent: str, path: Path, line: str) -> str | None:
    if path.suffix == ".py":
        found = PYTHON_IMPORT.match(line)
        if found and found.group(1) != parent:
            return f"`{found.group(1)}`"
        return None
    found = IMPORT_PATH.search(line)
    if not found:
        return None
    try:
        relative = (path.parent / found.group(1)).resolve().relative_to(root)
    except ValueError:
        return None
    top = relative.parts[0] if relative.parts else ""
    if top in CODE_PARENTS and top != parent:
        return f"`{_label(found.group(1))}` (induk {top})"
    return None


def _missing(root: Path, present: list[str]) -> list[str]:
    findings = []
    for parent in (p for p in present if p in CODE_PARENTS):
        folder = root / parent
        if not (folder / "README.md").is_file():
            findings.append(f"`{parent}` belum punya README.md.")
        if not _has_manifest(folder, parent):
            findings.append(f"`{parent}` belum punya manifest dependency sendiri.")
    for folder in [root, *(root / p for p in present)]:
        if (folder / ".env").is_file():
            findings += _env_findings(root, folder)
    if "assets" in present:
        for current, _, files in _walk(root / "assets", depth=8):
            for name in files:
                if Path(name).suffix.lower() in CODE_IN_ASSETS:
                    where = _label((current / name).relative_to(root).as_posix())
                    findings.append(f"`{where}` adalah kode, bukan asset.")
    return findings


def _has_manifest(folder: Path, parent: str) -> bool:
    names = {
        "backend": BACKEND_FILES | {"package.json"},
        "frontend": {"package.json", "angular.json"},
        "mobile": MOBILE_FILES | {"package.json"},
    }[parent]
    return any((folder / name).is_file() for name in names)


def _env_findings(root: Path, folder: Path) -> list[str]:
    where = _label(folder.relative_to(root).as_posix()) if folder != root else "."
    findings = []
    ignored = False
    for ignore in {root / ".gitignore", folder / ".gitignore"}:
        if ignore.is_file():
            lines = ignore.read_text(encoding="utf-8", errors="ignore").splitlines()
            ignored |= any(line.strip() in {".env", "*.env", ".env*"} for line in lines)
    if not ignored:
        findings.append(
            f"`{where}/.env` ada, tetapi `.gitignore` belum mengabaikannya."
        )
    if not (folder / ".env.example").is_file():
        findings.append(f"`{where}/.env` ada tanpa `.env.example` di sebelahnya.")
    return findings


def _allowed_roots() -> list[Path]:
    roots = [Path.cwd()]
    for item in os.environ.get(ROOTS_ENV, "").split(os.pathsep):
        if item.strip():
            roots.append(Path(item).expanduser())
    return [root.resolve() for root in roots]


def _refusal(root: Path, requested: str) -> str | None:
    """Alasan menolak memeriksa folder ini, atau None jika boleh."""
    if root == Path(root.anchor) or root == Path.home().resolve():
        return (
            f"Folder `{_label(requested)}` terlalu luas untuk satu proyek. "
            "Pilih folder root proyeknya."
        )
    if any(root.is_relative_to(allowed) for allowed in _allowed_roots()):
        return None
    return (
        f"Folder `{_label(requested)}` berada di luar folder kerja server. "
        "Jalankan code assistant dari folder proyek itu, atau daftarkan folder "
        f"tersebut di environment variable {ROOTS_ENV} (pisahkan dengan "
        f"`{os.pathsep}`) sebelum server dinyalakan."
    )


def _numbered(items: list[str]) -> list[str]:
    shown = items[:MAX_LISTED]
    lines = [f"{index}. {text}" for index, text in enumerate(shown, 1)]
    if len(items) > MAX_LISTED:
        lines.append(f"... dan {len(items) - MAX_LISTED} temuan lain.")
    return lines


def check_layout(path: str = ".") -> str:
    """Periksa folder proyek terhadap struktur backend, frontend, mobile, assets.

    Mengembalikan rencana: file yang perlu dipindahkan beserta perintah
    `git mv`, folder yang perlu keputusan, impor yang melompati batas induk,
    dan kekurangan tiap induk. Tool ini tidak mengubah file apa pun; pindahkan
    file hanya setelah pemilik proyek setuju, lalu panggil lagi sampai bersih.

    Args:
        path: Folder root proyek, di dalam folder kerja server atau di dalam
            folder yang terdaftar di ZUL_PROJECT_ROOTS. Default: folder kerja.
    """
    root = Path(path).expanduser().resolve()
    refusal = _refusal(root, path)
    if refusal:
        return refusal
    if not root.is_dir():
        return f"Folder `{_label(path)}` tidak ditemukan atau bukan folder."

    linked = [parent for parent in PARENTS if (root / parent).is_symlink()]
    present = [
        parent
        for parent in PARENTS
        if (root / parent).is_dir() and parent not in linked
    ]
    absent = [parent for parent in PARENTS if parent not in present]
    moves, decisions = _misplaced(root)
    decisions += [f"`{parent}` adalah symlink; tidak diperiksa." for parent in linked]
    crossings = _crossings(root, present)
    missing = _missing(root, present)

    lines = [
        f"# Pemeriksaan struktur: {_label(root.name)}",
        "",
        f"Induk yang ada: {', '.join(present) or 'belum ada'}.",
        f"Induk yang belum ada: {', '.join(absent) or 'tidak ada'}. "
        "Induk yang tidak dibutuhkan proyek ini boleh dilewati.",
        "",
    ]
    sections = (
        ("Perlu dipindahkan", moves),
        ("Perlu keputusan pemilik proyek", decisions),
        ("Impor yang melompati batas induk", crossings),
        ("Kekurangan di tiap induk", missing),
    )
    total = 0
    for title, items in sections:
        if items:
            total += len(items)
            lines += [f"## {title}", "", *_numbered(items), ""]
    if not total:
        lines += ["Struktur sudah sesuai: tidak ada temuan.", ""]
    else:
        lines += [
            "## Setelah memindahkan",
            "",
            "Perbarui path di Dockerfile, docker-compose, konfigurasi CI, dan README,",
            "lalu jalankan test di setiap induk dan panggil `check_layout` lagi.",
        ]
    return "\n".join(lines)
