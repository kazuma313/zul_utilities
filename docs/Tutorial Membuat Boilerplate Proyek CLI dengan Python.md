<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Tutorial Membuat Boilerplate Proyek CLI dengan Python UV

Tutorial ini akan memandu Anda langkah demi langkah untuk membuat CLI tool bernama **"zul"** yang dapat membuat template proyek dan menginstall utility helper. Tutorial ini dirancang khusus untuk pemula dan menggunakan pendekatan yang sederhana dan mudah dipahami.

![Alur kerja CLI tool "zul" untuk membuat boilerplate proyek dan menginstall utilities](https://ppl-ai-code-interpreter-files.s3.amazonaws.com/web/direct-files/554761d40f556b0bea0c7b58f41ca540/95b9846e-8eba-4ffd-8dd1-0b442a43be0c/a0dac2ed.png)

Alur kerja CLI tool "zul" untuk membuat boilerplate proyek dan menginstall utilities

## Pendahuluan

**Zul** adalah CLI (Command Line Interface) tool yang akan Anda buat untuk membantu mempercepat development workflow. Tool ini memiliki dua fungsi utama:

1. **`zul build web`** - Membuat template struktur proyek web secara otomatis
2. **`zul install milvus_helper`** - Menginstall utility helper yang bisa diimport dalam kode Python

### Kenapa Membuat CLI Tool?

Sebagai developer, seringkali kita melakukan tugas yang berulang seperti membuat struktur folder proyek baru atau menyiapkan utility yang sering dipakai. Dengan CLI tool, tugas-tugas ini bisa diotomatisasi dan dijalankan hanya dengan satu command.[^1][^2][^3]

## Pengenalan Dependencies

Sebelum memulai, mari kita pahami dulu library yang akan digunakan dan fungsinya masing-masing:

### Dependencies Utama

**1. Typer[all] (≥0.12.0)**

Library ini adalah fondasi untuk membuat CLI application. Typer menggunakan Python type hints untuk membuat CLI yang intuitif dengan fitur:[^2][^3]

- Automatic help generation (`--help`)
- Command dan subcommand organization
- Rich output dengan warna dan formatting
- Type validation otomatis[^4][^2]

**2. InquirerPy (≥0.3.4)**

Library untuk membuat interactive prompts di terminal. Berguna untuk:[^5][^6]

- Meminta input dari user dengan interface yang cantik
- Konfirmasi (yes/no questions)
- Select dari list pilihan
- Multi-select checkboxes[^7][^5]

**3. Jinja2 (≥3.1.0)**

Template engine untuk generate file dari template. Fitur utama:[^8][^9][^10]

- Variable substitution dengan `{{ variable }}`
- Control structures seperti `{% if %}` dan `{% for %}`
- Template inheritance untuk reusability[^11][^8]

**4. Pydantic (≥2.0.0)**

Library untuk data validation dan parsing. Digunakan untuk:[^12]

- Type validation otomatis
- Data parsing yang aman
- Model definitions yang jelas[^13][^14]

**5. Pydantic-Settings (≥2.0.0)**

Extension dari Pydantic untuk configuration management. Memudahkan:[^15][^14][^13]

- Load config dari environment variables
- Parse `.env` files
- Type-safe configuration[^16][^17]


### Dev Dependencies (Optional)

Development tools untuk quality assurance:[^18]

- **pytest** - Testing framework
- **pytest-cov** - Code coverage reporting
- **black** - Auto code formatter
- **ruff** - Fast Python linter
- **mypy** - Static type checker


## Persiapan Lingkungan

### Langkah 1: Install UV

UV adalah package manager modern untuk Python yang sangat cepat dan efficient. Install UV sesuai sistem operasi Anda:[^1][^19][^20]

**Linux/macOS:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Verifikasi instalasi:**

```bash
uv --version
```


### Langkah 2: Membuat Proyek Baru

Buat proyek dengan struktur package menggunakan flag `--package`:[^21][^22]

```bash
uv init --package zul
cd zul
```

Command ini akan membuat struktur dasar:

```
zul/
├── pyproject.toml
├── README.md
├── .python-version
└── src/
    └── zul/
        └── __init__.py
```

Flag `--package` penting karena membuat proyek Anda installable dan memungkinkan pembuatan CLI entry point.[^22][^23][^21]

### Langkah 3: Menambahkan Dependencies

Gunakan `uv add` untuk menambahkan dependencies:[^18][^24]

```bash
# Dependencies utama
uv add "typer[all]>=0.12.0"
uv add "inquirerpy>=0.3.4"
uv add "jinja2>=3.1.0"
uv add "pydantic>=2.0.0"
uv add "pydantic-settings>=2.0.0"

# Dev dependencies
uv add --dev "pytest>=7.0.0"
uv add --dev "pytest-cov>=4.0.0"
uv add --dev "black>=23.0.0"
uv add --dev "ruff>=0.1.0"
uv add --dev "mypy>=1.0.0"
```

UV akan otomatis mengupdate `pyproject.toml` dan membuat `uv.lock` file untuk reproducible builds.[^1][^20][^18]

### Langkah 4: Membuat Struktur Folder

Buat folder untuk organize kode Anda:[^12][^25][^26]

```bash
# Buat folder commands
mkdir src/zul/commands
touch src/zul/commands/__init__.py
touch src/zul/commands/build.py
touch src/zul/commands/install.py

# Buat folder utilities
mkdir src/zul/utilities
touch src/zul/utilities/__init__.py
touch src/zul/utilities/milvus_helper.py

# Buat folder templates
mkdir -p src/zul/templates/web
```

**Penjelasan struktur:**

- `commands/` - Berisi implementasi setiap CLI command
- `utilities/` - Berisi helper modules yang bisa diimport
- `templates/` - Berisi template Jinja2 untuk generate files[^8][^27]

Struktur akhir proyek:

```
zul/
├── pyproject.toml
├── README.md
├── .python-version
├── src/
│   └── zul/
│       ├── __init__.py
│       ├── cli.py
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── build.py
│       │   └── install.py
│       ├── templates/
│       │   └── web/
│       │       ├── main.py
│       │       ├── requirements.txt
│       │       └── README.md
│       └── utilities/
│           ├── __init__.py
│           └── milvus_helper.py
└── tests/
    └── __init__.py
```


## Konfigurasi Entry Point

### Langkah 5: Edit pyproject.toml

File `pyproject.toml` adalah jantung dari proyek Python modern. Edit file ini untuk menambahkan CLI entry point:[^28][^29][^30][^31][^32][^33]

```toml
[project]
name = "zul"
version = "0.1.0"
description = "CLI tool untuk membuat template proyek dan utilities"
readme = "README.md"
requires-python = ">=3.8"
dependencies = [
    "typer[all]>=0.12.0",
    "inquirerpy>=0.3.4",
    "jinja2>=3.1.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
]

[project.scripts]
zul = "zul.cli:app"  # <-- INI BAGIAN PENTING!

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build_meta"
```

**Penjelasan penting:**

**`[project.scripts]`** - Bagian ini mendefinisikan entry point CLI:[^29][^30][^31][^32]

- `zul` adalah nama command yang akan dipanggil di terminal
- `"zul.cli:app"` artinya: dari module `zul.cli`, jalankan object `app`
- Syntax: `command_name = "package.module:function"`[^31][^34]

**`[build-system]`** - Menentukan build backend:[^32][^21]

- `hatchling` adalah build tool yang ringan dan cepat
- Alternatif: `setuptools`, `flit`, `poetry`[^29][^32]


## Implementasi Kode

### Langkah 6A: Membuat CLI Entry Point

Buat file `src/zul/cli.py` sebagai main entry point:[^2][^3][^4]

```python
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
```

**Penjelasan kode:**

1. **`typer.Typer()`** - Membuat aplikasi CLI utama[^4][^2]
2. **`app.add_typer()`** - Menambahkan subcommand group[^3][^35]
3. **`@app.command()`** - Decorator untuk mendefinisikan command[^36][^4]
4. **`typer.echo()`** - Print output (lebih baik dari `print()` untuk CLI)[^2][^3]

### Langkah 6B: Implementasi Command Build

Buat file `src/zul/commands/__init__.py`:

```python
"""
Commands package
"""
```

Buat file `src/zul/commands/build.py`:[^2][^3][^5]

```python
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

```

python main.py

```

## Struktur Proyek

```

{{ project_name }}/
├── main.py
├── README.md
└── requirements.txt

```
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
```

**Penjelasan kode detail:**

1. **`typer.Option()`** - Mendefinisikan CLI option dengan default None[^4][^36]
2. **`inquirer.text()`** - Membuat interactive text input[^5][^6][^7]
3. **`inquirer.confirm()`** - Membuat yes/no prompt[^6][^5]
4. **`Path()`** - Object oriented file path handling[^12]
5. **`Template().render()`** - Jinja2 rendering template dengan context[^8][^9][^10]
6. **`typer.Exit()`** - Exit dengan error code[^3][^2]

### Langkah 6C: Implementasi Command Install

Buat file `src/zul/commands/install.py`:

```python
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
```


### Langkah 6D: Membuat Utility Module

Buat file `src/zul/utilities/__init__.py`:

```python
"""
Utilities package
"""
```

Buat file `src/zul/utilities/milvus_helper.py`:

```python
"""
Milvus Helper Utility
Module ini bisa di-extend sesuai kebutuhan
"""

class Milvus:
    """
    Helper class untuk bekerja dengan Milvus vector database
    
    Contoh:
        >>> from zul.utilities.milvus_helper import Milvus
        >>> client = Milvus(host="localhost", port=19530)
        >>> client.connect()
    """
    
    def __init__(self, host: str = "localhost", port: int = 19530):
        """
        Initialize Milvus client
        
        Args:
            host: Milvus server host
            port: Milvus server port
        """
        self.host = host
        self.port = port
        self._connected = False
        
    def connect(self):
        """Connect ke Milvus server"""
        print(f"Connecting to Milvus at {self.host}:{self.port}")
        self._connected = True
        print("✅ Connected successfully!")
        
    def disconnect(self):
        """Disconnect dari Milvus server"""
        if self._connected:
            print("Disconnecting from Milvus...")
            self._connected = False
            print("✅ Disconnected successfully!")
        else:
            print("⚠️  Already disconnected")
    
    def is_connected(self) -> bool:
        """Check connection status"""
        return self._connected
```

**Catatan:** Ini adalah placeholder implementation. Anda bisa mengembangkannya dengan fungsi-fungsi yang Anda butuhkan.[^12][^25]

### Langkah 6E: Update __init__.py Utama

Edit file `src/zul/__init__.py`:

```python
"""
Zul - CLI tool untuk membuat template proyek dan utilities
"""
__version__ = "0.1.0"

# Export utilities agar bisa diimport langsung
from zul.utilities import milvus_helper

__all__ = ["milvus_helper"]
```


## Testing dan Development

### Langkah 7: Testing Lokal

Ada dua cara untuk test CLI tool Anda:[^21][^22][^24]

**Cara 1: Menggunakan `uv run` (Recommended untuk development)**

```bash
# Lihat help
uv run zul --help

# Test command version
uv run zul version

# Test build web command (interactive)
uv run zul build web

# Test build web dengan option
uv run zul build web --name test-project

# Test install command
uv run zul install milvus_helper
```

**Cara 2: Install dalam mode editable**

```bash
# Install proyek dalam mode development
uv pip install -e .

# Sekarang bisa langsung panggil 'zul'
zul --help
zul version
zul build web
```

Mode editable (`-e`) memungkinkan Anda mengedit kode dan perubahan langsung terlihat tanpa perlu reinstall.[^22][^23][^37]

### Contoh Output Expected

Ketika menjalankan `zul build web`:

```
? Masukkan nama proyek: my-awesome-project
? Buat proyek 'my-awesome-project'? Yes
✅ Proyek 'my-awesome-project' berhasil dibuat!
📁 Lokasi: /home/user/projects/my-awesome-project

📝 File yang dibuat:
  - my-awesome-project/main.py
  - my-awesome-project/README.md
  - my-awesome-project/requirements.txt
```


### Testing dengan Python Script

Anda juga bisa test utility module dengan membuat file test Python:

```python
# test_utilities.py
from zul.utilities.milvus_helper import Milvus

def test_milvus_connection():
    client = Milvus(host="localhost", port=19530)
    client.connect()
    assert client.is_connected() == True
    client.disconnect()
    assert client.is_connected() == False
    print("✅ All tests passed!")

if __name__ == "__main__":
    test_milvus_connection()
```

Jalankan:

```bash
uv run python test_utilities.py
```


## Build dan Deployment

### Langkah 8: Build Package (Opsional)

Jika ingin membuat distribusi package yang bisa di-share:[^20][^33][^21]

```bash
# Build package
uv build

# Output akan berada di folder dist/
# - dist/zul-0.1.0-py3-none-any.whl (wheel file)
# - dist/zul-0.1.0.tar.gz (source distribution)
```

File ini bisa diupload ke PyPI atau private package registry.[^23][^38]

### Langkah 9: Install Secara Global (Opsional)

**Install dengan pip:**

```bash
pip install .
```

**Install dengan uv tool (Recommended):**

```bash
uv tool install .
```

Setelah install global, command `zul` bisa dipanggil dari direktori mana saja:[^22][^38][^37]

```bash
cd ~/Documents
zul build web --name new-project
```


## Pengembangan Lanjutan

### Menambahkan Command Baru

Contoh menambahkan command `zul build fastapi`:[^2][^3]

1. **Edit `src/zul/commands/build.py`:**
```python
@app.command()
def fastapi(
    name: str = typer.Option(None, "--name", "-n")
):
    """Membuat template proyek FastAPI"""
    if not name:
        name = inquirer.text(
            message="Nama proyek FastAPI:",
            default="my-fastapi-app"
        ).execute()
    
    project_dir = Path(name)
    project_dir.mkdir(parents=True, exist_ok=False)
    
    # Template untuk FastAPI
    fastapi_template = """from fastapi import FastAPI

app = FastAPI(title="{{ project_name }}")

@app.get("/")
async def root():
    return {"message": "Hello from {{ project_name }}!"}
"""
    
    context = {"project_name": name}
    (project_dir / "main.py").write_text(
        Template(fastapi_template).render(context)
    )
    (project_dir / "requirements.txt").write_text(
        "fastapi>=0.104.0\nuvicorn>=0.24.0\n"
    )
    
    typer.echo(f"✅ FastAPI project '{name}' created!")
```

2. **Test:**
```bash
uv run zul build fastapi --name my-api
```


### Menggunakan Template Files

Untuk template yang lebih kompleks, gunakan file terpisah:[^8][^27][^39]

1. **Buat template file `src/zul/templates/web/app.py.j2`:**
```python
"""
{{ project_name }}
Created with zul CLI tool
"""
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class {{ project_name.replace('-', '_').title() }}:
    """Main application class"""
    
    def __init__(self):
        self.name = "{{ project_name }}"
        logger.info(f"Initialized {self.name}")
    
    def run(self):
        """Run the application"""
        logger.info("Application is running...")

if __name__ == "__main__":
    app = {{ project_name.replace('-', '_').title() }}()
    app.run()
```

2. **Load template dari file:**
```python
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

def create_from_template(project_name: str):
    # Get templates directory
    templates_dir = Path(__file__).parent.parent / "templates" / "web"
    
    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader(templates_dir))
    
    # Load template
    template = env.get_template("app.py.j2")
    
    # Render with context
    content = template.render(project_name=project_name)
    
    # Write to file
    output_file = Path(project_name) / "app.py"
    output_file.write_text(content)
```


### Menambahkan Konfigurasi dengan Pydantic Settings

Buat file `src/zul/config.py`:[^13][^14][^16][^17]

```python
"""
Configuration management dengan Pydantic Settings
"""
from pydantic_settings import BaseSettings
from pydantic import Field

class ZulSettings(BaseSettings):
    """
    Settings untuk Zul CLI tool
    Bisa dikonfigurasi via environment variables atau .env file
    """
    
    # Default template directory
    templates_dir: str = Field(
        default="~/.zul/templates",
        description="Directory untuk custom templates"
    )
    
    # Default project author
    author: str = Field(
        default="Your Name",
        env="ZUL_AUTHOR"
    )
    
    # Default license
    license: str = Field(
        default="MIT",
        env="ZUL_LICENSE"
    )
    
    # Debug mode
    debug: bool = Field(
        default=False,
        env="ZUL_DEBUG"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Singleton instance
settings = ZulSettings()
```

Gunakan dalam command:

```python
from zul.config import settings

@app.command()
def web(name: str = None):
    if not name:
        name = inquirer.text(
            message="Project name:",
            default="my-project"
        ).execute()
    
    context = {
        "project_name": name,
        "author": settings.author,
        "license": settings.license
    }
    # ... rest of the code
```

User bisa set environment variable:

```bash
export ZUL_AUTHOR="John Doe"
export ZUL_LICENSE="Apache-2.0"
zul build web
```


## Tips dan Best Practices

### 1. Error Handling

Tambahkan proper error handling:[^2][^3]

```python
import typer
from pathlib import Path

@app.command()
def web(name: str = None):
    try:
        if not name:
            name = inquirer.text(message="Project name:").execute()
        
        project_dir = Path(name)
        
        if project_dir.exists():
            typer.secho(
                f"❌ Error: Directory '{name}' already exists!",
                fg=typer.colors.RED,
                err=True
            )
            raise typer.Exit(code=1)
        
        project_dir.mkdir(parents=True)
        # ... create files
        
    except KeyboardInterrupt:
        typer.echo("\n⚠️  Cancelled by user")
        raise typer.Exit(code=130)
    except Exception as e:
        typer.secho(
            f"❌ Unexpected error: {e}",
            fg=typer.colors.RED,
            err=True
        )
        raise typer.Exit(code=1)
```


### 2. Progress Indicators

Gunakan progress bars untuk operasi yang lama:[^2]

```python
import time
import typer

@app.command()
def build(name: str):
    with typer.progressbar(
        length=100,
        label="Creating project"
    ) as progress:
        # Simulate tasks
        for i in range(100):
            time.sleep(0.01)
            progress.update(1)
    
    typer.echo("✅ Project created!")
```


### 3. Colored Output

Gunakan warna untuk output yang lebih informatif:[^2][^3]

```python
# Success message
typer.secho("✅ Success!", fg=typer.colors.GREEN)

# Warning
typer.secho("⚠️  Warning!", fg=typer.colors.YELLOW)

# Error
typer.secho("❌ Error!", fg=typer.colors.RED, err=True)

# Info
typer.secho("ℹ️  Info", fg=typer.colors.BLUE)
```


### 4. Validation Input

Validate user input dengan callback:[^3][^4]

```python
def validate_project_name(value: str) -> str:
    """Validate project name"""
    if not value:
        raise typer.BadParameter("Project name cannot be empty")
    
    if not value.replace('-', '').replace('_', '').isalnum():
        raise typer.BadParameter(
            "Project name can only contain letters, numbers, '-' and '_'"
        )
    
    return value

@app.command()
def web(
    name: str = typer.Option(
        ...,
        callback=validate_project_name,
        help="Project name"
    )
):
    # name sudah tervalidasi
    pass
```


### 5. Documentation

Tambahkan docstring yang jelas:[^3]

```python
@app.command()
def web(
    name: str = typer.Option(None, "--name", "-n"),
    author: str = typer.Option("", "--author", "-a"),
    license: str = typer.Option("MIT", "--license", "-l")
):
    """
    Membuat template proyek web baru.
    
    Command ini akan:
    1. Membuat direktori proyek
    2. Generate file main.py dari template
    3. Generate README.md dengan metadata
    4. Membuat requirements.txt
    
    Contoh penggunaan:
        $ zul build web --name my-project --author "John Doe"
        $ zul build web  # Interactive mode
    """
    pass
```


## Troubleshooting

### Problem: Command tidak ditemukan setelah install

**Solusi:**

```bash
# Pastikan PATH sudah benar
which zul

# Reinstall dengan uv tool
uv tool uninstall zul
uv tool install .

# Atau update shell config
source ~/.bashrc  # atau ~/.zshrc
```


### Problem: Import error untuk utilities

**Solusi:**

```python
# Pastikan __init__.py ada di setiap folder
# Dan import path benar
from zul.utilities.milvus_helper import Milvus  # ✅ Correct
from utilities.milvus_helper import Milvus       # ❌ Wrong
```


### Problem: Template tidak ditemukan

**Solusi:**

```python
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Get absolute path to templates
template_dir = Path(__file__).parent.parent / "templates"
env = Environment(loader=FileSystemLoader(str(template_dir)))
```


## Kesimpulan

Anda telah berhasil membuat CLI tool "zul" yang lengkap dengan fitur:

1. ✅ **Command system** dengan Typer untuk organized CLI commands[^2][^3]
2. ✅ **Interactive prompts** dengan InquirerPy untuk UX yang baik[^5][^6]
3. ✅ **Template generation** dengan Jinja2 untuk generate project files[^8][^9]
4. ✅ **Utility modules** yang bisa diimport dalam kode Python
5. ✅ **Modern tooling** dengan UV untuk fast dependency management[^1][^19][^20]
6. ✅ **Type safety** dengan Pydantic untuk configuration[^13][^14]

CLI tool ini bisa terus dikembangkan dengan menambahkan:

- Template untuk berbagai jenis proyek (FastAPI, Django, Flask, dll)
- More utility helpers (database, file processing, API clients)
- Configuration management dengan .env files[^14][^16]
- Testing suite dengan pytest[^3]
- Publishing ke PyPI untuk sharing dengan komunitas[^23][^38]

Dengan mengikuti tutorial ini step-by-step, Anda sekarang memiliki foundation yang solid untuk membuat CLI tools Python yang professional dan maintainable. Happy coding! 🚀
<span style="display:none">[^40][^41][^42][^43][^44][^45][^46][^47][^48][^49][^50][^51][^52][^53][^54][^55][^56][^57][^58][^59][^60][^61][^62][^63][^64][^65][^66][^67][^68][^69][^70][^71][^72][^73][^74][^75]</span>

<div align="center">⁂</div>

[^1]: https://www.saaspegasus.com/guides/uv-deep-dive/

[^2]: https://typer.tiangolo.com

[^3]: https://realpython.com/python-typer-cli/

[^4]: https://typer.tiangolo.com/tutorial/first-steps/

[^5]: https://inquirerpy.readthedocs.io/en/latest/pages/prompts/input.html

[^6]: https://inquirerpy.readthedocs.io

[^7]: https://github.com/kazhala/InquirerPy

[^8]: https://pythonadventures.wordpress.com/2014/02/25/jinja2-example-for-generating-a-local-file-using-a-template/

[^9]: https://www.geeksforgeeks.org/python/how-to-use-jinja-for-document-generation/

[^10]: https://realpython.com/primer-on-jinja-templating/

[^11]: https://jinja.palletsprojects.com/en/stable/templates/

[^12]: https://realpython.com/python-script-structure/

[^13]: https://docs.pydantic.dev/1.10/usage/settings/

[^14]: https://python.plainenglish.io/get-your-python-configurations-right-every-time-with-pydantic-settings-441d8a46c832

[^15]: https://field-idempotency--pydantic-docs.netlify.app/usage/settings/

[^16]: https://proudlynerd.vidiemme.it/mastering-python-project-configuration-with-pydantic-f924a0803dd4

[^17]: https://fastapi.tiangolo.com/fa/advanced/settings/

[^18]: https://www.datacamp.com/tutorial/python-uv

[^19]: https://www.pythoncheatsheet.org/blog/python-uv-package-manager

[^20]: https://realpython.com/python-uv/

[^21]: https://docs.astral.sh/uv/concepts/projects/init/

[^22]: https://mathspp.com/blog/using-uv-to-build-and-install-python-cli-apps

[^23]: https://pybit.es/articles/how-to-package-and-deploy-cli-apps/

[^24]: https://docs.astral.sh/uv/guides/projects/

[^25]: https://www.reddit.com/r/Python/comments/1krsxut/modern_python_boilerplate_good_package_basic/

[^26]: https://dagster.io/blog/python-project-best-practices

[^27]: https://www.asyncapi.com/docs/tools/generator/generator-template

[^28]: https://stackoverflow.com/questions/18787036/difference-between-entry-points-console-scripts-and-scripts-in-setup-py

[^29]: https://stackoverflow.com/questions/63326840/specifying-command-line-scripts-in-pyproject-toml

[^30]: https://xebia.com/blog/an-updated-guide-to-setuptools-and-pyproject-toml/

[^31]: https://setuptools.pypa.io/en/latest/userguide/entry_point.html

[^32]: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/

[^33]: https://til.simonwillison.net/python/pyproject

[^34]: http://python-packaging.readthedocs.io/en/latest/command-line-scripts.html

[^35]: https://www.youtube.com/watch?v=w7M5QzE_8u0

[^36]: https://typer.tiangolo.com/tutorial/

[^37]: https://til.simonwillison.net/python/uv-cli-apps

[^38]: https://thisdavej.com/packaging-python-command-line-apps-the-modern-way-with-uv/

[^39]: https://trustedfirmware-m.readthedocs.io/en/latest/design_docs/software/tfm_code_generation_with_jinja2.html

[^40]: https://gist.github.com/ericmjl/27e50331f24db3e8f957d1fe7bbbe510

[^41]: https://docs.astral.sh/uv/getting-started/first-steps/

[^42]: https://www.youtube.com/watch?v=8-i3U_3Gxko

[^43]: https://stackoverflow.com/questions/193161/what-is-the-best-project-structure-for-a-python-application

[^44]: https://www.youtube.com/watch?v=AMdG7IjgSPM

[^45]: https://docs.python-guide.org/writing/structure/

[^46]: https://docs.astral.sh/uv/guides/install-python/

[^47]: https://www.geeksforgeeks.org/python/python-typer-module/

[^48]: https://stackoverflow.com/questions/75537421/using-main-py-as-entry-point-of-python-module

[^49]: https://discuss.python.org/t/python-cli-entry-point-doesnt-work-as-expected/5952

[^50]: https://docs.python.org/3/library/__main__.html

[^51]: https://www.reddit.com/r/learnpython/comments/1k3js3d/what_are_projectscripts_in_pyprojecttoml/

[^52]: https://www.geeksforgeeks.org/python/usage-of-__main__-py-in-python/

[^53]: https://www.reddit.com/r/learnpython/comments/azxgkn/eli5_how_to_structure_a_python_project/

[^54]: https://github.com/bazelbuild/rules_python/issues/318

[^55]: https://discuss.python.org/t/why-do-script-entrypoints-require-a-function-be-specified/14090

[^56]: https://discuss.python.org/t/whats-the-status-of-scripts-vs-entry-points/18524

[^57]: https://devsjc.github.io/blog/20240627-the-complete-guide-to-pyproject-toml/

[^58]: https://blog.claude.nl/posts/how-to-structure-a-python-project-with-multiple-entry-points/

[^59]: https://packaging.python.org/specifications/entry-points/

[^60]: https://python-poetry.org/docs/pyproject/

[^61]: https://www.reddit.com/r/Python/comments/1b4qwds/an_extremely_modern_and_configurable_python/

[^62]: https://pydigger.com/pypi/InquirerPy

[^63]: https://github.com/AnthonyBloomer/python-cli-template

[^64]: https://github.com/pyscaffold/pyscaffold

[^65]: https://inquirerpy.readthedocs.io/en/latest/pages/inquirer.html

[^66]: https://www.youtube.com/watch?v=OraYXEr0Irg

[^67]: https://simonwillison.net/2023/Sep/30/cli-tools-python/

[^68]: https://www.reddit.com/r/programming/comments/kz3uy4/inquirerpy_python_port_of_inquirerjs_a_collection/

[^69]: https://discuss.python.org/t/creating-project-files-from-a-packages-command-line-interface/71212

[^70]: https://github.com/CITGuru/PyInquirer

[^71]: https://www.reddit.com/r/learnpython/comments/yfigfy/generating_pdf_from_some_sort_of_template_jinja2/

[^72]: https://themeselection.com/python-cli-library/

[^73]: https://stackoverflow.com/questions/7898049/boilerplate-code-in-python

[^74]: https://docs.pydantic.dev/latest/concepts/pydantic_settings/

[^75]: https://blog.stephenturner.us/p/python-cli-click-cookiecutter

