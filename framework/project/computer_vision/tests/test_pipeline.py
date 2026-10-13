import csv
import json

from conftest import BASE_CONFIG, FakeDetector
from zul.computer_vision.video import VideoInfo

from cctv.cli import main
from cctv.pipeline import RunOptions, run
from cctv.settings import load_scene_config


def walking_down(call: int) -> list[list[float]]:
    """Satu orang berjalan dari zona "depan" ke bawah, melintasi garis y=120."""
    foot = 40 + call * 5
    return [[150, foot - 40, 170, foot]]


def test_pipeline_writes_video_csv_and_summary(tmp_path, write_scene, fake_video):
    scene = load_scene_config(BASE_CONFIG, write_scene(fake_video))
    detector = FakeDetector(walking_down)

    summary = run(scene, detector, RunOptions(mode="save", output_dir=tmp_path / "out"))

    folder = tmp_path / "out" / "contoh"
    assert detector.calls == 40
    assert summary["frame_diproses"] == 40
    assert summary["garis"]["pintu"]["masuk"] + summary["garis"]["pintu"]["keluar"] == 1
    assert VideoInfo.from_path(folder / "annotated.mp4").total_frames == 40
    with (folder / "visits.csv").open(encoding="utf-8") as file:
        visits = list(csv.DictReader(file))
    assert [row["zone_name"] for row in visits] == ["depan"]
    assert json.loads((folder / "summary.json").read_text(encoding="utf-8")) == summary
    assert not (folder / "contacts.csv").exists()


def test_stride_and_range_process_only_part_of_the_video(
    tmp_path, write_scene, fake_video
):
    scene = load_scene_config(BASE_CONFIG, write_scene(fake_video))

    summary = run(
        scene,
        FakeDetector(lambda call: []),
        RunOptions(start=10, end=30, stride=2, output_dir=tmp_path / "out"),
    )

    assert summary["frame_diproses"] == 10


def test_cli_check_reports_the_scene_without_loading_a_model(
    write_scene, fake_video, capsys
):
    code = main(["check", str(write_scene(fake_video)), "--base", str(BASE_CONFIG)])

    report = json.loads(capsys.readouterr().out)
    assert code == 0
    assert report["zona"] == ["depan"] and report["garis"] == ["pintu"]
    assert report["video_ada"] is True


def test_cli_explains_an_invalid_config(tmp_path, capsys):
    broken = tmp_path / "rusak.yaml"
    broken.write_text("ZONES: []\n", encoding="utf-8")

    code = main(["check", str(broken), "--base", str(BASE_CONFIG)])

    assert code == 2
    assert "SOURCE_VIDEO_PATH" in capsys.readouterr().err
