"""
Perintah `cctv`: menjalankan satu kamera, atau memeriksa config-nya saja.

Gunanya:
    `cctv run` memuat config, model, lalu memproses video sesuai mode.
    `cctv check` hanya memuat dan memeriksa config, tanpa model dan tanpa
    video, untuk memastikan geometri dan pengaturan benar sebelum proses
    yang lama dimulai.

Cara pakai:
    cctv run configs/entrance.yaml --mode both
    cctv run configs/interior.yaml --mode save --start 1000 --end 2500 --stride 3
    cctv check configs/entrance.yaml
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from zul.computer_vision.config import ConfigError

from .settings import SceneConfig, load_scene_config

DEFAULT_BASE = Path("configs/base.yaml")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cctv", description="Analitik video CCTV di atas Zul."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser("run", help="Proses satu kamera.")
    _add_scene_arguments(run)
    run.add_argument("--mode", choices=("live", "save", "both"), default="save")
    run.add_argument("--start", type=int, default=0, help="Frame pertama.")
    run.add_argument(
        "--end", type=int, default=None, help="Frame terakhir (tidak ikut)."
    )
    run.add_argument("--stride", type=int, default=1, help="Proses setiap frame ke-N.")
    run.add_argument("--output", type=Path, default=Path("outputs"))

    check = commands.add_parser("check", help="Periksa config tanpa memuat model.")
    _add_scene_arguments(check)
    return parser


def _add_scene_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "scene", type=Path, help="Config kamera, misalnya configs/entrance.yaml."
    )
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument(
        "--source", type=Path, default=None, help="Ganti SOURCE_VIDEO_PATH."
    )


def describe(scene: SceneConfig) -> dict:
    """Ringkasan config untuk `cctv check`."""
    return {
        "kamera": scene.name,
        "video": scene.source.as_posix(),
        "video_ada": scene.source.exists(),
        "zona": [zone.name for zone in scene.zones],
        "garis": [line.name for line in scene.lines],
        "area_diabaikan": len(scene.ignore_polygons),
        "pengaturan_ditimpa": list(scene.overrides),
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        scene = load_scene_config(args.base, args.scene, source=args.source)
    except ConfigError as error:
        print(f"Config tidak valid: {error}", file=sys.stderr)
        return 2

    if args.command == "check":
        print(json.dumps(describe(scene), indent=2, ensure_ascii=False))
        return 0

    from .detector import load_detector
    from .pipeline import RunOptions, run

    options = RunOptions(
        mode=args.mode,
        start=args.start,
        end=args.end,
        stride=args.stride,
        output_dir=args.output,
    )
    try:
        summary = run(scene, load_detector(scene.settings), options)
    except FileNotFoundError as error:
        print(error, file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0
