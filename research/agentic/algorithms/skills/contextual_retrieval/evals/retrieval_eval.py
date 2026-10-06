"""How often the right chunk is found, with and without contexts: embeddings, BM25 and both (rank fusion).

    python evals/retrieval_eval.py --run header=runs/header.jsonl --run gemma3-4b=runs/gemma3-4b.jsonl \
        --queries evals/queries.json --out runs/retrieval.json

Every --run is the output of scripts/contextualize.py for the same documents.  "raw" (the chunk text alone)
is added from the first run.  The right chunk of a question is the one that contains its "evidence".
Embeddings come from Ollama (default nomic-embed-text) and are cached next to --out, so a second run only
embeds new texts.  Reports recall@k (the right chunk among the first k) and MRR, overall and per question
type, like the article's 1 - recall@20 measured on a smaller corpus.  Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

KS = (1, 3, 5, 10)


def norm(text: str) -> str:
    return " ".join(text.lower().split())


def tokens(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


class BM25:
    """Okapi BM25 over whole words (k1 1.5, b 0.75), the classic lexical ranking."""

    def __init__(self, texts: list[str], k1: float = 1.5, b: float = 0.75):
        self.docs = [Counter(tokens(t)) for t in texts]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg = sum(self.lengths) / max(1, len(self.lengths))
        df = Counter(word for d in self.docs for word in d)
        n = len(self.docs)
        self.idf = {w: math.log(1 + (n - f + 0.5) / (f + 0.5)) for w, f in df.items()}
        self.k1, self.b = k1, b

    def scores(self, query: str) -> list[float]:
        words = tokens(query)
        out = []
        for doc, length in zip(self.docs, self.lengths):
            score = 0.0
            for w in words:
                f = doc.get(w, 0)
                if f:
                    score += self.idf[w] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * length / self.avg))
            out.append(score)
        return out


class Embedder:
    def __init__(self, model: str, base_url: str, cache_path: Path):
        self.model, self.base = model, base_url.rstrip("/")
        self.cache_path = cache_path
        self.cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
        self.nomic = "nomic" in model

    def _key(self, text: str) -> str:
        return hashlib.sha1(f"{self.model}\n{text}".encode("utf-8")).hexdigest()

    def vectors(self, texts: list[str], kind: str) -> list[list[float]]:
        prefix = ("search_query: " if kind == "query" else "search_document: ") if self.nomic else ""
        texts = [prefix + t for t in texts]
        missing = [t for t in dict.fromkeys(texts) if self._key(t) not in self.cache]
        for i in range(0, len(missing), 16):
            group = missing[i:i + 16]
            request = urllib.request.Request(self.base + "/api/embed", headers={"Content-Type": "application/json"},
                                             data=json.dumps({"model": self.model, "input": group}).encode("utf-8"))
            with urllib.request.urlopen(request, timeout=600) as response:
                for text, vector in zip(group, json.loads(response.read().decode("utf-8"))["embeddings"]):
                    self.cache[self._key(text)] = vector
        if missing:
            self.cache_path.write_text(json.dumps(self.cache), encoding="utf-8")
        return [self.cache[self._key(t)] for t in texts]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)) or 1.0)


def ranking(scores: list[float]) -> list[int]:
    return sorted(range(len(scores)), key=lambda i: -scores[i])


def fuse(*rankings: list[int], k: int = 60) -> list[int]:
    """Reciprocal rank fusion: every ranking gives 1 / (k + rank) to each chunk."""
    total: Counter = Counter()
    for order in rankings:
        for rank, index in enumerate(order):
            total[index] += 1 / (k + rank + 1)
    return [i for i, _ in total.most_common()]


def metrics(ranks: list[int | None]) -> dict:
    """recall@k and MRR from the 0-based rank of the right chunk in each ranking (None: not found)."""
    n = len(ranks) or 1
    out = {f"recall@{k}": sum(r is not None and r < k for r in ranks) / n for k in KS}
    out["mrr@10"] = sum(1 / (r + 1) for r in ranks if r is not None and r < 10) / n
    return out


def evaluate(records: list[dict], field: str, queries: list[dict], embedder: Embedder, query_vectors: list) -> dict:
    texts = [r[field] for r in records]
    gold = []
    for q in queries:
        hits = [i for i, r in enumerate(records) if norm(q["evidence"]) in norm(r["text"])]
        if len(hits) != 1:
            raise ValueError(f"evidence {q['evidence']!r} is in {len(hits)} chunks, not 1")
        gold.append(hits[0])
    doc_vectors = embedder.vectors(texts, "document")
    bm25 = BM25(texts)
    results = {"dense": [], "bm25": [], "hybrid": []}
    for q, g, qv in zip(queries, gold, query_vectors):
        dense = ranking([cosine(qv, dv) for dv in doc_vectors])
        lexical = ranking(bm25.scores(q["q"]))
        for name, order in (("dense", dense), ("bm25", lexical), ("hybrid", fuse(dense, lexical))):
            results[name].append(order.index(g))
    report = {}
    for name, ranks in results.items():
        report[name] = metrics(ranks)
        for kind in sorted({q["type"] for q in queries}):
            report[name][kind] = metrics([r for r, q in zip(ranks, queries) if q["type"] == kind])
        report[name]["ranks"] = ranks
    return report


def run_stats(records: list[dict]) -> dict:
    with_context = [r for r in records if r.get("context")]
    reasons = Counter(p.split(":")[0] for r in records for p in r.get("checks", []))
    seconds = [r.get("seconds", 0) for r in records]
    return {"chunks": len(records), "with_context": len(with_context),
            "context_words": round(sum(len(r["context"].split()) for r in with_context) / max(1, len(with_context)), 1),
            "seconds_per_chunk": round(sum(seconds) / max(1, len(seconds)), 2), "rejected": dict(reasons)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", action="append", required=True, metavar="NAME=FILE", help="output of contextualize.py")
    ap.add_argument("--queries", default=str(Path(__file__).with_name("queries.json")))
    ap.add_argument("--embed-model", default="nomic-embed-text")
    ap.add_argument("--base-url", default="http://localhost:11434")
    ap.add_argument("--out", default="retrieval.json")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    queries = json.loads(Path(args.queries).read_text(encoding="utf-8"))["queries"]
    out = Path(args.out)
    embedder = Embedder(args.embed_model, args.base_url, out.with_name(out.stem + ".embeddings.json"))
    query_vectors = embedder.vectors([q["q"] for q in queries], "query")
    runs = {}
    for item in args.run:
        name, _, path = item.partition("=")
        runs[name] = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    first = next(iter(runs.values()))
    results = {"raw": {"retrieval": evaluate(first, "text", queries, embedder, query_vectors), "stats": {}}}
    for name, records in runs.items():
        results[name] = {"retrieval": evaluate(records, "contextualized_text", queries, embedder, query_vectors),
                         "stats": run_stats(records)}
    out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    kinds = sorted({q["type"] for q in queries})
    counts = ", ".join(f"{sum(q['type'] == kind for q in queries)} {kind}" for kind in kinds)
    print(f"{len(queries)} questions ({counts}), {len(first)} chunks, embeddings {args.embed_model}")
    print(f"{'variant':<12} {'method':<7} " + " ".join(f"{'R@' + str(k):>5}" for k in KS) + f" {'MRR':>5}  "
          + " ".join(f"{k[:8] + ' R@5':>13}" for k in kinds))
    for name, result in results.items():
        for method in ("dense", "bm25", "hybrid"):
            m = result["retrieval"][method]
            print(f"{name:<12} {method:<7} " + " ".join(f"{m[f'recall@{k}']:>5.2f}" for k in KS) + f" {m['mrr@10']:>5.2f}  "
                  + " ".join(f"{m[k]['recall@5']:>13.2f}" for k in kinds))
    print(f"results: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
