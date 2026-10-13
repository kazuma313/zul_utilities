from pathlib import Path

import pytest
from conftest import BASE_CONFIG, PROJECT
from zul.computer_vision.config import ConfigError

from cctv.settings import load_scene_config


def test_example_cameras_load_with_their_geometry():
    entrance = load_scene_config(BASE_CONFIG, PROJECT / "configs" / "entrance.yaml")
    interior = load_scene_config(BASE_CONFIG, PROJECT / "configs" / "interior.yaml")

    assert entrance.name == "entrance"
    assert [zone.name for zone in entrance.zones] == ["depan_toko"]
    assert entrance.lines[0].start == (1257.0, 497.0)
    assert len(entrance.ignore_polygons) == 1
    assert entrance.settings.PROXIMITY_METRES == 2.0
    assert entrance.overrides == ("PROXIMITY_METRES",)
    assert [zone.name for zone in interior.zones] == [
        "rak_a",
        "rak_b",
        "rak_c",
        "rak_d",
    ]
    assert interior.settings.PROXIMITY_METRES == 0.0


def test_source_option_replaces_the_video_in_the_config(write_scene):
    scene = load_scene_config(BASE_CONFIG, write_scene(), source="lain.mp4")

    assert scene.source == Path("lain.mp4")


def test_unknown_setting_names_the_closest_one(tmp_path, write_scene):
    scene = write_scene()
    scene.write_text(
        scene.read_text(encoding="utf-8") + "  CONFIDENSE: 0.3\n", encoding="utf-8"
    )

    with pytest.raises(ConfigError, match="CONFIDENCE"):
        load_scene_config(BASE_CONFIG, scene)


@pytest.mark.parametrize(
    ("replace", "message"),
    [
        ("[[0, 0], [320, 0], [320, 90], [0, 90]]", None),
        ("[[0, 0], [320, 0]]", "minimal 3 titik"),
        ("[[0, 0], [320, 0], [320, true]]", "harus titik"),
    ],
)
def test_zone_polygons_are_checked(write_scene, replace, message):
    scene = write_scene()
    text = scene.read_text(encoding="utf-8")
    scene.write_text(
        text.replace("[[0, 0], [320, 0], [320, 90], [0, 90]]", replace),
        encoding="utf-8",
    )

    if message is None:
        assert load_scene_config(BASE_CONFIG, scene).zones[0].name == "depan"
    else:
        with pytest.raises(ConfigError, match=message):
            load_scene_config(BASE_CONFIG, scene)


def test_duplicate_names_and_missing_video_are_rejected(tmp_path):
    duplicate = tmp_path / "ganda.yaml"
    duplicate.write_text(
        "SOURCE_VIDEO_PATH: a.mp4\nZONES:\n"
        "  - {name: a, polygon: [[0, 0], [1, 0], [1, 1]]}\n"
        "  - {name: a, polygon: [[0, 0], [2, 0], [2, 2]]}\n",
        encoding="utf-8",
    )
    missing = tmp_path / "tanpa_video.yaml"
    missing.write_text("ZONES: []\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="lebih dari sekali: a"):
        load_scene_config(BASE_CONFIG, duplicate)
    with pytest.raises(ConfigError, match="SOURCE_VIDEO_PATH"):
        load_scene_config(BASE_CONFIG, missing)
