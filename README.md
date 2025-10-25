# 🚀 Zul - Python Project Boilerplate Generator

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![UV](https://img.shields.io/badge/package%20manager-uv-orange)](https://github.com/astral-sh/uv)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Zul adalah CLI tool yang powerful dan mudah digunakan untuk membuat template proyek Python dengan cepat. Tidak perlu lagi membuat folder dan file secara manual - biarkan Zul yang melakukannya untuk Anda!

## ✨ Features

- 🎨 **Interactive Prompts** - Interface yang user-friendly dengan InquirerPy
- 📦 **Project Templates** - Generate struktur proyek web dengan satu command
- 🔧 **Utility Helpers** - Built-in utilities yang bisa langsung diimport (seperti Milvus helper)
- ⚡ **Fast & Modern** - Dibangun dengan UV package manager untuk performa maksimal
- 🎯 **Type-Safe** - Menggunakan Pydantic untuk validation dan settings management
- 📝 **Template Engine** - Powered by Jinja2 untuk customizable file generation

## 📋 Requirements

- Python 3.8 atau lebih tinggi
- UV package manager (atau pip)

## 🚀 Installation

### Option 1: Install dari GitHub (Recommended)

#### Menggunakan pip:

```bash
# Install versi terbaru
pip install git+https://github.com/kazuma313/zul_utilities.git

# Install versi spesifik (tag/branch)
pip install git+https://github.com/kazuma313/zul_utilities.git@v0.1.0
```

#### Menggunakan UV (Recommended):

```bash
# Install sebagai tool global
uv tool install git+https://github.com/kazuma313/zul_utilities.git

# Atau untuk development
git clone https://github.com/kazuma313/zul_utilities.git
cd zul
uv sync
uv pip install -e .
```

### Option 2: Install dari Source

```bash
# Clone repository
git clone https://github.com/kazuma313/zul_utilities.git
cd zul

# Install dengan UV
uv sync
uv pip install -e .

# Atau dengan pip
pip install -e .
```

### Option 3: Add ke requirements.txt

Tambahkan baris ini ke file `requirements.txt` proyek Anda:

```txt
# Install dari GitHub main branch
zul @ git+https://github.com/kazuma313/zul_utilities.git

# Atau install versi spesifik
zul @ git+https://github.com/kazuma313/zul_utilities.git@v0.1.0

# Atau install dari branch tertentu
zul @ git+https://github.com/kazuma313/zul_utilities.git@development
```

Kemudian install:

```bash
pip install -r requirements.txt
```

## 📖 Usage

### Generate Web Project Template

```bash
# Interactive mode - akan menanyakan nama proyek
zul build web

# Atau langsung dengan option
zul build web --name my-awesome-project
```

**Output:**
```
✅ Proyek 'my-awesome-project' berhasil dibuat!
📁 Lokasi: /path/to/my-awesome-project

📝 File yang dibuat:
  - my-awesome-project/main.py
  - my-awesome-project/README.md
  - my-awesome-project/requirements.txt
```

**Struktur project yang dihasilkan:**
```
my-awesome-project/
├── main.py           # Entry point dengan template code
├── README.md         # Project documentation
└── requirements.txt  # Dependencies list
```

### Install Utilities

```bash
# Install milvus_helper utility
zul install milvus_helper
```

Kemudian gunakan di kode Python Anda:

```python
from zul.utilities.milvus_helper import Milvus

# Inisialisasi Milvus client
client = Milvus(host="localhost", port=19530)
client.connect()

# Cek status koneksi
if client.is_connected():
    print("Connected to Milvus!")

# Disconnect
client.disconnect()
```

### Check Version

```bash
zul version
```

### Help & Documentation

```bash
# General help
zul --help

# Help untuk specific command
zul build --help
zul install --help
```

## 🎯 Use Cases

### 1. Rapid Prototyping

Buat proyek baru dengan cepat untuk eksperimen atau proof-of-concept:

```bash
zul build web --name poc-api
cd poc-api
python main.py
```

### 2. Consistent Project Structure

Pastikan semua proyek dalam tim memiliki struktur yang konsisten:

```bash
# Setiap developer menjalankan command yang sama
zul build web --name feature-xyz
```

### 3. Reusable Utilities

Import helper utilities yang sudah Anda buat:

```python
# Di proyek lain, tinggal import
from zul.utilities.milvus_helper import Milvus
from zul.utilities.pdf_converter import convert_md_to_pdf  # Future utility
```

## 🛠️ Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/kazuma313/zul_utilities.git
cd zul

# Install dengan development dependencies
uv sync --all-extras

# Atau dengan pip
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run dengan coverage report
pytest --cov=zul --cov-report=html

# Run specific test file
pytest tests/test_build.py
```

### Code Formatting & Linting

```bash
# Format code dengan Black
black src/

# Lint dengan Ruff
ruff check src/

# Type checking dengan mypy
mypy src/
```

### Project Structure

```
zul/
├── pyproject.toml          # Project configuration
├── README.md               # This file
├── src/
│   └── zul/
│       ├── __init__.py     # Package initialization
│       ├── cli.py          # Main CLI entry point
│       ├── commands/       # CLI commands
│       │   ├── __init__.py
│       │   ├── build.py    # Build command implementation
│       │   └── install.py  # Install command implementation
│       ├── templates/      # Jinja2 templates
│       │   └── web/        # Web project templates
│       └── utilities/      # Helper utilities
│           ├── __init__.py
│           └── milvus_helper.py
└── tests/                  # Test files
    └── __init__.py
```

## 📚 Documentation

### Adding New Templates

Untuk menambahkan template baru (misalnya FastAPI):

1. **Buat command baru di `src/zul/commands/build.py`:**

```python
@app.command()
def fastapi(name: str = typer.Option(None, "--name", "-n")):
    """Generate FastAPI project template"""
    if not name:
        name = inquirer.text(
            message="FastAPI project name:",
            default="my-fastapi-app"
        ).execute()
    
    # Implementation here...
```

2. **Buat template files di `src/zul/templates/fastapi/`**

3. **Test command:**

```bash
uv run zul build fastapi --name test-api
```

### Adding New Utilities

Untuk menambahkan utility baru:

1. **Buat file di `src/zul/utilities/`:**

```python
# src/zul/utilities/pdf_converter.py
def convert_md_to_pdf(input_file: str, output_file: str):
    """Convert Markdown to PDF"""
    # Implementation here...
```

2. **Tambahkan install command di `src/zul/commands/install.py`:**

```python
@app.command()
def pdf_converter():
    """Install PDF converter utility"""
    typer.echo("📦 Installing PDF converter...")
    # Implementation here...
```

3. **Export dari `src/zul/__init__.py`:**

```python
from zul.utilities import milvus_helper, pdf_converter
__all__ = ["milvus_helper", "pdf_converter"]
```

## 🤝 Contributing

Contributions are welcome! Berikut cara contribute:

1. **Fork repository ini**
2. **Buat branch baru** (`git checkout -b feature/amazing-feature`)
3. **Commit changes** (`git commit -m 'Add some amazing feature'`)
4. **Push ke branch** (`git push origin feature/amazing-feature`)
5. **Open Pull Request**

### Contribution Guidelines

- Follow existing code style (Black + Ruff)
- Add tests for new features
- Update documentation
- Keep commits clean and descriptive

## 📋 Roadmap

- [ ] Add FastAPI project template
- [ ] Add Django project template
- [ ] Add Flask project template
- [ ] Add CLI testing framework template
- [ ] Add Docker configuration template
- [ ] Add CI/CD pipeline templates (GitHub Actions, GitLab CI)
- [ ] Add PDF converter utility
- [ ] Add database migration utility
- [ ] Add API client generator utility
- [ ] Interactive template customization
- [ ] Custom template support from external sources
- [ ] Configuration file support (.zulrc)

## 🐛 Known Issues

Belum ada known issues. Jika menemukan bug, silakan [buat issue baru](https://github.com/YOUR_USERNAME/zul/issues).

## 📝 Changelog

### v0.1.0 (2025-10-25)

**Initial Release**

- ✨ Basic CLI framework dengan Typer
- ✨ `zul build web` command untuk generate web project template
- ✨ `zul install milvus_helper` command
- ✨ Interactive prompts dengan InquirerPy
- ✨ Template generation dengan Jinja2
- ✨ Milvus helper utility
- 📚 Comprehensive documentation

## 🔗 Links

- **Documentation:** [GitHub Wiki](https://github.com/YOUR_USERNAME/zul/wiki)
- **Issues:** [GitHub Issues](https://github.com/YOUR_USERNAME/zul/issues)
- **Discussions:** [GitHub Discussions](https://github.com/YOUR_USERNAME/zul/discussions)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Typer](https://typer.tiangolo.com/) - CLI framework
- [InquirerPy](https://inquirerpy.readthedocs.io/) - Interactive prompts
- [Jinja2](https://jinja.palletsprojects.com/) - Template engine
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [UV](https://github.com/astral-sh/uv) - Python package manager

## 👨‍💻 Author

**Your Name**

- GitHub: [@YOUR_USERNAME](https://github.com/YOUR_USERNAME)
- Email: your.email@example.com

## ⭐ Show Your Support

Jika project ini membantu Anda, jangan lupa kasih ⭐️ di GitHub!

---

<p align="center">Made with ❤️ using Python & UV</p>
