"""
Command untuk build template proyek

Gunanya:
    `zul build hexa` menyalin seluruh isi `zul/templates/hexa` menjadi
    proyek baru, lalu menulis nama proyek ke README-nya.

Cara pakai:
    zul build hexa                          # interaktif, menanyakan nama
    zul build hexa --name my-app            # nama langsung, masih konfirmasi
    zul build hexa --name my-app --yes      # tanpa konfirmasi (script / CI)

Cara menambah template baru (misal `api`):
    1. Buat folder `zul/templates/api/` berisi kerangka proyeknya.
       Folder kosong perlu file `.gitkeep` supaya ikut ter-copy.
    2. Tambahkan perintahnya:

        @app.command()
        def api(name: str = typer.Option(..., "--name", "-n")):
            copy_template("api", Path(name))

Dipakai dari Python (misalnya di test):
    from zul.commands.build import copy_template

    copy_template("hexa", Path("my-app"))
"""

import shutil
from pathlib import Path

import typer
from InquirerPy import inquirer

app = typer.Typer(no_args_is_help=True, help="Buat proyek baru dari template")

# --------------------------------------------------------------------------
# Lokasi dan Aturan Template
# --------------------------------------------------------------------------
#
# Template ikut ter-install bersama package, di folder templates yang
# bersebelahan dengan folder commands. File hasil samping Python
# dilewati supaya tidak ikut tersalin ke dalam proyek baru.
#

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
DEFAULT_HEXA_PROJECT_NAME = "my-hexa-project"
PROJECT_NAME_PLACEHOLDER = "{{ project_name }}"

_IGNORED_TEMPLATE_FILES = shutil.ignore_patterns("__pycache__", "*.py[cod]")

# --------------------------------------------------------------------------
# Pertanyaan Interaktif
# --------------------------------------------------------------------------


def _ask_project_name() -> str:
    return inquirer.text(  # type: ignore
        message="Masukkan nama proyek:", default=DEFAULT_HEXA_PROJECT_NAME
    ).execute()


def _confirm_creation(name: str) -> bool:
    return inquirer.confirm(  # type: ignore
        message=f"Buat proyek '{name}' (hexa)?", default=True
    ).execute()


# --------------------------------------------------------------------------
# Menyalin Template
# --------------------------------------------------------------------------


def copy_template(template_name: str, project_dir: Path) -> list[Path]:
    """
    Copy SELURUH isi templates/<template_name> ke project_dir.

    Returns:
        Daftar file/folder level teratas yang dibuat di project_dir.

    Raises:
        FileNotFoundError: Jika template tidak ada di package.
        FileExistsError: Jika project_dir sudah ada.
    """
    template_dir = TEMPLATES_DIR / template_name
    if not template_dir.is_dir():
        raise FileNotFoundError(
            f"Template '{template_name}' tidak ditemukan: {template_dir}"
        )

    if project_dir.exists():
        raise FileExistsError(f"Direktori '{project_dir}' sudah ada!")

    # Kalau penyalinan gagal di tengah jalan, folder proyek yang baru
    # terisi sebagian dihapus lagi. Proyek yang setengah jadi jauh
    # lebih menyesatkan dibanding tidak ada proyek sama sekali.
    try:
        shutil.copytree(template_dir, project_dir, ignore=_IGNORED_TEMPLATE_FILES)
    except Exception:
        shutil.rmtree(project_dir, ignore_errors=True)
        raise

    return sorted(project_dir.iterdir())


def render_project_name(project_dir: Path, project_name: str) -> None:
    """Ganti placeholder nama proyek di README hasil generate."""
    readme = project_dir / "README.md"

    if not readme.is_file():
        return

    text = readme.read_text(encoding="utf-8")
    rendered = text.replace(PROJECT_NAME_PLACEHOLDER, project_name)

    readme.write_text(rendered, encoding="utf-8")


# --------------------------------------------------------------------------
# Perintah
# --------------------------------------------------------------------------


@app.command()
def hexa(
    name: str = typer.Option(
        None,
        "--name",
        "-n",
        help="Nama proyek (opsional, akan ditanyakan jika tidak diisi)",
    ),
    skip_confirmation: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Lewati konfirmasi (berguna untuk script / CI)",
    ),
):
    """
    Membuat template proyek hexa dengan MENGCOPY SELURUH isi templates/hexa
    (file & folder apa pun di dalamnya)

    Contoh penggunaan:
    $ zul build hexa --name my-project
    $ zul build hexa --name my-project --yes   # Tanpa konfirmasi
    $ zul build hexa  # Akan menanyakan nama secara interaktif

    """
    name = (name or _ask_project_name()).strip()

    if not name:
        typer.echo("❌ Error: Nama proyek tidak boleh kosong!")
        raise typer.Exit(1)

    if not skip_confirmation and not _confirm_creation(name):
        typer.echo("❌ Dibatalkan")
        raise typer.Exit()

    project_dir = Path(name)

    try:
        created_items = copy_template("hexa", project_dir)
    except FileExistsError:
        typer.echo(f"❌ Error: Direktori '{name}' sudah ada!")
        raise typer.Exit(1) from None

    render_project_name(project_dir, project_dir.name)

    for item in created_items:
        if item.is_dir():
            typer.echo(f"📁  Folder {item.name} dicopy.")
        else:
            typer.echo(f"📄  File {item.name} dicopy.")

    typer.echo(f"\n✅ Proyek HEXA '{name}' berhasil dibuat!")
    typer.echo(f"📁 Lokasi: {project_dir.absolute()}")
