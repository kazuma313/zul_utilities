"""Check that this machine can run the mind-map skill.

    python scripts/check_env.py            # report
    python scripts/check_env.py --build    # also build the example map (SVG, and PNG when a browser exists)
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--build", action="store_true")
    args = ap.parse_args()
    ok = sys.version_info >= (3, 9)
    print(f"[{'ok' if ok else 'FAIL'}]   Python {sys.version.split()[0]}" + ("" if ok else " - 3.9+ required"))
    import build_mindmap as engine
    from render_svg import FONT_DIR
    fonts = sorted(FONT_DIR.glob("poppins-*.woff2"))
    print(f"[{'ok' if fonts else 'warn'}]   {len(fonts)} bundled font files (embedded in SVG/HTML)")
    b = engine.find_browser()
    if b:
        print(f"[ok]   browser for PNG/PDF: {b}")
    else:
        try:
            import cairosvg  # noqa: F401
            print("[ok]   cairosvg found for PNG/PDF (no browser needed)")
        except ImportError:
            print("[warn] no browser and no cairosvg -> SVG/HTML/MD only. Install Edge/Chrome, `pip install cairosvg`, "
                  "or set POSTER_BROWSER=<path to chrome.exe>")
    print(f"[{'ok' if shutil.which('pdftotext') else 'info'}]   pdftotext {'found' if shutil.which('pdftotext') else 'not found'}"
          " (PDF sources; alternative: pip install pypdf)")
    try:
        import PIL  # noqa: F401
        print("[ok]   Pillow (PNG cropping)")
    except ImportError:
        print("[info] Pillow not installed - PNGs may carry a white margin at the bottom")
    if ok and args.build:
        spec = engine.SKILL_DIR / "assets" / "examples" / "fotosintesis.md"
        with tempfile.TemporaryDirectory() as tmp:
            res = engine.build_mindmap(spec.read_text(encoding="utf-8"), "check.png", output_dir=tmp, also=["svg", "md"])
            print(f"[ok]   example built: {', '.join(res['files'])}" if res["ok"] else f"[FAIL] {res['error']}")
            ok &= bool(res["ok"])
    print("\nREADY" if ok else "\nNOT READY")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
