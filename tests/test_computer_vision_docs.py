import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "docs" / "assets" / "computer-vision"

# --------------------------------------------------------------------------
# Contoh Di Panduan
# --------------------------------------------------------------------------
#
# Setiap blok `python title="nama.py"` di halaman ini berdiri sendiri
# dengan data buatan, jadi bisa dijalankan apa adanya. Gambar hasil
# contoh juga harus ada di docs/assets, tempat halaman memuatnya.
#

PAGES = [
    "menggambar-di-frame.md",
    "menghitung-dengan-garis-dan-poligon.md",
    "mengukur-durasi.md",
    "membaca-arah-hadap-dan-jarak.md",
    "menghitamkan-dan-menyamarkan-area.md",
]
BLOCK = re.compile(r'^( *)```python title="([^"]+\.py)"\n(.*?)^\1```', re.S | re.M)


def examples():
    for page in PAGES:
        text = (ROOT / "docs" / "panduan" / page).read_text(encoding="utf-8")
        for _, name, code in BLOCK.findall(text):
            yield pytest.param(textwrap.dedent(code), id=f"{page}:{name}")


@pytest.mark.parametrize("code", list(examples()))
def test_docs_example_runs_and_its_image_is_published(code, tmp_path):
    pytest.importorskip("cv2")
    script = tmp_path / "contoh.py"
    script.write_text(code, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(script)], cwd=tmp_path, capture_output=True, text=True
    )

    assert result.returncode == 0, result.stderr[-2000:]
    for image in tmp_path.glob("*.png"):
        assert (ASSETS / image.name).exists(), f"{image.name} belum ada di {ASSETS}"


def test_every_page_has_examples():
    assert len(list(examples())) >= len(PAGES)
