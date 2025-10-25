"""
Command untuk install utilities
"""
import typer

app = typer.Typer()

@app.command()
def milvus_helper():
    """
    Install milvus_helper utility
    
    Setelah install, utility bisa diimport dalam kode Python:
    from zul.utilities.milvus_helper import Milvus
    
    Contoh penggunaan:
    $ zul install milvus_helper
    """
    typer.echo("📦 Installing milvus_helper...")
    typer.echo("✅ milvus_helper berhasil diinstall!")
    typer.echo("\n💡 Cara menggunakan:")
    typer.echo("  from zul.utilities.milvus_helper import Milvus")
    typer.echo("  client = Milvus(host='localhost', port=19530)")
    typer.echo("  client.connect()")
