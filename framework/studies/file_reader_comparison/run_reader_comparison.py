"""Which model reads pictures best for the learning skills?  Same four images, every reader, one table.

    uv run python framework/studies/file_reader_comparison/run_reader_comparison.py --prepare   # make inputs/
    uv run python framework/studies/file_reader_comparison/run_reader_comparison.py             # run every reader
    uv run python framework/studies/file_reader_comparison/run_reader_comparison.py --score     # score saved outputs

Readers: the skills' own reader (read_material.VisionReader, the prompt follows the model) with
gemma3:4b, qwen3-vl:4b and glm-ocr through Ollama, and Docling's VLM pipeline with gemma3:4b.  Inputs:
a screenshot of mediawiki.org, a survey slide, page 5 of a PDF in research/arsip/catatan_docs/ turned into a picture as if it
were scanned, and a table drawn here.  What each should contain is in inputs/truth.json; outputs/ keeps
every reader's text, results.json the times and scores.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INPUTS, OUTPUTS = HERE / "inputs", HERE / "outputs"
sys.path.insert(0, str(ROOT / "framework" / "agentic" / "skills" / "silabus_belajar" / "scripts"))
import read_material as rm  # noqa: E402

READERS = ["gemma3:4b", "qwen3-vl:4b", "glm-ocr", "docling-vlm:gemma3:4b"]
TABLE = [["Reksa dana", "Jenis", "NAB per unit", "Biaya beli", "Risiko"],
         ["Dana Kas Prima", "Pasar uang", "Rp1.250", "0%", "Rendah"],
         ["Obligasi Nusantara", "Pendapatan tetap", "Rp1.875", "1%", "Sedang"],
         ["Saham Andalas", "Saham", "Rp2.430", "2%", "Tinggi"],
         ["Campuran Sejahtera", "Campuran", "Rp1.610", "1,5%", "Sedang"]]
MEDIAWIKI = ["Users & Developers", "Register for the conference", "registration is now open until October 9",
             "MediaWiki is a collaboration and documentation platform", "vibrant community", "Main Page", "Discussion",
             "Read", "View source", "View history", "tens of thousands of websites",
             "thousands of companies and organisations", "It powers Wikipedia", "Find out more",
             "Set up and run MediaWiki", "Edit and use MediaWiki", "Download, install and configure",
             "Add functionality by installing", "extensions", "Learn how to navigate", "Learn how to edit a page",
             "Learn more about reading, editing", "Photo of participants of the Wikimedia Hackathon 2026",
             "Appearance", "Automatic"]
SLIDE = ["Survei dalam angka", "350", "72%", "310.000", "64%", "Responden dari 500 yang diundang",
         "Belanja online minimal sebulan sekali", "Rata-rata belanja per bulan", "Membayar dengan e-wallet"]


def prepare(screenshot: str | None) -> None:
    from PIL import Image, ImageDraw, ImageFont
    import pypdfium2

    INPUTS.mkdir(exist_ok=True)
    if screenshot:
        shutil.copy(screenshot, INPUTS / "mediawiki.webp")
    shutil.copy(ROOT / "framework/agentic/skills/evals/comparison/claude-run/pptx_claude/slides/slide02.png",
                INPUTS / "slide.png")
    pdf = glob.glob(str(ROOT / "research" / "arsip" / "catatan_docs" / "Perbandingan*.pdf"))[0]
    document = pypdfium2.PdfDocument(pdf)
    document[4].render(scale=2).to_pil().convert("L").save(INPUTS / "halaman-pdf.png")
    document.close()
    page = subprocess.run(["pdftotext", "-f", "5", "-l", "5", "-enc", "UTF-8", pdf, "-"],
                          capture_output=True).stdout.decode("utf-8", "replace")
    font, bold = ImageFont.truetype("arial.ttf", 22), ImageFont.truetype("arialbd.ttf", 22)
    widths, row_h = [240, 210, 170, 140, 120], 48
    image = Image.new("RGB", (sum(widths) + 40, row_h * len(TABLE) + 40), "white")
    draw = ImageDraw.Draw(image)
    for r, row in enumerate(TABLE):
        x = 20
        for c, cell in enumerate(row):
            draw.rectangle([x, 20 + r * row_h, x + widths[c], 20 + (r + 1) * row_h], outline="black", width=2)
            draw.text((x + 10, 32 + r * row_h), cell, fill="black", font=bold if r == 0 else font)
            x += widths[c]
    image.save(INPUTS / "tabel.png")
    truth = {"mediawiki.webp": {"expected": MEDIAWIKI}, "slide.png": {"expected": SLIDE},
             "halaman-pdf.png": {"reference": page}, "tabel.png": {"expected": [c for row in TABLE for c in row],
                                                                    "rows": TABLE}}
    (INPUTS / "truth.json").write_text(json.dumps(truth, ensure_ascii=False, indent=2), encoding="utf-8")
    print("inputs:", sorted(p.name for p in INPUTS.iterdir()))


def read_with(reader: str, path: Path) -> str:
    if reader.startswith("docling-vlm:"):
        from zul.utilities.OCR.docling_OCR import DoclingVLMConverter
        converter = DoclingVLMConverter(model=reader.split(":", 1)[1], response_format="markdown", max_tokens=2048,
                                        hostname_and_port="http://localhost:11434/v1/chat/completions", timeout=300,
                                        prompt="Convert this page to markdown. Copy every visible text exactly.")
        return converter.convert_to_markdown(str(path))
    return rm.VisionReader(model=reader)(path.read_bytes(), path.name)


def _plain(text: str) -> str:
    text = re.sub(r"<[^>]+>|&lt;[^&]+&gt;|[*_#`|>\\]", " ", text)
    return " ".join(text.replace("’", "'").lower().split())


def _words(text: str) -> Counter:
    return Counter(re.findall(r"[^\W_]+", text.lower()))


def score(name: str, text: str, truth: dict) -> dict:
    plain = _plain(text)
    if "reference" in truth:
        ref, out = _words(truth["reference"]), _words(text)
        found = sum((ref & out).values())
        return {"word_recall": round(found / max(1, sum(ref.values())), 3),
                "word_precision": round(found / max(1, sum(out.values())), 3)}
    expected = truth["expected"]
    missing = [e for e in expected if _plain(e) not in plain]
    row = {"found": len(expected) - len(missing), "of": len(expected), "missing": missing}
    if "rows" in truth:          # a row is kept when its cells come in order on one line
        lines = [_plain(line) for line in text.splitlines()]
        row["rows_kept"] = sum(any(re.search(".*".join(re.escape(_plain(c)) for c in r), line) for line in lines)
                               for r in truth["rows"])
    return row


def run(readers: list) -> None:
    truth = json.loads((INPUTS / "truth.json").read_text(encoding="utf-8"))
    results_path = HERE / "results.json"
    results = json.loads(results_path.read_text(encoding="utf-8")) if results_path.exists() else {}
    for reader in readers:
        folder = OUTPUTS / re.sub(r"[^\w.-]+", "-", reader)
        folder.mkdir(parents=True, exist_ok=True)
        for name in truth:
            started = time.perf_counter()
            try:
                text, error = read_with(reader, INPUTS / name), ""
            except Exception as exc:  # noqa: BLE001 - a reader that fails is a result too
                text, error = "", str(exc)[:300]
            seconds = round(time.perf_counter() - started, 1)
            (folder / f"{Path(name).stem}.md").write_text(text, encoding="utf-8")
            results[f"{reader}/{name}"] = {"seconds": seconds, "error": error, **score(name, text, truth[name])}
            print(reader, name, results[f"{reader}/{name}"], flush=True)
            results_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


def rescore() -> None:
    truth = json.loads((INPUTS / "truth.json").read_text(encoding="utf-8"))
    results_path = HERE / "results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    for key, row in results.items():
        reader, name = key.rsplit("/", 1)
        text = (OUTPUTS / re.sub(r"[^\w.-]+", "-", reader) / f"{Path(name).stem}.md").read_text(encoding="utf-8")
        results[key] = {"seconds": row["seconds"], "error": row.get("error", ""), **score(name, text, truth[name])}
        print(key, results[key])
    results_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("screenshot", nargs="?", help="with --prepare: the mediawiki.org screenshot")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--readers", default=",".join(READERS))
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    if args.prepare:
        prepare(args.screenshot)
    elif args.score:
        rescore()
    else:
        run(args.readers.split(","))
    return 0


if __name__ == "__main__":
    sys.exit(main())
