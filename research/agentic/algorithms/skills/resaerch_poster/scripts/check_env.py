"""Check that this machine can run the research-poster skill.

    python scripts/check_env.py            # report
    python scripts/check_env.py --build    # also build the example poster

Exit code 0 = ready (HTML at least), 1 = not ready.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--build", action="store_true")
    args = ap.parse_args()
    ok = sys.version_info >= (3, 9)
    print(f"[{'ok' if ok else 'FAIL'}]   Python {sys.version.split()[0]}" + ("" if ok else " - 3.9 or newer is required"))
    try:
        import PIL
        print(f"[ok]   Pillow {PIL.__version__} (images are resized before embedding)")
    except ImportError:
        print("[info] Pillow missing - images are embedded as-is (pip install pillow to shrink them)")
    import build_poster as engine
    fonts = sorted(engine.FONT_DIR.glob("poppins-*.woff2"))
    print(f"[{'ok' if fonts else 'warn'}]   {len(fonts)} bundled font files" + ("" if fonts else " - Poppins missing, Arial will be used"))
    browser = engine.find_browser()
    if browser:
        print(f"[ok]   browser for PDF/PNG: {browser}")
    else:
        print("[warn] no Chromium browser found -> only HTML output. Fix: install Microsoft Edge or Google Chrome,\n"
              "       or `pip install playwright` + `playwright install chromium`, or set POSTER_BROWSER=<path to chrome.exe>")
    if ok and args.build:
        spec = engine.SKILL_DIR / "assets" / "examples" / "consumer_research.json"
        with tempfile.TemporaryDirectory() as tmp:
            res = engine.build_poster(spec.read_text(encoding="utf-8"), "check.pdf", output_dir=tmp, image_dirs=[spec.parent])
            if res["ok"]:
                print(f"[ok]   example built: {', '.join(res['files'])}")
            else:
                print(f"[FAIL] example build failed: {res['error']}")
                ok = False
    print("\nREADY" if ok else "\nNOT READY")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
