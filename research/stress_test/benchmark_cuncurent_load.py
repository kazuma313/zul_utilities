#!/usr/bin/env python3
"""
GuideLLM Benchmark — CONCURRENT USER TEST (All 6 Scenarios)
Profile  : concurrent — ukur performa dari 1 hingga 1000 user aktif bersamaan
Tujuan   : Cari max concurrent user yang masih memenuhi SLO per scenario

Concurrency levels: 1, 2, 4, 8, 16, 32, 64, 100, 150, 200, 256, 300, 400, 512, 700, 1000

Scenarios:
  1. short         — 128 prompt / 128 output   (chat interaktif)
  2. medium        — 512 prompt / 256 output   (RAG chatbot)
  3. long          — 2048 prompt / 512 output  (summarization dokumen)
  4. decode_heavy  — 256 prompt / 1024 output  (code gen, laporan)
  5. summarization — dataset real multi_news / arxiv
  6. math_reasoning — dataset real MATH / LongReason / GSM8K

Estimasi durasi total:
  16 level × 120 detik × 6 scenario = ~192 menit (~3.2 jam)
  Jalankan di background dengan: ./run_benchmark.sh

Usage:
  Foreground : python benchmark_concurrent.py
  Background : ./run_benchmark.sh
  Monitor    : tail -f results/<timestamp>_concurrent/benchmark.log
"""

import json
import os
import sys
import logging
import site
import pathlib
import subprocess
from datetime import datetime
from pathlib import Path

# ============================================================
# KONFIGURASI
# ============================================================
URI       = "https://llm.air.id"
API_KEY   = ""
MODEL     = "qwen3-30b-zul-gpu-load-balancing"
PROCESSOR = "/data/qwen3-30b-a3b-instruct-2507"

# Level rendah (1-64)    : warmup GPU, temukan titik awal saturasi
# Level menengah (100-256): zona operasional 2 GPU H200 (max-num-seqs 256 per GPU)
# Level tinggi (300-512) : stress test mendekati batas hardware
# Level ekstrem (700-1000): uji antrian LiteLLM + perilaku saat overload
CONCURRENCY_LEVELS = [1, 2, 4, 8, 16, 32, 64, 100, 150, 200, 256, 300, 400, 512, 700, 1000]

# Durasi lebih lama di level tinggi agar sistem settle ke steady-state
# Level 1-64    : 90 detik cukup
# Level 100+    : butuh 120 detik — queue LiteLLM perlu waktu stabilisasi
# Level 512-1000: butuh 150 detik — termasuk warmup antrian
MAX_SECONDS = "120"
WARMUP      = "0.10"   # 10% awal dibuang — lebih ketat untuk akurasi
COOLDOWN    = "0.10"
MAX_ERRORS  = "100"    # toleransi error lebih tinggi di level ekstrem (700-1000)
SAMPLE_REQ  = "20"

# Nama folder dibaca dari env variable BENCHMARK_FOLDER_NAME yang di-set oleh run_benchmark.sh
# Format: 2026-07-06-{nama_benchmark}  →  results/2026-07-06-1gpu-qwen3-30b/
# Fallback: jika dijalankan langsung tanpa .sh, pakai tanggal + "benchmark"
_folder_name = os.environ.get(
    "BENCHMARK_FOLDER_NAME",
    f"{datetime.now().strftime('%Y-%m-%d')}-benchmark",
)
OUTPUT_DIR = Path(__file__).parent / "results" / _folder_name

# ============================================================
# LOGGING SETUP — stdout + file sekaligus
# ============================================================

def setup_logging(log_dir: Path) -> logging.Logger:
    """
    Setup logger dengan dua handler:
    - StreamHandler  → tetap tampil di terminal (stdout)
    - FileHandler    → disimpan ke log_dir/benchmark.log

    Format: [2026-07-06 14:23:01] INFO  — pesan
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "benchmark.log"

    fmt     = logging.Formatter(
        fmt      = "[%(asctime)s] %(levelname)-5s — %(message)s",
        datefmt  = "%Y-%m-%d %H:%M:%S",
    )

    logger  = logging.getLogger("benchmark")
    logger.setLevel(logging.DEBUG)

    # Handler 1: terminal
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)

    # Handler 2: file (menyimpan semua level termasuk DEBUG)
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    logger.addHandler(sh)
    logger.addHandler(fh)

    return logger, log_file


# Logger global — diinisialisasi di run() setelah OUTPUT_DIR dibuat
log: logging.Logger = None


def _log_subprocess_output(proc_result: subprocess.CompletedProcess):
    """Tulis stdout/stderr subprocess ke log file (level DEBUG)."""
    if proc_result.stdout:
        for line in proc_result.stdout.splitlines():
            log.debug("[guidellm stdout] %s", line)
    if proc_result.stderr:
        for line in proc_result.stderr.splitlines():
            log.debug("[guidellm stderr] %s", line)


# ============================================================
# DEFINISI 6 SCENARIO
# ============================================================
SCENARIOS = [
    {
        "name"    : "short",
        "data"    : "prompt_tokens=128,output_tokens=128",
        "use_case": "Chat interaktif, QnA singkat",
        "slo": {
            "ttft_p95_ms": 500,
            "itl_p95_ms" : 20,
            "e2e_p95_s"  : 3.0,
            "error_rate" : 0.01,
        },
    },
    {
        "name"    : "medium",
        "data"    : "prompt_tokens=512,output_tokens=256",
        "use_case": "RAG chatbot, draft email",
        "slo": {
            "ttft_p95_ms": 1000,
            "itl_p95_ms" : 30,
            "e2e_p95_s"  : 8.0,
            "error_rate" : 0.01,
        },
    },
    {
        "name"    : "long",
        "data"    : "prompt_tokens=2048,output_tokens=512",
        "use_case": "Summarization dokumen panjang",
        "slo": {
            "ttft_p95_ms": 3000,
            "itl_p95_ms" : 50,
            "e2e_p95_s"  : 30.0,
            "error_rate" : 0.02,
        },
    },
    {
        "name"    : "decode_heavy",
        "data"    : "prompt_tokens=256,output_tokens=1024",
        "use_case": "Code generation, laporan otomatis",
        "slo": {
            "ttft_p95_ms": 800,
            "itl_p95_ms" : 30,
            "e2e_p95_s"  : 45.0,
            "tps_min"    : 40,
            "error_rate" : 0.02,
        },
    },
    {
        "name"    : "summarization",
        "data"    : None,
        "use_case": "Summarization multi-dokumen (real dataset)",
        "slo": {
            "ttft_p95_ms": 2000,
            "itl_p95_ms" : 40,
            "e2e_p95_s"  : 60.0,
            "error_rate" : 0.03,
        },
    },
    {
        "name"    : "math_reasoning",
        "data"    : None,
        "use_case": "Math reasoning, Chain-of-Thought",
        "slo": {
            "ttft_p95_ms": 800,
            "itl_p95_ms" : 25,
            "e2e_p95_s"  : 120.0,
            "tps_min"    : 40,
            "error_rate" : 0.02,
        },
    },
]

SUMMARIZATION_INSTRUCTION = (
    "You are a professional document analyst. "
    "Read the following document carefully and provide a concise summary "
    "covering: (1) main topic, (2) key findings or events, (3) important conclusions. "
    "Keep your summary under 300 words.\n\nDOCUMENT:\n"
)

COT_INSTRUCTION = (
    "You are an expert mathematician and logical reasoner. "
    "Solve the following problem step by step. "
    "Show your complete reasoning process, including all intermediate calculations. "
    "At the end, clearly state your final answer.\n\nPROBLEM:\n"
)


# ============================================================
# PATCH & VALIDASI
# ============================================================

def patch_health_check():
    """
    Cari lokasi guidellm secara dinamis menggunakan importlib.
    Menangani semua jenis instalasi:
      - pip install --user  → ~/.local/lib/...
      - pip install         → /usr/local/lib/...
      - venv                → <venv>/lib/...
      - conda               → <conda_env>/lib/...
    """
    import importlib.util

    spec = importlib.util.find_spec("guidellm")
    if spec is None or spec.origin is None:
        log.warning("Patch skip: guidellm tidak ditemukan via importlib.")
        return

    # spec.origin = .../guidellm/__init__.py
    # parent      = .../guidellm/
    guidellm_root = pathlib.Path(spec.origin).parent
    target        = guidellm_root / "backends" / "openai" / "http.py"

    log.debug("Guidellm path: %s", guidellm_root)
    log.debug("Patch target : %s", target)

    if not target.exists():
        log.warning("Patch skip: %s tidak ditemukan (mungkin sudah berubah di versi ini).", target)
        return

    src = target.read_text()
    if "patched: skip /health check" in src:
        log.info("Patch health check sudah diterapkan — skip.")
        return

    old_str = "    async def validate(self):"
    new_str = "    async def validate(self):\n        return  # patched: skip /health check"
    if old_str not in src:
        log.warning("Patch skip: signature 'validate(self)' tidak ditemukan — mungkin sudah berubah di guidellm %s.", "0.7.1")
        return

    target.write_text(src.replace(old_str, new_str, 1))
    log.info("Patch health check berhasil diterapkan → %s", target)


def validate_backend() -> bool:
    import httpx

    client = httpx.Client(
        headers = {"Authorization": f"Bearer {API_KEY}"},
        timeout = 60,
    )

    log.info("─── Validasi backend ───────────────────────────────────────")

    # Step 1 — koneksi
    log.info("[1/3] Mengecek koneksi ke %s ...", URI)
    try:
        resp = client.get(f"{URI}/v1/models")
    except httpx.ConnectError:
        log.error("Tidak bisa terhubung ke %s", URI)
        return False
    except httpx.TimeoutException:
        log.error("Timeout saat koneksi ke %s", URI)
        return False

    if resp.status_code == 401:
        log.error("API_KEY tidak valid (401 Unauthorized)")
        return False
    log.info("    Server dapat diakses (HTTP %s)", resp.status_code)

    # Step 2 — cek model
    log.info("[2/3] Mengecek model '%s' ...", MODEL)
    try:
        resp   = client.get(f"{URI}/v1/models")
        models = [m["id"] for m in resp.json().get("data", [])]
        if MODEL not in models:
            log.error("Model '%s' tidak ditemukan. Tersedia: %s", MODEL, models)
            return False
        log.info("    Model '%s' tersedia.", MODEL)
    except Exception as exc:
        log.warning("    Gagal cek model (%s), lanjut.", exc)

    # Step 3 — test inference
    log.info("[3/3] Test request ke model ...")
    try:
        resp = client.post(
            f"{URI}/v1/chat/completions",
            json={
                "model"     : MODEL,
                "messages"  : [{"role": "user", "content": "Reply OK only."}],
                "max_tokens": 5,
                "stream"    : False,
            },
            timeout=30,
        )
    except Exception as exc:
        log.error("Request gagal: %s", exc)
        return False

    if resp.status_code != 200:
        log.error("Model error (HTTP %s): %s", resp.status_code, resp.text[:200])
        return False

    content = resp.json()["choices"][0]["message"]["content"]
    log.info('    Model merespons → "%s"', content.strip())
    client.close()

    log.info("Semua validasi passed.")
    log.info("────────────────────────────────────────────────────────────")
    return True


# ============================================================
# DATASET
# ============================================================

def prepare_real_dataset(scenario_name: str, out_dir: Path) -> str | None:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"dataset_{scenario_name}.jsonl"

    if scenario_name == "summarization":
        datasets_to_try = [
            {"id": "alexfabbri/multi_news",    "split": "test", "col": "document", "max_chars": 6000, "instruction": SUMMARIZATION_INSTRUCTION},
            {"id": "ccdv/arxiv-summarization", "split": "test", "col": "article",  "max_chars": 8000, "instruction": SUMMARIZATION_INSTRUCTION},
        ]
    elif scenario_name == "math_reasoning":
        datasets_to_try = [
            {"id": "DigitalLearningGmbH/MATH-lighteval", "split": "test",     "col": "problem",  "max_chars": 2000, "instruction": COT_INSTRUCTION,
             "filter": lambda row: row.get("level", "") in ["Level 4", "Level 5"]},
            {"id": "lz1bytedance/LongReason",            "split": "original", "col": "input",    "max_chars": 4000, "instruction": COT_INSTRUCTION},
            {"id": "openai/gsm8k",                       "split": "test",     "col": "question", "max_chars": 2000, "instruction": COT_INSTRUCTION, "config": "main"},
        ]
    else:
        return None

    for ds_info in datasets_to_try:
        try:
            from datasets import load_dataset
            kwargs = {"split": ds_info["split"], "trust_remote_code": True}
            if ds_info.get("config"):
                kwargs["name"] = ds_info["config"]

            ds = load_dataset(ds_info["id"], **kwargs)
            if ds_info.get("filter"):
                ds = ds.filter(ds_info["filter"])

            count = 0
            with open(out_path, "w", encoding="utf-8") as f:
                for row in ds:
                    if count >= 150:
                        break
                    text = row.get(ds_info["col"], "")
                    if not text or len(text.strip()) < 50:
                        continue
                    prompt = ds_info["instruction"] + text[: ds_info["max_chars"]].strip()
                    f.write(json.dumps({"prompt": prompt}, ensure_ascii=False) + "\n")
                    count += 1

            if count > 0:
                log.info("    Dataset '%s': %d prompts → %s", ds_info["id"], count, out_path.name)
                return str(out_path)
        except Exception as exc:
            log.warning("    %s: %s", ds_info["id"], exc)

    return None


# ============================================================
# BENCHMARK RUNNER
# ============================================================

def run_scenario_concurrent(scenario: dict, scenario_dir: Path) -> dict:
    """
    Gunakan syntax GuideLLM v0.7.x:
      guidellm run
        --backend openai_http target=URL,model=MODEL,api_key=KEY
        --profile concurrent
        --override "profile.streams" 1,2,4,...
        --constraint max_duration seconds=120
        --constraint max_errors count=100
        --data synthetic prompt_tokens=128,output_tokens=128
        --output json path=./benchmarks.json
    """
    name     = scenario["name"]
    data     = scenario["data"]
    streams  = ",".join(str(c) for c in CONCURRENCY_LEVELS)

    # ── Backend string (key=value format v0.7.x) ─────────────
    backend_str = f"kind=openai_http,target={URI},model={MODEL},api_key={API_KEY}"

    # ── Data string ───────────────────────────────────────────
    # Synthetic: "synthetic prompt_tokens=128,output_tokens=128"
    # File JSONL: "json_file path=/path/to/file.jsonl"
    if scenario.get("use_real_dataset"):
        data_str = f"kind=json_file,path={data}"
    else:
        # data sudah dalam format "prompt_tokens=128,output_tokens=128"
        # data format: "prompt_tokens=128,output_tokens=128"
        data_str = f"kind=synthetic_text,{data}"

    cmd = [
        "guidellm", "run",
        "--backend",   backend_str,
        "--tokenizer", f"kind=huggingface_auto,model={PROCESSOR}",

        # Profile: concurrent dengan list streams
        "--profile",   "kind=concurrent",
        "--override",  "profile.streams", streams,

        # Constraints: durasi + max errors per level
        "--constraint", f"kind=max_duration,seconds={MAX_SECONDS}",
        "--constraint", f"kind=max_errors,count={MAX_ERRORS}",

        # Data
        "--data",      data_str,

        # Output
        "--output",    f"kind=json,path={scenario_dir}/benchmarks.json",
        "--output",    f"kind=html,path={scenario_dir}/benchmarks.html",
    ]

    # Warmup & cooldown jika didukung di v0.7.x
    # Warmup & cooldown via profile kind string
    # (sudah ter-handle via kind=concurrent defaults di v0.7.x)

    log.info("=" * 60)
    log.info("  ▶  [%s]  %s", name.upper(), scenario["use_case"])
    log.info("     Data        : %s", data)
    log.info("     Concurrency : %s", CONCURRENCY_LEVELS)
    log.info("     Durasi/level: %ss", MAX_SECONDS)
    log.info("     Output      : %s", scenario_dir)
    log.info("=" * 60)

    # Simpan command yang dijalankan ke log (untuk reproducibility)
    log.debug("CMD: %s", " ".join(cmd))

    # Jalankan dengan Popen — stream output real-time ke terminal DAN log file
    # Tidak pakai capture_output=True karena akan buffer semua output sampai selesai
    # sehingga progress tidak terlihat selama benchmark berjalan (~32 menit)
    log_file_path = OUTPUT_DIR / "benchmark.log"

    with open(log_file_path, "a", encoding="utf-8") as log_fh:
        process = subprocess.Popen(
            cmd,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,   # gabung stderr ke stdout
            text   = True,
            bufsize= 1,                   # line-buffered
        )

        # Stream setiap baris — tulis ke terminal + log file sekaligus
        for line in process.stdout:
            print(line, end="", flush=True)           # terminal (real-time)
            log_fh.write(f"[guidellm] {line}")        # log file
            log_fh.flush()

        process.wait()
        returncode = process.returncode

    if returncode == 0:
        log.info("Selesai → %s", scenario_dir)
        return evaluate_concurrent(scenario, scenario_dir)
    else:
        log.error("Gagal (returncode %d)", returncode)
        return {}


# ============================================================
# EVALUASI
# ============================================================

def evaluate_concurrent(scenario: dict, scenario_dir: Path) -> dict:
    json_file = scenario_dir / "benchmarks.json"
    if not json_file.exists():
        log.warning("benchmarks.json tidak ditemukan di %s, skip evaluasi.", scenario_dir)
        return {}

    try:
        from guidellm import GenerativeBenchmarksReport
        report = GenerativeBenchmarksReport.from_file(json_file)
    except Exception as exc:
        log.warning("Tidak bisa load report: %s", exc)
        return {}

    slo     = scenario["slo"]
    name    = scenario["name"]
    results = {}

    log.info("")
    log.info("  📊 Hasil per concurrency level — %s", name.upper())
    log.info("  %-8s %6s %7s %10s %9s %9s %6s %8s",
             "Level", "RPS", "TPS", "TTFT p95", "ITL p95", "E2E p95", "Err%", "Status")
    log.info("  %s", "-" * 75)

    max_passing_concurrency = 0

    for i, bench in enumerate(report.benchmarks):
        level = CONCURRENCY_LEVELS[i] if i < len(CONCURRENCY_LEVELS) else f"idx{i}"
        try:
            ttft_p95 = bench.request_latency.time_to_first_token_s.percentile(95) * 1000
            itl_p95  = bench.token_latency.inter_token_latency_s.percentile(95) * 1000
            e2e_p95  = bench.request_latency.request_latency_s.percentile(95)
            tps      = bench.token_throughput.output or 0
            total    = (bench.request_counts.successful or 0) + (bench.request_counts.error or 0)
            err_rate = (bench.request_counts.error or 0) / total if total > 0 else 0
            rps      = bench.request_throughput.successful or 0

            all_ok = all([
                ttft_p95 <= slo["ttft_p95_ms"],
                itl_p95  <= slo["itl_p95_ms"],
                e2e_p95  <= slo["e2e_p95_s"],
                err_rate <= slo["error_rate"],
                tps      >= slo.get("tps_min", 0),
            ])

            status = "✅ PASS" if all_ok else "❌ FAIL"
            if all_ok:
                max_passing_concurrency = level

            results[level] = {
                "pass"        : all_ok,
                "rps"         : round(rps, 2),
                "tps"         : round(tps, 1),
                "ttft_p95_ms" : round(ttft_p95, 1),
                "itl_p95_ms"  : round(itl_p95, 1),
                "e2e_p95_s"   : round(e2e_p95, 2),
                "error_rate"  : round(err_rate * 100, 2),
            }

            log.info(
                "  %-8s %6.2f %7.1f %9.1fms %8.1fms %8.2fs %5.1f%% %8s",
                f"{level}u", rps, tps, ttft_p95, itl_p95, e2e_p95, err_rate * 100, status,
            )

        except Exception as exc:
            log.warning("  %-8s parse error: %s", f"{level}u", exc)

    log.info("")
    log.info("  🏆 Max concurrent user yang PASS semua SLO: %s user", max_passing_concurrency)
    return results


# ============================================================
# SUMMARY
# ============================================================

def print_final_summary(all_results: dict):
    log.info("")
    log.info("=" * 70)
    log.info("  🏁 RINGKASAN AKHIR — CONCURRENT USER BENCHMARK")
    log.info("=" * 70)
    log.info("  %-18s %14s %10s %16s", "Scenario", "Max Safe Users", "RPS @ Max", "TTFT p95 @ Max")
    log.info("  %s", "-" * 65)

    for scenario_name, level_results in all_results.items():
        if not level_results:
            log.info("  %-18s %14s", scenario_name, "—")
            continue

        passing = {k: v for k, v in level_results.items() if v.get("pass")}
        if passing:
            max_level = max(passing.keys())
            data      = passing[max_level]
            log.info("  %-18s %14s %9.2f %14.1fms",
                     scenario_name, f"{max_level} user", data["rps"], data["ttft_p95_ms"])
        else:
            log.info("  %-18s %14s", scenario_name, "0 (semua gagal)")

    log.info("")
    log.info("  📁 Semua hasil di: %s", OUTPUT_DIR)
    log.info("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

def run():
    global log

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Inisialisasi logging setelah OUTPUT_DIR dibuat
    log, log_file = setup_logging(OUTPUT_DIR)
    log.info("📁 Output root  : %s", OUTPUT_DIR)
    log.info("📝 Log file     : %s", log_file)
    log.info("🤖 Model        : %s", MODEL)
    log.info("🎯 Target       : %s", URI)
    log.info("👥 Concurrency  : %s", CONCURRENCY_LEVELS)
    log.info(
        "⏱️  Estimasi     : ~%d menit total (%d scenario × %d level × %ss)",
        int(MAX_SECONDS) * len(CONCURRENCY_LEVELS) * len(SCENARIOS) // 60,
        len(SCENARIOS), len(CONCURRENCY_LEVELS), MAX_SECONDS,
    )
    log.info("⚠️  Catatan      : level 512-1000 adalah stress test — error rate mungkin tinggi, ini normal")
    log.info("📋 Scenarios    : %s", [s["name"] for s in SCENARIOS])
    log.info("")

    # Simpan metadata run
    meta = {
        "model"               : MODEL,
        "target"              : URI,
        "concurrency_levels"  : CONCURRENCY_LEVELS,
        "max_seconds_per_level": MAX_SECONDS,
        "scenarios"           : [s["name"] for s in SCENARIOS],
        "run_date"            : datetime.now().isoformat(),
        "log_file"            : str(log_file),
    }
    with open(OUTPUT_DIR / "run_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    all_results: dict = {}

    for scenario in SCENARIOS:
        name         = scenario["name"]
        scenario_dir = OUTPUT_DIR / name
        scenario_dir.mkdir(parents=True, exist_ok=True)

        # Siapkan dataset real jika perlu
        if name in ("summarization", "math_reasoning"):
            log.info("📦 Menyiapkan dataset untuk %s ...", name)
            dataset_path = prepare_real_dataset(name, scenario_dir)

            if dataset_path:
                scenario["data"]             = dataset_path
                scenario["use_real_dataset"] = True
                log.info("    Dataset siap: %s", dataset_path)
            else:
                scenario["data"]             = (
                    "prompt_tokens=1500,output_tokens=300"
                    if name == "summarization"
                    else "prompt_tokens=200,output_tokens=800"
                )
                scenario["use_real_dataset"] = False
                log.warning("    Fallback synthetic: %s", scenario["data"])

        # Jalankan benchmark
        level_results          = run_scenario_concurrent(scenario, scenario_dir)
        all_results[name]      = level_results

        # Simpan hasil evaluasi per scenario
        eval_path = scenario_dir / "concurrent_evaluation.json"
        with open(eval_path, "w") as f:
            json.dump(level_results, f, indent=2)
        log.debug("Evaluasi disimpan → %s", eval_path)

    # Ringkasan akhir
    print_final_summary(all_results)

    # Simpan ringkasan ke file
    summary_path = OUTPUT_DIR / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(all_results, f, indent=2)

    log.info("✅ Semua benchmark selesai.")
    log.info("📁 Hasil lengkap : %s", OUTPUT_DIR)
    log.info("📝 Log lengkap   : %s", log_file)


if __name__ == "__main__":
    # Logger sementara sebelum OUTPUT_DIR siap (untuk patch & validasi)
    logging.basicConfig(
        level   = logging.INFO,
        format  = "[%(asctime)s] %(levelname)-5s — %(message)s",
        datefmt = "%Y-%m-%d %H:%M:%S",
        stream  = sys.stdout,
    )
    log = logging.getLogger("benchmark")

    log.info("=" * 60)
    log.info("  GuideLLM Benchmark — CONCURRENT USER (6 Scenarios)")
    log.info("=" * 60)

    patch_health_check()
    log.info("")

    if not validate_backend():
        log.error("⛔ Benchmark dibatalkan karena validasi gagal.")
        sys.exit(1)

    run()