"""
Kelompok perintah CLI. Satu file = satu kelompok.

Isi folder:
    build.py     `zul build ...`    membuat proyek dari template
    install.py   `zul install ...`  menulis file config utilitas

Contoh perintah baru di dalam kelompok yang sudah ada:
    # commands/build.py
    @app.command()
    def api(name: str = typer.Option(..., "--name", "-n")):
        '''Membuat proyek API minimal.'''
        copy_template("api", Path(name))
"""
