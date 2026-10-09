import csv
import re
from dataclasses import dataclass
from types import SimpleNamespace

import numpy as np
import pytest

from zul.computer_vision import analytics, geometry, pose
from zul.computer_vision.config import (
    ConfigError,
    changed_settings,
    load_scene,
    merge_scene,
    read_yaml,
    validate_settings,
)
from zul.computer_vision.crossing import LineCrossing
from zul.computer_vision.report import RecordWriter

# --------------------------------------------------------------------------
# Geometry
# --------------------------------------------------------------------------

CONCAVE = np.array([[10, 10], [60, 10], [60, 60], [35, 30], [10, 60]])


def test_box_anchor_ratio_sixth_lands_on_the_head():
    boxes = np.array([[100, 60, 140, 180], [0, 0, 10, 60]])

    assert geometry.box_anchors(boxes, ratio=1 / 6).tolist() == [
        [120.0, 80.0],
        [5.0, 10.0],
    ]
    assert geometry.foot_points(boxes).tolist() == [[120.0, 180.0], [5.0, 60.0]]
    assert geometry.box_heights(boxes).tolist() == [120.0, 60.0]


def test_points_in_polygon_matches_cv2_including_edges_and_vertices():
    cv2 = pytest.importorskip("cv2")
    grid = np.stack(np.meshgrid(np.arange(0, 71), np.arange(0, 71)), -1).reshape(-1, 2)
    midpoints = (CONCAVE + np.roll(CONCAVE, -1, axis=0)) / 2
    points = np.concatenate([grid, CONCAVE, midpoints]).astype(np.float64)
    contour = CONCAVE.astype(np.float32).reshape(-1, 1, 2)

    expected = [
        cv2.pointPolygonTest(contour, (float(x), float(y)), False) >= 0
        for x, y in points
    ]

    assert geometry.points_in_polygon(CONCAVE, points).tolist() == expected


def test_point_in_the_notch_of_a_concave_polygon_is_outside():
    assert not geometry.point_in_polygon(CONCAVE, (35, 50))
    assert geometry.point_in_polygon(CONCAVE, (12, 50))


def test_zone_membership_gives_overlap_to_the_first_zone():
    left = [[0, 0], [60, 0], [60, 60], [0, 60]]
    right = [[40, 0], [100, 0], [100, 60], [40, 60]]
    points = np.array([[10, 10], [50, 10], [90, 10], [200, 10]])

    membership = geometry.zone_membership([left, right], points)

    assert membership.tolist() == [0, 0, 1, -1]
    assert geometry.count_per_zone(2, membership) == [2, 1]


def test_as_polygon_list_accepts_one_polygon_or_many_and_drops_lines():
    one = [[0, 0], [10, 0], [10, 10]]

    assert len(geometry.as_polygon_list(one)) == 1
    assert len(geometry.as_polygon_list([one, one])) == 2
    assert geometry.as_polygon_list([one, [[0, 0], [5, 5]]])[0].dtype == np.int32
    assert len(geometry.as_polygon_list([one, [[0, 0], [5, 5]]])) == 1
    assert geometry.as_polygon_list(None) == []


def test_points_toward_respects_the_cone():
    assert geometry.points_toward((1, 0), (0, 0), (10, 2), cone_deg=30)
    assert not geometry.points_toward((1, 0), (0, 0), (0, 10), cone_deg=30)
    assert geometry.points_toward((1, 0), (0, 0), (0, 10), cone_deg=90)
    assert not geometry.points_toward(None, (0, 0), (10, 0))


def test_standing_on_the_target_counts_as_facing_it():
    assert geometry.points_toward((0, -1), (5, 5), (5, 5))


def test_zero_vectors_have_no_direction():
    assert geometry.unit((0, 0)) is None
    assert np.isnan(geometry.angle_between((0, 0), (1, 0)))
    assert geometry.angle_between((1, 0), (0, 1)) == pytest.approx(90.0)
    assert geometry.direction_angle((0, 1)) == pytest.approx(90.0)


# --------------------------------------------------------------------------
# Pose
# --------------------------------------------------------------------------


def person(
    left_shoulder=(120, 100),
    right_shoulder=(80, 100),
    nose=None,
    left_ear=None,
    right_ear=None,
):
    """Keypoint satu orang; bagian yang tidak diisi bernilai confidence 0."""
    xy = np.zeros((17, 2))
    conf = np.zeros(17)
    for index, point in [
        (pose.NOSE, nose),
        (pose.LEFT_EAR, left_ear),
        (pose.RIGHT_EAR, right_ear),
        (pose.LEFT_SHOULDER, left_shoulder),
        (pose.RIGHT_SHOULDER, right_shoulder),
    ]:
        if point is not None:
            xy[index], conf[index] = point, 0.9
    return xy, conf


def test_shoulders_of_a_person_facing_the_camera_point_down_the_image():
    xy, conf = person(left_shoulder=(120, 100), right_shoulder=(80, 100))

    direction, source = pose.facing_direction(xy, conf)

    assert source == "body"
    assert direction.tolist() == pytest.approx([0.0, 1.0])


def test_shoulders_of_a_person_with_their_back_to_the_camera_point_up():
    xy, conf = person(left_shoulder=(80, 100), right_shoulder=(120, 100))

    direction, _ = pose.facing_direction(xy, conf)

    assert direction.tolist() == pytest.approx([0.0, -1.0])


def test_head_direction_wins_over_shoulders_when_the_face_is_visible():
    xy, conf = person(nose=(110, 80), left_ear=(95, 80))

    direction, source = pose.facing_direction(xy, conf)

    assert source == "head"
    assert direction.tolist() == pytest.approx([1.0, 0.0])


def test_narrow_shoulders_from_the_side_give_no_direction():
    xy, conf = person(left_shoulder=(100, 100), right_shoulder=(102, 100))

    assert pose.facing_direction(xy, conf) == (None, "")


def test_facing_directions_accepts_a_frame_without_people():
    assert pose.facing_directions(None, None) == ([], [])


def test_facing_zone_targets_needs_the_zone_and_the_direction():
    boxes = np.array([[80, 100, 120, 220]] * 3)
    down, up = np.array([0.0, 1.0]), np.array([0.0, -1.0])
    targets = [np.array([100.0, 300.0])]

    flags = pose.facing_zone_targets(boxes, [down, up, down], [0, 0, -1], targets)

    assert flags == [True, False, False]


def test_poses_pair_with_the_box_that_holds_their_nose():
    boxes = np.array([[0, 0, 50, 100], [100, 0, 150, 100]])
    first, _ = person(nose=(120, 20))
    second, _ = person(nose=(30, 20))

    pairing = pose.match_poses_to_boxes(boxes, np.stack([first, second]))

    assert pairing == {0: 1, 1: 0}
    assert pose.by_box(pairing, ["a", "b"], 3) == ["b", "a", None]


# --------------------------------------------------------------------------
# Lintasan Garis
# --------------------------------------------------------------------------


def walk(line, track_id, ys, x=50.0):
    """Jalankan satu track melewati `ys`; kembalikan daftar (masuk, keluar)."""
    return [line.update([track_id], np.array([[x, y]])) for y in ys]


def test_crossing_counts_once_after_minimum_frames_on_the_new_side():
    line = LineCrossing((0, 0), (100, 0), minimum_frames=3)

    steps = walk(line, 1, [10, -10, -10, -10, -10])

    assert [crossed_in[0] for crossed_in, _ in steps] == [
        False,
        False,
        False,
        True,
        False,
    ]
    assert (line.in_count, line.out_count) == (1, 0)


def test_crossing_ignores_a_box_jittering_on_the_line():
    line = LineCrossing((0, 0), (100, 0), minimum_frames=3)

    walk(line, 1, [10, -10, 10, -10, 10, -10, 10, -10])

    assert (line.in_count, line.out_count) == (0, 0)


def test_crossing_ignores_people_beside_the_segment():
    line = LineCrossing((0, 0), (100, 0), minimum_frames=1)

    walk(line, 1, [10, -10, -10], x=150)

    assert line.in_count == 0


def test_swapping_line_points_swaps_in_and_out():
    line = LineCrossing((100, 0), (0, 0), minimum_frames=1)

    walk(line, 1, [10, -10])

    assert (line.in_count, line.out_count) == (0, 1)
    assert line.midpoint.tolist() == [50.0, 0.0]


# --------------------------------------------------------------------------
# Kunjungan Zona
# --------------------------------------------------------------------------


def test_short_gap_keeps_one_visit_and_long_gap_starts_another():
    visits = analytics.ZoneVisitTracker(["rak"], grace_s=1.0)
    seen = {0.0, 0.25, 0.5, 1.0, 1.25, 3.0, 3.25}

    for step in range(15):
        t = step * 0.25
        visits.update(step, t, [4] if t in seen else [], [0] if t in seen else [])
    visits.close_all()

    assert [(v.enter_time_s, v.exit_time_s) for v in visits.completed] == [
        (0.0, 1.25),
        (3.0, 3.25),
    ]
    assert visits.visit_count(0) == 2
    assert visits.unique_visitors(0) == 1


def test_moving_to_another_zone_closes_the_visit_at_once():
    visits = analytics.ZoneVisitTracker(["a", "b"], grace_s=5.0)

    visits.update(0, 0.0, [4], [0])
    closed = visits.update(1, 0.5, [4], [1])

    assert [v.zone_name for v in closed] == ["a"]
    assert visits.zone_of(4) == 1


# --------------------------------------------------------------------------
# Perhatian Ke Zona
# --------------------------------------------------------------------------


def run_attention(tracker, frames):
    """`frames`: daftar (detik, membership, looking) untuk track 1."""
    closed = []
    for number, (t, zone, looking) in enumerate(frames):
        closed += tracker.update(number, t, [1], [zone], [looking])
    return closed + tracker.close_all()


def test_looking_at_the_shelf_long_enough_is_attention():
    tracker = analytics.AttentionTracker(["rak"], minimum_s=1.0, frame_period_s=0.25)

    (spell,) = run_attention(tracker, [(i * 0.25, 0, True) for i in range(5)])

    assert spell.looking_s == pytest.approx(1.0)
    assert spell.span_s == pytest.approx(1.0)


def test_a_face_outside_the_zone_earns_nothing():
    tracker = analytics.AttentionTracker(["rak"], minimum_s=1.0, frame_period_s=0.25)

    assert run_attention(tracker, [(i * 0.25, -1, True) for i in range(20)]) == []


def test_standing_in_the_zone_without_looking_is_not_attention():
    tracker = analytics.AttentionTracker(["rak"], minimum_s=1.0, frame_period_s=0.25)

    assert run_attention(tracker, [(i * 0.25, 0, False) for i in range(20)]) == []


def test_a_glance_shorter_than_the_threshold_is_not_attention():
    tracker = analytics.AttentionTracker(["rak"], minimum_s=3.0, frame_period_s=0.25)

    assert run_attention(tracker, [(i * 0.25, 0, True) for i in range(8)]) == []


def test_a_gap_inside_grace_earns_only_the_credit_cap():
    tracker = analytics.AttentionTracker(
        ["rak"], minimum_s=3.0, grace_s=1.0, frame_period_s=0.1
    )

    tracker.update(0, 0.0, [1], [0], [True])
    tracker.update(9, 0.9, [1], [0], [True])

    assert tracker.credit_cap_s == pytest.approx(0.2)
    assert tracker.looking_s(1, 0) == pytest.approx(0.2)


def test_an_empty_frame_after_grace_closes_the_spell():
    tracker = analytics.AttentionTracker(["rak"], minimum_s=1.0, frame_period_s=0.25)
    for i in range(5):
        tracker.update(i, i * 0.25, [1], [0], [True])

    assert tracker.update(10, 2.5, None, [], []) != []
    assert tracker.people(0) == 1


def test_credit_cap_follows_the_threshold():
    assert analytics.credit_cap(1 / 30, 3.0, 2, 0.25) == pytest.approx(2 / 30)
    assert analytics.credit_cap(1.0, 0.5, 2, 0.25) == pytest.approx(0.125)


# --------------------------------------------------------------------------
# Kontak Antar Kelompok
# --------------------------------------------------------------------------


def test_proximity_is_measured_in_metres_from_box_height():
    boxes = np.array([[0, 0, 50, 170], [150, 0, 200, 170], [400, 0, 450, 170]])

    pairs = analytics.proximity_pairs(boxes, [True, False, False])

    assert [(s, o) for s, o, _ in pairs] == [(0, 1)]
    assert pairs[0][2] == pytest.approx(1.5)
    assert analytics.proximity_pairs(boxes, [False] * 3) == []
    assert (
        analytics.proximity_pairs(boxes, [True, False, False], exclude=[0, 1, 0]) == []
    )


def test_sixty_frames_close_together_are_one_contact():
    log = analytics.ProximityLog(minimum_s=1.0, grace_s=1.0)

    for frame in range(60):
        log.update(frame, frame / 30, [7, 9], [(0, 1, 1.2)])
    (contact,) = log.close_all()

    assert (contact.subject_id, contact.other_id) == (7, 9)
    assert contact.duration_s == pytest.approx(59 / 30)


def test_subjects_without_contact_stay_in_the_average():
    log = analytics.ProximityLog(minimum_s=0.0)
    log.note_subjects([7, 8, 9], [True, True, False], 0.0)

    log.update(0, 0.0, [7, 8, 9], [(0, 2, 1.0)])
    log.close_all()

    assert log.contacts_per_subject() == {7: 1, 8: 0}
    assert log.idle_subjects() == [8]
    assert log.average_contacts() == pytest.approx(0.5)


# --------------------------------------------------------------------------
# Minat Dan Konversi
# --------------------------------------------------------------------------


def test_interest_qualifies_then_upgrades_to_entered_and_stays():
    interest = analytics.InterestTracker(threshold_s=1.0, frame_period_s=0.25)

    newly = [interest.update(i, i * 0.25, [3], [True]) for i in range(5)]
    assert newly[-1] == [3]
    assert interest.outcome_of(3) == interest.PASSED_BY

    interest.mark_crossed([3], 6, 1.5)
    interest.update(7, 1.75, [3], [False])

    assert interest.outcome_of(3) == interest.ENTERED
    assert (interest.counts().entered, interest.counts().passed_by) == (1, 0)
    (record,) = interest.records()
    assert (record.qualified_time_s, record.crossed_time_s) == (1.0, 1.5)


def test_a_glance_is_not_interest():
    interest = analytics.InterestTracker(threshold_s=1.0, frame_period_s=0.25)

    for i in range(3):
        interest.update(i, i * 0.25, [3], [True])

    assert interest.outcome_of(3) is None
    assert interest.records() == []
    assert interest.counts().total == 0


def test_interest_needs_the_zone_and_the_facing_test():
    interest = analytics.InterestTracker(threshold_s=1.0, frame_period_s=0.25)

    for i in range(10):
        interest.update(i, i * 0.25, [1, 2], [True, True], [False, True], [True, False])

    assert interest.looking_s(1) == 0.0
    assert interest.looking_s(2) == 0.0


def test_interest_after_a_long_gap_earns_only_the_credit_cap():
    interest = analytics.InterestTracker(threshold_s=1.0, frame_period_s=0.25)

    interest.update(0, 0.0, [3], [True])
    interest.update(1, 5.0, [3], [True])

    assert interest.looking_s(3) == pytest.approx(0.25)


# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Rules:
    CONFIDENCE: float
    FACING_CONE_DEG: float


def test_scene_settings_merge_by_name_and_list_overrides(tmp_path):
    (tmp_path / "base.yaml").write_text(
        "settings:\n  CONFIDENCE: 0.2\n  FACING_CONE_DEG: 90\n", encoding="utf-8"
    )
    (tmp_path / "toko.yaml").write_text(
        "settings:\n  CONFIDENCE: 0.3\nPOLYGON_LABELS: [rak_a]\n", encoding="utf-8"
    )

    scene = load_scene(tmp_path / "base.yaml", tmp_path / "toko.yaml")

    assert scene["settings"] == {"CONFIDENCE": 0.3, "FACING_CONE_DEG": 90}
    assert scene["overrides"] == ["CONFIDENCE"]
    assert scene["POLYGON_LABELS"] == ["rak_a"]


def test_validate_settings_turns_int_into_float():
    values = validate_settings({"CONFIDENCE": 0.2, "FACING_CONE_DEG": 90}, Rules)

    assert values == {"CONFIDENCE": 0.2, "FACING_CONE_DEG": 90.0}
    assert isinstance(values["FACING_CONE_DEG"], float)


@pytest.mark.parametrize(
    ("settings", "message"),
    [
        ({"CONFIDENSE": 0.2, "FACING_CONE_DEG": 90}, "maksudnya CONFIDENCE?"),
        ({"CONFIDENCE": 0.2}, "FACING_CONE_DEG (Rules)"),
        ({"CONFIDENCE": "tinggi", "FACING_CONE_DEG": 90}, "harus float"),
        ({"CONFIDENCE": True, "FACING_CONE_DEG": 90}, "bukan bool"),
    ],
)
def test_validate_settings_explains_what_is_wrong(settings, message):
    with pytest.raises(ConfigError, match=re.escape(message)):
        validate_settings(settings, Rules)


def test_read_yaml_reports_the_line_of_broken_yaml(tmp_path):
    broken = tmp_path / "rusak.yaml"
    broken.write_text("settings:\n  A: [1, 2\n", encoding="utf-8")
    listing = tmp_path / "list.yaml"
    listing.write_text("- a\n- b\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="baris"):
        read_yaml(broken)
    with pytest.raises(ConfigError, match="mapping"):
        read_yaml(listing)
    assert read_yaml(tmp_path / "tidak_ada.yaml") == {}


def test_merge_and_changed_settings_report_differences():
    merged = merge_scene({"settings": {"A": 1, "B": 2}}, {"settings": {"B": 3}})

    assert merged["overrides"] == ["B"]
    assert changed_settings({"A": 1, "B": 2}, merged["settings"]) == ["B: 2 -> 3"]


# --------------------------------------------------------------------------
# CSV
# --------------------------------------------------------------------------


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.reader(handle))


def test_record_writer_writes_fields_properties_and_rounds_floats(tmp_path):
    spell = analytics.Attention(1, 4, 0, "rak", 10, 1.0, 40, 4.123456, 2.0004)
    path = tmp_path / "out" / "attention.csv"

    with RecordWriter(path, ["attention_id", "zone_name", "looking_s", "span_s"]) as w:
        w.write([spell])

    assert read_rows(path) == [
        ["attention_id", "zone_name", "looking_s", "span_s"],
        ["1", "rak", "2.0", "3.123"],
    ]


def test_record_writer_takes_columns_from_a_dataclass_and_blanks_none(tmp_path):
    record = analytics.InterestRecord(3, "passed_by", 30, 1.0, None, None)
    path = tmp_path / "interest.csv"

    with RecordWriter(path, analytics.InterestRecord) as writer:
        writer.write([record])

    assert read_rows(path)[1] == ["3", "passed_by", "30", "1.0", "", ""]


def test_record_writer_leaves_a_header_when_nothing_happened(tmp_path):
    path = tmp_path / "kosong.csv"

    with RecordWriter(path, ["a", "b"]) as writer:
        writer.write([])

    assert read_rows(path) == [["a", "b"]]
    with pytest.raises(RuntimeError):
        RecordWriter(path, ["a"]).write([])


# --------------------------------------------------------------------------
# Gambar Dan Masker (zul[vision])
# --------------------------------------------------------------------------


def test_polygon_mask_keeps_or_blacks_out_the_inside():
    pytest.importorskip("cv2")
    from zul.computer_vision import draw

    square = [[10, 10], [30, 10], [30, 30], [10, 30]]
    keep = draw.polygon_mask([square], 40, 40, keep_inside=True)
    drop = draw.polygon_mask([square], 40, 40)
    image = np.full((40, 40, 3), 200, dtype=np.uint8)

    assert (keep[20, 20, 0], keep[0, 0, 0]) == (255, 0)
    assert (drop[20, 20, 0], drop[0, 0, 0]) == (0, 255)
    assert draw.apply_mask(image, keep)[0, 0, 0] == 0
    assert draw.apply_mask(image, None) is image
    assert draw.combine_masks(None, None) is None
    assert draw.combine_masks(keep, drop).max() == 0


def test_colours_are_stable_per_track_and_parse_hex():
    pytest.importorskip("cv2")
    from zul.computer_vision import draw

    assert draw.bgr("#FF8000") == (0, 128, 255)
    assert draw.track_color(5) == draw.track_color(5)
    assert draw.track_color(1) != draw.track_color(2)


def test_skeleton_skips_hidden_keypoints_and_empty_frames():
    pytest.importorskip("cv2")
    from zul.computer_vision import draw

    scene = np.zeros((200, 200, 3), dtype=np.uint8)
    xy, conf = person()

    assert draw.draw_skeleton(scene, None) is scene
    draw.draw_skeleton(scene, xy[None], conf[None])
    assert scene[0, 0].tolist() == [0, 0, 0]
    assert scene[100, 100].any()


# --------------------------------------------------------------------------
# Video (zul[vision])
# --------------------------------------------------------------------------


def test_video_round_trip_keeps_frame_numbers_and_seconds(tmp_path):
    pytest.importorskip("cv2")
    from zul.computer_vision.video import VideoInfo, VideoWriter, read_frames

    path = tmp_path / "klip.mp4"
    with VideoWriter(path, VideoInfo(64, 48, 10.0, 12)) as writer:
        for i in range(12):
            writer.write(np.full((48, 64, 3), i * 20, dtype=np.uint8))

    info = VideoInfo.from_path(path)
    frames = list(read_frames(path, start=2, end=10, stride=3))

    assert (info.width, info.height, info.fps, info.total_frames) == (64, 48, 10, 12)
    assert [number for number, _, _ in frames] == [2, 5, 8]
    assert [t for _, t, _ in frames] == pytest.approx([0.2, 0.5, 0.8])
    assert [round(frame.mean() / 20) for _, _, frame in frames] == [2, 5, 8]


def test_video_slice_divides_fps_by_stride():
    pytest.importorskip("cv2")
    from zul.computer_vision.video import VideoInfo

    sliced = VideoInfo(1280, 720, 30.0, 9000).slice(1000, 2500, 3)

    assert (sliced.fps, sliced.total_frames) == (10.0, 500)


# --------------------------------------------------------------------------
# Deteksi Dan Tracking (zul[yolo])
# --------------------------------------------------------------------------


class FakeTensor:
    """Pengganti tensor torch: cukup `.cpu().numpy()` dan `len`."""

    def __init__(self, values):
        self.values = np.asarray(values, dtype=np.float64)

    def __len__(self):
        return len(self.values)

    def cpu(self):
        return self

    def numpy(self):
        return self.values


def detections_with_keypoints(boxes):
    """Deteksi dengan keypoint di tengah setiap kotak, untuk memeriksa urutan."""
    from zul.computer_vision.detection import Detections

    boxes = np.asarray(boxes, dtype=np.float64)
    centres = geometry.box_anchors(boxes)
    return Detections(
        xyxy=boxes,
        confidence=np.full(len(boxes), 0.9),
        class_id=np.zeros(len(boxes), dtype=int),
        keypoints_xy=np.repeat(centres[:, None, :], 17, axis=1),
        keypoints_conf=np.ones((len(boxes), 17)),
    )


def test_detections_slice_and_rescale_every_column_together():
    pytest.importorskip("cv2")

    people = detections_with_keypoints([[0, 0, 10, 20], [100, 0, 110, 20]])
    second = people[np.array([False, True])]
    doubled = second.rescale(0.5)

    assert len(second) == 1
    assert second.keypoints_xy[0, 0].tolist() == [105.0, 10.0]
    assert doubled.xyxy.tolist() == [[200.0, 0.0, 220.0, 40.0]]
    assert doubled.keypoints_xy[0, 0].tolist() == [210.0, 20.0]
    assert people.rescale(1.0) is people


def test_detections_from_an_ultralytics_result_without_torch():
    pytest.importorskip("cv2")
    from zul.computer_vision.detection import Detections

    class Boxes:
        xyxy = FakeTensor([[1, 2, 3, 4]])
        conf = FakeTensor([0.8])
        cls = FakeTensor([0])

        def __len__(self):
            return 1

    keypoints = SimpleNamespace(xy=FakeTensor(np.ones((1, 17, 2))), conf=None)
    result = SimpleNamespace(boxes=Boxes(), keypoints=keypoints)

    people = Detections.from_ultralytics(result)

    assert people.xyxy.tolist() == [[1.0, 2.0, 3.0, 4.0]]
    assert people.keypoints_xy.shape == (1, 17, 2)
    assert people.keypoints_conf is None
    assert len(Detections.from_ultralytics(SimpleNamespace(boxes=None))) == 0


def test_standardise_frame_shrinks_the_long_side_only():
    pytest.importorskip("cv2")
    from zul.computer_vision.detection import standardise_frame

    big, scale = standardise_frame(np.zeros((720, 1280, 3), dtype=np.uint8))
    small = np.zeros((100, 200, 3), dtype=np.uint8)

    assert (big.shape[:2], scale) == ((360, 640), 0.5)
    assert standardise_frame(small) == (small, 1.0)


def test_byte_tracker_keeps_ids_and_keypoints_with_their_boxes():
    pytest.importorskip("ultralytics")
    from zul.computer_vision.detection import ByteTracker

    tracker = ByteTracker(frame_rate=10)
    ids_by_x = []
    for step in range(6):
        boxes = [[10 + 4 * step, 50, 60 + 4 * step, 200], [300, 40, 350, 190]]
        if step % 2:
            boxes.reverse()
        people = tracker.update(detections_with_keypoints(boxes))
        centres = people.keypoints_xy[:, 0, 0]
        inside = (people.xyxy[:, 0] <= centres) & (centres <= people.xyxy[:, 2])

        assert len(people) == 2
        assert inside.all()
        ids_by_x.append(
            dict(zip(people.xyxy[:, 0] > 200, people.tracker_id, strict=True))
        )

    assert all(ids == ids_by_x[0] for ids in ids_by_x)


def test_byte_tracker_returns_an_empty_frame_with_ids():
    pytest.importorskip("ultralytics")
    from zul.computer_vision.detection import ByteTracker, Detections

    people = ByteTracker().update(Detections())

    assert len(people) == 0
    assert people.tracker_id is not None


def test_yolo_world_without_clip_stops_with_install_hint():
    pytest.importorskip("ultralytics")
    import importlib.util

    if importlib.util.find_spec("clip") is not None:
        pytest.skip("CLIP ter-install")
    from zul.computer_vision.detection import load_model

    with pytest.raises(ImportError, match="CLIP"):
        load_model("yolov8l-worldv2.pt", prompts=["person"])


def test_fetch_without_download_only_checks(tmp_path):
    from zul.computer_vision.weights import fetch

    present = tmp_path / "model.pt"
    present.write_bytes(b"0" * 10)

    assert fetch(tmp_path / "tidak_ada.pt", download=False) == (False, "belum ada")
    assert fetch(present)[0] is True
