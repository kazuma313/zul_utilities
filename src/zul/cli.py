"""
CLI Entry Point untuk Zul
"""

import typer
from zul.commands import build, install

# Buat aplikasi Typer utama
app = typer.Typer(
    name="zul",
    help="🚀 CLI tool untuk membuat template proyek dan utilities",
    add_completion=False,
)

# Register subcommands
app.add_typer(build.app, name="build")
app.add_typer(install.app, name="install")


@app.command()
def version():
    """Tampilkan versi zul"""
    typer.echo("zul version 0.1.0")


if __name__ == "__main__":
    app()
