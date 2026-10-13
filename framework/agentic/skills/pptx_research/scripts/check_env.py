"""Check that this machine can run the pptx-research skill.

    python scripts/check_env.py            # report
    python scripts/check_env.py --build    # also build assets/examples/research_proposal.json

Exit code 0 = ready, 1 = not ready.
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
    ok = True
    print(f"[ok]   Python {sys.version.split()[0]}" if sys.version_info >= (3, 9)
          else f"[FAIL] Python {sys.version.split()[0]} - 3.9 or newer is required")
    ok &= sys.version_info >= (3, 9)
    try:
        import pptx
        print(f"[ok]   python-pptx {pptx.__version__}")
    except ImportError:
        print("[FAIL] python-pptx missing -> pip install python-pptx")
        ok = False
    try:
        import PIL
        print(f"[ok]   Pillow {PIL.__version__}")
    except ImportError:
        print("[FAIL] Pillow missing -> pip install pillow")
        ok = False

    import build_deck as engine
    tpl = engine.DEFAULT_TEMPLATE
    if tpl.is_file():
        try:
            from pptx import Presentation
            n = len(Presentation(str(tpl)).slides)
            good = n == 15
            print(f"[{'ok' if good else 'FAIL'}]   template {tpl.name}: {n} slides, {tpl.stat().st_size / 1e6:.1f} MB"
                  + ("" if good else " (15 expected - see references/template_setup.md)"))
            ok &= good
        except Exception as e:
            print(f"[FAIL] template cannot be opened: {e}")
            ok = False
    else:
        print(f"[FAIL] template missing: {tpl}\n       see references/template_setup.md")
        ok = False
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    print(f"[{'ok' if soffice else 'info'}]   LibreOffice {'found' if soffice else 'not found'} "
          "(optional, only for scripts/render_preview.py)")

    if ok and args.build:
        spec = engine.SKILL_DIR / "assets" / "examples" / "research_proposal.json"
        with tempfile.TemporaryDirectory() as tmp:
            res = engine.build_deck(spec.read_text(encoding="utf-8"), "check.pptx", output_dir=tmp,
                                    image_dirs=[spec.parent])
            print(f"[ok]   test deck built ({res['slides']} slides)" if res["ok"]
                  else f"[FAIL] test build failed: {res['error']}")
            ok &= bool(res["ok"])
    print("\nREADY" if ok else "\nNOT READY")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
