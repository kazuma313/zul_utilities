"""
Command untuk build template proyek
"""

import typer
from pathlib import Path
from InquirerPy import inquirer
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

app = typer.Typer()

@app.command()
def web(
    name: str = typer.Option(
        None,
        "--name",
        "-n",
        help="Nama proyek (opsional, akan ditanyakan jika tidak diisi)",
    ),
):
    """
    Membuat template proyek web menggunakan file template dari folder 'templates/web'

    Contoh penggunaan:
    $ zul build web --name my-project
    $ zul build web  # Akan menanyakan nama secara interaktif
    """
    # Jika nama proyek tidak diberikan, tanyakan secara interaktif
    if not name:
        name = inquirer.text(message="Masukkan nama proyek:", default="my-web-project").execute() # type: ignore

    # Konfirmasi sebelum membuat proyek
    confirm = inquirer.confirm(message=f"Buat proyek '{name}'?", default=True).execute() # type: ignore
    if not confirm:
        typer.echo("❌ Dibatalkan")
        raise typer.Exit()

    # Tentukan direktori output
    project_dir = Path(name)
    if project_dir.exists():
        typer.echo(f"❌ Error: Direktori '{name}' sudah ada!")
        raise typer.Exit(1)
    project_dir.mkdir(parents=True)

    # Path ke folder templates
    template_dir = Path(__file__).parent.parent / "templates" / "web"

    # Siapkan environment Jinja2
    env = Environment(loader=FileSystemLoader(template_dir))

    # Konteks variabel yang akan diisi di template
    context = {"project_name": name}

    # Daftar file template yang akan digenerate
    templates = {
        "main.py.j2": "main.py",
        "README.md.j2": "README.md",
        "requirements.txt.j2": "requirements.txt",
    }

    # Iterasi setiap template
    for src, dest in templates.items():
        try:
            template = env.get_template(src)
            rendered = template.render(context)
            (project_dir / dest).write_text(rendered, encoding="utf-8")
            typer.echo(f"📝  Membuat file {dest}")
        except TemplateNotFound:
            typer.echo(f"⚠️  Template {src} tidak ditemukan di {template_dir}")

    typer.echo(f"\n✅ Proyek '{name}' berhasil dibuat!")
    typer.echo(f"📁 Lokasi: {project_dir.absolute()}")
