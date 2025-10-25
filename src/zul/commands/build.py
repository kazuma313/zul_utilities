"""
Command untuk build template proyek
"""
import typer
from pathlib import Path
from InquirerPy import inquirer
from jinja2 import Template

app = typer.Typer()

@app.command()
def web(
    name: str = typer.Option(
        None, 
        "--name", 
        "-n",
        help="Nama proyek (opsional, akan ditanyakan jika tidak diisi)"
    )
):
    """
    Membuat template proyek web
    
    Contoh penggunaan:
    $ zul build web --name my-project
    $ zul build web  # Akan menanyakan nama secara interaktif
    """
    # Jika nama tidak diberikan sebagai option, tanyakan dengan InquirerPy
    if not name:
        name = inquirer.text(
            message="Masukkan nama proyek:",
            default="my-web-project"
        ).execute()
    
    # Konfirmasi sebelum membuat proyek
    confirm = inquirer.confirm(
        message=f"Buat proyek '{name}'?",
        default=True
    ).execute()
    
    if not confirm:
        typer.echo("❌ Dibatalkan")
        raise typer.Exit()
    
    # Buat direktori proyek
    project_dir = Path(name)
    
    if project_dir.exists():
        typer.echo(f"❌ Error: Direktori '{name}' sudah ada!")
        raise typer.Exit(1)
    
    project_dir.mkdir(parents=True)
    
    # Template untuk main.py menggunakan Jinja2
    main_template = """# {{ project_name }}
# File ini dibuat otomatis oleh zul

def main():
    print("Hello from {{ project_name }}!")

if __name__ == "__main__":
    main()
"""
    
    # Template untuk README.md
    readme_template = """# {{ project_name }}

Proyek ini dibuat menggunakan `zul build web`

## Cara menjalankan
```python
python main.py
```

## Struktur Proyek

{{ project_name }}/
├── main.py
├── README.md
└── requirements.txt

"""
    # Context data untuk template
    context = {"project_name": name}
    
    # Generate dan tulis file menggunakan Jinja2
    main_content = Template(main_template).render(context)
    (project_dir / "main.py").write_text(main_content)
    
    readme_content = Template(readme_template).render(context)
    (project_dir / "README.md").write_text(readme_content)
    
    (project_dir / "requirements.txt").write_text("# Dependencies\n")
    
    # Tampilkan pesan sukses
    typer.echo(f"✅ Proyek '{name}' berhasil dibuat!")
    typer.echo(f"📁 Lokasi: {project_dir.absolute()}")
    typer.echo("\n📝 File yang dibuat:")
    typer.echo(f"  - {name}/main.py")
    typer.echo(f"  - {name}/README.md")
    typer.echo(f"  - {name}/requirements.txt")