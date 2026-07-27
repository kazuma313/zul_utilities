"""
Command untuk build template proyek
"""
import typer
import shutil
from pathlib import Path
from InquirerPy import inquirer

app = typer.Typer()

@app.command()
def hexa(
    name: str = typer.Option(
        None,
        "--name",
        "-n",
        help="Nama proyek (opsional, akan ditanyakan jika tidak diisi)",
    ),
):
    """
    Membuat template proyek hexa dengan MENGCOPY SELURUH isi templates/hexa
    (file & folder apa pun di dalamnya)
    
    Contoh penggunaan:
    $ zul build hexa --name my-project
    $ zul build haxa  # Akan menanyakan nama secara interaktif
    
    """
    if not name:
        name = inquirer.text(message="Masukkan nama proyek:", default="my-hexa-project").execute()  # type: ignore

    confirm = inquirer.confirm(message=f"Buat proyek '{name}' (hexa)?", default=True).execute()  # type: ignore
    if not confirm:
        typer.echo("❌ Dibatalkan")
        raise typer.Exit()

    project_dir = Path(name)
    if project_dir.exists():
        typer.echo(f"❌ Error: Direktori '{name}' sudah ada!")
        raise typer.Exit(1)
    project_dir.mkdir(parents=True)

    template_dir = Path(__file__).parent.parent / "templates" / "hexa"

    # Copy seluruh isi templates/hexa ke hasil
    for item in template_dir.iterdir():
        dest = project_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
            typer.echo(f"📁  Folder {item.name} dicopy.")
        else:
            shutil.copy2(item, dest)
            typer.echo(f"📄  File {item.name} dicopy.")

    typer.echo(f"\n✅ Proyek HEXA '{name}' berhasil dibuat!")
    typer.echo(f"📁 Lokasi: {project_dir.absolute()}")
