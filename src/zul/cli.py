"""
CLI Entry Point untuk Zul

Gunanya:
    Mendaftarkan semua perintah `zul`. Entry point ini di-install oleh
    `[project.scripts]` di pyproject.toml: `zul = "zul.cli:app"`.

Cara pakai:
    zul --help
    zul --version
    zul build hexa --name my-app
    zul install milvus-helper

Cara menambah kelompok perintah baru (misal `zul deploy ...`):
    1. Buat `zul/commands/deploy.py` berisi `app = typer.Typer()` dan
       fungsi berdekorator `@app.command()`.
    2. Daftarkan di sini: `app.add_typer(deploy.app, name="deploy")`.
"""

import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

import typer

from zul.commands import build, install

PACKAGE_NAME = "zul"

# --------------------------------------------------------------------------
# Keluaran yang Tahan Encoding
# --------------------------------------------------------------------------
#
# Pesan Zul memakai emoji. Di Windows, keluaran yang dialihkan ke file atau
# ke program lain sering memakai encoding yang tidak mengenal emoji, dan
# tanpa penjagaan ini perintahnya gagal sebelum mengerjakan apa pun.
# Karakter yang tidak bisa ditulis diganti dengan tanda tanya.
#


def _tolerate_unencodable_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)

        if reconfigure is not None:
            reconfigure(errors="replace")


_tolerate_unencodable_output()

# --------------------------------------------------------------------------
# Aplikasi dan Kelompok Perintah
# --------------------------------------------------------------------------
#
# Setiap kelompok perintah tinggal di modulnya sendiri dalam folder
# commands, kemudian didaftarkan di sini dengan namanya. Hasilnya
# adalah perintah bertingkat seperti perintah zul build hexa.
#

app = typer.Typer(
    name=PACKAGE_NAME,
    help="🚀 CLI tool untuk membuat template proyek dan utilities",
    add_completion=False,
    no_args_is_help=True,
)

app.add_typer(build.app, name="build")
app.add_typer(install.app, name="install")

# --------------------------------------------------------------------------
# Versi
# --------------------------------------------------------------------------


def get_version() -> str:
    """Versi zul yang ter-install, dibaca dari metadata package (pyproject.toml)."""
    try:
        return package_version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "unknown"


def _print_version_and_exit(show_version: bool) -> None:
    if show_version:
        typer.echo(f"{PACKAGE_NAME} version {get_version()}")

        raise typer.Exit()


# --------------------------------------------------------------------------
# Perintah Utama
# --------------------------------------------------------------------------


@app.callback()
def main(
    show_version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Tampilkan versi zul lalu keluar",
        callback=_print_version_and_exit,
        is_eager=True,
    ),
):
    """🚀 CLI tool untuk membuat template proyek dan utilities"""


@app.command()
def version():
    """Tampilkan versi zul"""
    typer.echo(f"{PACKAGE_NAME} version {get_version()}")


if __name__ == "__main__":
    app()
