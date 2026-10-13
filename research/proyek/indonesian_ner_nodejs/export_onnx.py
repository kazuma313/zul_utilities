"""Download cahya/bert-base-indonesian-NER and convert it to ONNX, the format transformers.js can run in Node.js.

    uv run --with onnx --with onnxscript python export_onnx.py

The Hugging Face repository only has PyTorch and Flax weights. This script writes, in models/cahya/bert-base-indonesian-NER/:
  onnx/model.onnx   the network (fp32), with batch size and sentence length left free
  tokenizer.json    the WordPiece tokenizer (lower case), built from the repository's vocab.txt
  config.json       includes the 39 labels (B-/I- for 19 entity types, and O)
and, next to this script, reference.json: what the original PyTorch model answers for every line of samples.txt.
check.mjs compares Node.js against it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline

MODEL_ID = "cahya/bert-base-indonesian-NER"
HERE = Path(__file__).resolve().parent
OUT = HERE / "models" / MODEL_ID
INPUTS = ("input_ids", "attention_mask", "token_type_ids")


class Logits(torch.nn.Module):
    """The model with plain tensors in and out, which is what the exporter needs."""

    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, input_ids, attention_mask, token_type_ids):
        return self.model(input_ids=input_ids, attention_mask=attention_mask, token_type_ids=token_type_ids).logits


def export(model, tokenizer) -> Path:
    path = OUT / "onnx" / "model.onnx"
    path.parent.mkdir(parents=True, exist_ok=True)
    example = tokenizer("Joko Widodo lahir di Surakarta.", return_tensors="pt")
    batch, length = torch.export.Dim("batch", max=64), torch.export.Dim("sequence", max=512)
    torch.onnx.export(
        Logits(model).eval(), tuple(example[name] for name in INPUTS), str(path),
        input_names=list(INPUTS), output_names=["logits"], dynamo=True, external_data=False,
        dynamic_shapes={name: {0: batch, 1: length} for name in INPUTS},
    )
    return path


def reference(model, tokenizer) -> list[dict]:
    """Token ids, tokens, logits and entities of the PyTorch model, for comparing the Node.js result."""
    ner = pipeline("token-classification", model=model, tokenizer=tokenizer, aggregation_strategy="first", device="cpu")
    rows = []
    for text in (HERE / "samples.txt").read_text(encoding="utf-8").splitlines():
        if not text.strip():
            continue
        encoded = tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            logits = model(**encoded).logits[0]
        ids = encoded["input_ids"][0].tolist()
        rows.append({
            "text": text,
            "input_ids": ids,
            "tokens": tokenizer.convert_ids_to_tokens(ids),
            "labels": [model.config.id2label[i] for i in logits.argmax(-1).tolist()],
            "logits": [[round(x, 5) for x in row] for row in logits.tolist()],
            "entities": [{"type": e["entity_group"], "text": text[e["start"]:e["end"]], "start": int(e["start"]),
                          "end": int(e["end"]), "score": round(float(e["score"]), 4)} for e in ner(text)],
        })
    return rows


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")       # torch.onnx prints emoji; the Windows console is cp1252
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForTokenClassification.from_pretrained(MODEL_ID, attn_implementation="eager").eval()
    path = export(model, tokenizer)
    tokenizer.save_pretrained(OUT)
    model.config.save_pretrained(OUT)
    rows = reference(model, tokenizer)
    (HERE / "reference.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"ONNX: {path} ({path.stat().st_size / 1e6:.0f} MB)")
    print(f"reference: {len(rows)} sentences, {sum(len(r['entities']) for r in rows)} entities")
    for row in rows:
        print("-", row["text"])
        for e in row["entities"]:
            print(f"    {e['type']:<4} {e['text']}  ({e['score']})")


if __name__ == "__main__":
    main()
