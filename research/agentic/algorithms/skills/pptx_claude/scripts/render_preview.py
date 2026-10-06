"""Render a .pptx to PNG images so the result can be checked visually.

OPTIONAL - only needed for visual QA.  Requires LibreOffice (`soffice`) and
either `pdftoppm` (poppler) or the Python package `pymupdf`.

    python scripts/render_preview.py deck.pptx              # -> deck_preview/slide-01.png ...
    python scripts/render_preview.py deck.pptx --grid       # + deck_preview/grid.png (needs Pillow)

Exit code 0 on success, 1 on failure (message on stdout).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _find_soffice() -> str | None:
    for name in ("soffice", "libreoffice"):
        exe = shutil.which(name)
        if exe:
            return exe
    for cand in (
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ):
        if Path(cand).is_file():
            return cand
    return None


def pptx_to_pdf(pptx: Path, out_dir: Path) -> Path:
    soffice = _find_soffice()
    if not soffice:
        raise RuntimeError("LibreOffice not found - install it or open the .pptx manually.")
    with tempfile.TemporaryDirectory() as profile:  # private profile: safe to run in parallel
        subprocess.run(
            [soffice, f"-env:UserInstallation={Path(profile).as_uri()}", "--headless",
             "--convert-to", "pdf", "--outdir", str(out_dir), str(pptx)],
            capture_output=True, timeout=300, check=True,
        )
    pdf = out_dir / (pptx.stem + ".pdf")
    if not pdf.is_file():
        raise RuntimeError("LibreOffice did not produce a PDF.")
    return pdf


def pdf_to_pngs(pdf: Path, out_dir: Path, dpi: int) -> list[Path]:
    if shutil.which("pdftoppm"):
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(out_dir / "slide")],
                       capture_output=True, timeout=300, check=True)
        return sorted(out_dir.glob("slide-*.png"))
    try:
        import fitz  # pymupdf
    except ImportError as e:
        raise RuntimeError("Need `pdftoppm` (poppler) or `pip install pymupdf` to make PNGs. "
                           f"The PDF is here: {pdf}") from e
    out = []
    with fitz.open(pdf) as doc:
        for i, page in enumerate(doc, 1):
            path = out_dir / f"slide-{i:02d}.png"
            page.get_pixmap(dpi=dpi).save(path)
            out.append(path)
    return out


def make_grid(pngs: list[Path], out: Path, cols: int = 4, thumb_w: int = 480) -> Path:
    from PIL import Image  # optional
    thumbs = []
    for p in pngs:
        im = Image.open(p).convert("RGB")
        thumbs.append(im.resize((thumb_w, round(im.height * thumb_w / im.width))))
    th = max(t.height for t in thumbs)
    rows = -(-len(thumbs) // cols)
    pad = 12
    sheet = Image.new("RGB", (cols * (thumb_w + pad) + pad, rows * (th + pad) + pad), "white")
    for i, t in enumerate(thumbs):
        sheet.paste(t, (pad + (i % cols) * (thumb_w + pad), pad + (i // cols) * (th + pad)))
    sheet.save(out)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pptx")
    ap.add_argument("-o", "--out-dir", help="Default: <name>_preview next to the file")
    ap.add_argument("--dpi", type=int, default=60)
    ap.add_argument("--grid", action="store_true", help="Also write grid.png with every slide")
    args = ap.parse_args()

    pptx = Path(args.pptx).resolve()
    if not pptx.is_file():
        print(f"ERROR: file not found: {pptx}")
        return 1
    out_dir = Path(args.out_dir) if args.out_dir else pptx.with_name(pptx.stem + "_preview")
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        pdf = pptx_to_pdf(pptx, out_dir)
        pngs = pdf_to_pngs(pdf, out_dir, args.dpi)
        print(f"OK: {len(pngs)} slide images in {out_dir}")
        if args.grid:
            print(f"OK: grid {make_grid(pngs, out_dir / 'grid.png')}")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {e.cmd[0]} failed: {(e.stderr or b'').decode(errors='replace')[-400:]}")
    except Exception as e:
        print(f"ERROR: {e}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
