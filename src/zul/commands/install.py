"""
Command untuk install utilities secara lokal di project
"""

import typer
import json
from pathlib import Path

app = typer.Typer()

@app.command()
def milvus_helper(config_name: str = "milvus_config.json"):
    """
    Inisialisasi konfigurasi milvus_helper di folder project saat ini.
    """
    typer.echo("📦 Setup milvus_helper config di folder project...")

    # Path ke direktori project (cwd) dan config file
    project_dir = Path.cwd()
    config_file = project_dir / config_name

    # Default konfigurasi
    default_config = {
        "host": "localhost",
        "port": 19530,
        "alias": "default",
        "metadata_dir": str(project_dir / "collections"),
    }

    # Cek dan konfirmasi jika file sudah ada
    if config_file.exists():
        typer.secho("⚠️  milvus_config.json sudah ada di folder project!", fg=typer.colors.YELLOW)
        overwrite = typer.confirm("Ganti konfigurasi lama?", default=False)
        if not overwrite:
            typer.echo("⏹️  Dibatalkan.")
            raise typer.Exit(0)

    # Buat config file baru
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(default_config, f, indent=4)
    typer.secho(f"✅ {config_file} berhasil dibuat!", fg=typer.colors.GREEN)
    
    # # Buat folder koleksi
    # metadata_dir = Path(default_config["metadata_dir"])
    # metadata_dir.mkdir(parents=True, exist_ok=True)

    typer.echo("\n📁 File config:")
    typer.echo(f"  - {config_file}")
    typer.echo("💡 Cara pakai di Python:")
    typer.echo("  from zul.utilities.milvus_helper import Milvus")
    typer.echo(f"  client = Milvus(config_path='{config_file.name}')")
    typer.echo("  client.connect()")
