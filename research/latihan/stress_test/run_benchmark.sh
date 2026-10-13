#!/usr/bin/env bash
# =============================================================
# run_benchmark.sh — Jalankan benchmark_concurrent.py di background
#
# Cara pakai:
#   chmod +x run_benchmark.sh
#   ./run_benchmark.sh              # start background
#   ./run_benchmark.sh status       # cek apakah masih jalan
#   ./run_benchmark.sh monitor      # live tail log terbaru
#   ./run_benchmark.sh stop         # stop proses benchmark
#
# Format folder output:
#   results/2026-07-06-{BENCHMARK_NAME}/
# =============================================================

# ============================================================
# ✏️  GANTI NAMA BENCHMARK DI SINI
# ------------------------------------------------------------
# Nama ini akan jadi bagian dari nama folder hasil benchmark.
# Gunakan huruf kecil, angka, dan tanda hubung (-) saja.
# Contoh: "1gpu-qwen3-30b", "2gpu-loadbalance", "gpu5-baseline"
# ============================================================
# BENCHMARK_NAME="1gpu-qwen3-30b-gpu5" -> change this to your desired benchmark name
BENCHMARK_NAME="2gpu-qwen3-30b-gpu-loadbalance-usage-based-routing-kedua"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCHMARK_PY="$SCRIPT_DIR/benchmark_cuncurent_load.py"
RESULTS_DIR="$SCRIPT_DIR/results"
PID_FILE="$SCRIPT_DIR/benchmark.pid"
NOHUP_LOG="$SCRIPT_DIR/nohup_${BENCHMARK_NAME}.log"

# ── Warna output ──────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# ── Helper: cari log terbaru ──────────────────────────────────
latest_log() {
    find "$RESULTS_DIR" -name "benchmark.log" 2>/dev/null \
        | sort | tail -n 1
}

# ── Helper: cek proses masih jalan ───────────────────────────
is_running() {
    [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

# =============================================================
# SUBCOMMAND: status
# =============================================================
if [[ "$1" == "status" ]]; then
    echo ""
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}✅ Benchmark sedang berjalan (PID: $PID)${NC}"

        LOG=$(latest_log)
        if [[ -n "$LOG" ]]; then
            echo -e "${BLUE}📝 Log file: $LOG${NC}"
            echo ""
            echo "── 10 baris terakhir log ──────────────────────────────────"
            tail -n 10 "$LOG"
        fi
    else
        echo -e "${YELLOW}⚠️  Tidak ada benchmark yang sedang berjalan.${NC}"
        LOG=$(latest_log)
        if [[ -n "$LOG" ]]; then
            echo -e "${BLUE}📝 Log terakhir ditemukan: $LOG${NC}"
            echo ""
            echo "── 5 baris terakhir log ───────────────────────────────────"
            tail -n 5 "$LOG"
        fi
    fi
    echo ""
    exit 0
fi

# =============================================================
# SUBCOMMAND: monitor
# =============================================================
if [[ "$1" == "monitor" ]]; then
    LOG=$(latest_log)
    if [[ -z "$LOG" ]]; then
        echo -e "${RED}❌ Tidak ada log file ditemukan di $RESULTS_DIR${NC}"
        exit 1
    fi
    echo -e "${BLUE}📡 Live monitoring: $LOG${NC}"
    echo -e "${YELLOW}   (Ctrl+C untuk keluar — benchmark tetap jalan di background)${NC}"
    echo ""
    tail -f "$LOG"
    exit 0
fi

# =============================================================
# SUBCOMMAND: stop
# =============================================================
if [[ "$1" == "stop" ]]; then
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo -e "${YELLOW}🛑 Menghentikan benchmark (PID: $PID) ...${NC}"
        kill "$PID"
        sleep 2
        if kill -0 "$PID" 2>/dev/null; then
            kill -9 "$PID"
            echo -e "${RED}   Force killed.${NC}"
        else
            echo -e "${GREEN}   Berhasil dihentikan.${NC}"
        fi
        rm -f "$PID_FILE"
    else
        echo -e "${YELLOW}⚠️  Tidak ada benchmark yang sedang berjalan.${NC}"
        rm -f "$PID_FILE"
    fi
    exit 0
fi

# =============================================================
# DEFAULT: START benchmark di background
# =============================================================

# Validasi BENCHMARK_NAME — hanya boleh huruf kecil, angka, tanda hubung
if [[ ! "$BENCHMARK_NAME" =~ ^[a-z0-9][a-z0-9-]*[a-z0-9]$ ]]; then
    echo -e "${RED}❌ BENCHMARK_NAME tidak valid: '$BENCHMARK_NAME'${NC}"
    echo -e "   Gunakan huruf kecil, angka, dan tanda hubung saja."
    echo -e "   Contoh: 1gpu-qwen3-30b, 2gpu-loadbalance, gpu5-baseline"
    exit 1
fi

# Cek apakah sudah ada yang jalan
if is_running; then
    PID=$(cat "$PID_FILE")
    echo -e "${RED}❌ Benchmark sudah berjalan (PID: $PID).${NC}"
    echo -e "   Gunakan ${YELLOW}./run_benchmark.sh stop${NC} untuk menghentikannya dulu."
    exit 1
fi

# Cek benchmark.py ada
if [[ ! -f "$BENCHMARK_PY" ]]; then
    echo -e "${RED}❌ File tidak ditemukan: $BENCHMARK_PY${NC}"
    exit 1
fi

# Cek Python & guidellm tersedia
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}❌ python3 tidak ditemukan.${NC}"
    exit 1
fi

if ! python3 -c "import guidellm" 2>/dev/null; then
    echo -e "${RED}❌ guidellm belum terinstall. Jalankan: pip install guidellm${NC}"
    exit 1
fi

# Buat results dir
mkdir -p "$RESULTS_DIR"

# Format tanggal: 2026-07-06
TODAY=$(date +%Y-%m-%d)
FOLDER_NAME="${TODAY}-${BENCHMARK_NAME}"

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     GuideLLM Benchmark — Background Runner              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Benchmark : ${YELLOW}$BENCHMARK_NAME${NC}"
echo -e "  Folder    : ${YELLOW}results/$FOLDER_NAME/${NC}"
echo -e "  Script    : ${YELLOW}$BENCHMARK_PY${NC}"
echo -e "  nohup log : ${YELLOW}$NOHUP_LOG${NC}"
echo ""
echo -e "${YELLOW}⏱️  Estimasi: ~3-4 jam (16 level × 6 scenario × 120 detik)${NC}"
echo ""

# Pass nama folder ke Python via environment variable
# benchmark_concurrent.py akan membaca BENCHMARK_FOLDER_NAME
# untuk menentukan OUTPUT_DIR
export BENCHMARK_FOLDER_NAME="$FOLDER_NAME"

# Jalankan dengan nohup
nohup python3 -u "$BENCHMARK_PY" > "$NOHUP_LOG" 2>&1 &
BG_PID=$!

# Simpan PID
echo "$BG_PID" > "$PID_FILE"

sleep 2   # beri waktu process startup

if kill -0 "$BG_PID" 2>/dev/null; then
    echo -e "${GREEN}✅ Benchmark berhasil dijalankan di background!${NC}"
    echo ""
    echo -e "  PID       : ${YELLOW}$BG_PID${NC}"
    echo -e "  Folder    : ${YELLOW}results/$FOLDER_NAME/${NC}"
    echo -e "  Log utama : ${YELLOW}results/$FOLDER_NAME/benchmark.log${NC}"
    echo ""
    echo -e "─── Perintah monitoring ──────────────────────────────────────"
    echo -e "  ${GREEN}./run_benchmark.sh monitor${NC}   # live tail log terbaru"
    echo -e "  ${GREEN}./run_benchmark.sh status${NC}    # cek status + 10 baris terakhir"
    echo -e "  ${GREEN}./run_benchmark.sh stop${NC}      # hentikan benchmark"
    echo ""
    echo -e "  ${GREEN}tail -f $NOHUP_LOG${NC}"
    echo -e "    └── log nohup (output awal sebelum results dir dibuat)"
    echo ""
    echo -e "  ${GREEN}watch -n 5 './run_benchmark.sh status'${NC}"
    echo -e "    └── auto-refresh status setiap 5 detik"
    echo ""
    echo -e "  ${GREEN}watch -n 1 nvidia-smi${NC}"
    echo -e "    └── monitor GPU utilization di terminal lain"
    echo "─────────────────────────────────────────────────────────────"
    echo ""
else
    echo -e "${RED}❌ Proses gagal start. Cek nohup log:${NC}"
    echo ""
    cat "$NOHUP_LOG"
    rm -f "$PID_FILE"
    exit 1
fi