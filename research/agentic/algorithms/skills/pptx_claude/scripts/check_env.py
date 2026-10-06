"""Check that this machine can run the pptx-claude skill.

    python scripts/check_env.py            # human-readable report
    python scripts/check_env.py --build    # also build assets/examples/minimal_deck.json

Exit code 0 = ready (icons may still be disabled), 1 = not ready.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import create_pptx as engine  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--build", action="store_true", help="Build a 4-slide test deck as the final check")
    args = ap.parse_args()
    ok = True

    print(f"[ok]   Python {sys.version.split()[0]}")
    if sys.version_info < (3, 9):
        print("[FAIL] Python 3.9 or newer is required")
        ok = False

    if engine._node_ok():
        ver = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip()
        print(f"[ok]   Node.js {ver}")
    else:
        print("[FAIL] Node.js not found on PATH -> install Node 18+ from https://nodejs.org")
        print("\nNOT READY")
        return 1

    node_dir = engine._find_node_dir()
    if engine._pptxgenjs_ok(node_dir):
        print(f"[ok]   pptxgenjs found ({node_dir or 'global / NODE_PATH'})")
    else:
        print("[FAIL] pptxgenjs not found")
        print("       " + engine.INSTALL_HINT.replace("\n", "\n       "))
        ok = False

    if ok and engine._icons_ok(node_dir):
        print("[ok]   icon packages found (react, react-dom, react-icons, sharp)")
    elif ok:
        print("[warn] icon packages missing -> decks still build, but WITHOUT icons")
        print(f"       fix: cd \"{engine.SKILL_DIR}\" && npm install")

    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    print(f"[{'ok' if soffice else 'info'}]   LibreOffice {'found' if soffice else 'not found'}"
          " (optional, only for scripts/render_preview.py)")

    if ok and args.build:
        spec = engine.SKILL_DIR / "assets" / "examples" / "minimal_deck.json"
        with tempfile.TemporaryDirectory() as tmp:
            res = engine.create_pptx(spec.read_text(encoding="utf-8"), "check_env_test.pptx", output_dir=tmp)
            if res["ok"]:
                print(f"[ok]   test deck built ({res['slides']} slides)")
            else:
                print(f"[FAIL] test build failed: {res['error']}")
                ok = False

    print("\nREADY" if ok else "\nNOT READY")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
