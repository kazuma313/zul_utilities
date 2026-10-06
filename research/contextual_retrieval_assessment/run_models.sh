#!/usr/bin/env bash
# Runs the whole assessment again: header only, then the three models, the retrieval scores, and a new judging sheet.
# Everything goes to rerun/, so the recorded results (and the judge scores that belong to them) stay as they are.
# Needs Ollama with gemma3:4b, qwen3:4b, qwen3:8b and nomic-embed-text; about 50 minutes on an RTX 3060 6 GB.
cd "$(dirname "$0")"
ROOT=$(cd ../.. && pwd)
SKILL="$ROOT/research/agentic/algorithms/skills/contextual_retrieval"
py() { uv run --project "$ROOT" python "$@"; }
mkdir -p rerun/runs rerun/logs

py "$SKILL/scripts/contextualize.py" corpus/* -o rerun/runs/header.jsonl --no-llm
for model in gemma3:4b qwen3:4b qwen3:8b; do
  name=$(echo "$model" | tr ':' '-')
  start=$(date +%s)
  echo "=== $model $(date +%H:%M:%S)"
  py "$SKILL/scripts/contextualize.py" corpus/* -o "rerun/runs/$name.jsonl" --model "$model" --verbose > "rerun/logs/$name.log" 2>&1
  echo "exit $? after $(( $(date +%s) - start )) s"
  grep -E "^(OK|- |ERROR)" "rerun/logs/$name.log"
done

py "$SKILL/evals/retrieval_eval.py" --queries queries.json --out rerun/retrieval.json \
  --run header=rerun/runs/header.jsonl --run gemma3-4b=rerun/runs/gemma3-4b.jsonl \
  --run qwen3-4b=rerun/runs/qwen3-4b.jsonl --run qwen3-8b=rerun/runs/qwen3-8b.jsonl
py "$SKILL/evals/judge_sheet.py" make --every 3 --out rerun/judge \
  --run gemma3-4b=rerun/runs/gemma3-4b.jsonl --run qwen3-4b=rerun/runs/qwen3-4b.jsonl --run qwen3-8b=rerun/runs/qwen3-8b.jsonl
echo "=== done: score rerun/judge/sheet.md into rerun/judge/scores.json, then run judge_sheet.py score --out rerun/judge"
