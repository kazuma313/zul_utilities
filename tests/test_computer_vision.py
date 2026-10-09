import csv
import re
from dataclasses import dataclass
from types import SimpleNamespace

import numpy as np
import pytest

from zul.computer_vision import geometry, pose
from zul.computer_vision.config import (
    ConfigError,
    changed_settings,
    load_scene,
    merge_scene,
    read_yaml,
    validate_settings,
)
from zul.computer_vision.distance import (
    PairTimer,
    distance_m,
    pairs_within,
    pixels_per_metre,
)
from zul.computer_vision.report import RecordWriter
from zul.computer_vision.timers import ConditionTimer, Spell, ZoneTimer, credit_cap
from zul.computer_vision.zones import LineCounter, PolygonZone

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
# Poligon Penghitung
# --------------------------------------------------------------------------

SQUARE = [[0, 0], [100, 0], [100, 100], [0, 100]]


def test_polygon_zone_counts_now_and_unique_ids_over_time():
    zone = PolygonZone(SQUARE, "rak")

    zone.update(np.array([[10, 10], [50, 50], [200, 200]]), [1, 2, 3])
    inside = zone.update(np.array([[10, 10], [300, 300]]), [1, 4])

    assert inside.tolist() == [True, False]
    assert (zone.current_count, zone.total_count) == (1, 2)
    assert zone.centroid.tolist() == [50.0, 50.0]


def test_polygon_zone_without_ids_counts_only_the_current_frame():
    zone = PolygonZone(SQUARE)

    zone.update(np.array([[10, 10], [20, 20]]))

    assert (zone.current_count, zone.total_count) == (2, 0)


def test_polygon_zone_needs_three_points():
    with pytest.raises(ValueError):
        PolygonZone([[0, 0], [10, 10]])


# --------------------------------------------------------------------------
# Garis Penghitung
# --------------------------------------------------------------------------


def walk(line, track_id, ys, x=50.0):
    """Jalankan satu track melewati `ys`; kembalikan daftar (masuk, keluar)."""
    return [line.update(np.array([[x, y]]), [track_id]) for y in ys]


def test_line_counts_once_after_minimum_frames_on_the_new_side():
    line = LineCounter((0, 0), (100, 0), minimum_frames=3)

    steps = walk(line, 1, [10, -10, -10, -10, -10])

    assert [crossed_in[0] for crossed_in, _ in steps] == [
        False,
        False,
        False,
        True,
        False,
    ]
    assert (line.in_count, line.out_count) == (1, 0)


def test_line_ignores_a_box_jittering_on_the_line():
    line = LineCounter((0, 0), (100, 0), minimum_frames=3)

    walk(line, 1, [10, -10, 10, -10, 10, -10, 10, -10])

    assert (line.in_count, line.out_count) == (0, 0)


def test_line_ignores_people_beside_the_segment():
    line = LineCounter((0, 0), (100, 0), minimum_frames=1)

    walk(line, 1, [10, -10, -10], x=150)

    assert line.in_count == 0


def test_swapping_line_points_swaps_in_and_out():
    line = LineCounter((100, 0), (0, 0), minimum_frames=1)

    walk(line, 1, [10, -10])

    assert (line.in_count, line.out_count) == (0, 1)
    assert line.midpoint.tolist() == [50.0, 0.0]


def test_in_normal_points_to_the_in_side():
    line = LineCounter((0, 0), (100, 0))
    probe = line.midpoint + line.in_normal * 10

    assert line.sides(probe)[0].tolist() == [True]


def test_line_without_ids_counts_nothing():
    line = LineCounter((0, 0), (100, 0))

    assert line.update(np.array([[50, 10]]), None) == ([False], [False])
    with pytest.raises(ValueError):
        LineCounter((5, 5), (5, 5))


# --------------------------------------------------------------------------
# Timer Zona
# --------------------------------------------------------------------------


def test_short_gap_keeps_one_visit_and_long_gap_starts_another():
    visits = ZoneTimer(["rak"], grace_s=1.0)
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
    visits = ZoneTimer(["a", "b"], grace_s=5.0)

    visits.update(0, 0.0, [4], [0])
    closed = visits.update(1, 0.5, [4], [1])

    assert [v.zone_name for v in closed] == ["a"]
    assert visits.zone_of(4) == 1
    assert visits.dwell_s(4, 1.5) == pytest.approx(1.0)


# --------------------------------------------------------------------------
# Timer Kondisi
# --------------------------------------------------------------------------


def run_condition(timer, frames, groups=True):
    """`frames`: daftar (detik, grup, aktif) untuk track 1."""
    closed = []
    for number, (t, group, active) in enumerate(frames):
        closed += timer.update(
            number, t, [1], [active], groups=[group] if groups else None
        )
    return closed + timer.close_all()


def test_condition_true_long_enough_is_recorded():
    timer = ConditionTimer(minimum_s=1.0, frame_period_s=0.25, group_labels=["rak"])

    (spell,) = run_condition(timer, [(i * 0.25, 0, True) for i in range(5)])

    assert (spell.group, spell.group_name) == (0, "rak")
    assert spell.active_s == pytest.approx(1.0)
    assert spell.span_s == pytest.approx(1.0)


def test_rows_outside_every_group_earn_nothing():
    timer = ConditionTimer(minimum_s=1.0, frame_period_s=0.25)

    assert run_condition(timer, [(i * 0.25, -1, True) for i in range(20)]) == []


def test_presence_without_the_condition_is_not_recorded():
    timer = ConditionTimer(minimum_s=1.0, frame_period_s=0.25)

    assert run_condition(timer, [(i * 0.25, 0, False) for i in range(20)]) == []


def test_a_condition_shorter_than_the_minimum_is_not_recorded():
    timer = ConditionTimer(minimum_s=3.0, frame_period_s=0.25)

    assert run_condition(timer, [(i * 0.25, 0, True) for i in range(8)]) == []


def test_without_groups_one_spell_per_track():
    timer = ConditionTimer(minimum_s=1.0, frame_period_s=0.25)

    frames = [(i * 0.25, 0, True) for i in range(5)]
    (spell,) = run_condition(timer, frames, groups=False)

    assert (spell.group, spell.group_name) == (None, "")


def test_a_gap_inside_grace_earns_only_the_credit_cap():
    timer = ConditionTimer(minimum_s=3.0, grace_s=1.0, frame_period_s=0.1)

    timer.update(0, 0.0, [1], [True], groups=[0])
    timer.update(9, 0.9, [1], [True], groups=[0])

    assert timer.credit_cap_s == pytest.approx(0.2)
    assert timer.active_s(1, 0) == pytest.approx(0.2)


def test_an_empty_frame_after_grace_closes_the_spell():
    timer = ConditionTimer(minimum_s=1.0, frame_period_s=0.25)
    for i in range(5):
        timer.update(i, i * 0.25, [1], [True], groups=[0])

    assert timer.reached(1, 0)
    assert timer.update(10, 2.5, None, []) != []
    assert (timer.count(0), timer.people(0), timer.qualified()) == (1, 1, 1)
    assert timer.seconds(0) == pytest.approx(1.0)


def test_credit_cap_follows_the_threshold():
    assert credit_cap(1 / 30, 3.0, 2, 0.25) == pytest.approx(2 / 30)
    assert credit_cap(1.0, 0.5, 2, 0.25) == pytest.approx(0.125)


# --------------------------------------------------------------------------
# Jarak Dalam Meter
# --------------------------------------------------------------------------

PEOPLE = np.array([[0, 0, 50, 170], [150, 0, 200, 170], [400, 0, 450, 170]])


def test_distance_is_measured_in_metres_from_box_height():
    assert distance_m(PEOPLE[0], PEOPLE[1]) == pytest.approx(1.5)
    assert pixels_per_metre(PEOPLE).tolist() == pytest.approx([100.0] * 3)
    assert np.isnan(distance_m([0, 0, 10, 0], [5, 0, 15, 0]))


def test_pairs_within_counts_each_pair_once_without_groups():
    pairs = pairs_within(PEOPLE, max_distance_m=2.6)

    assert [(a, b) for a, b, _ in pairs] == [(0, 1), (1, 2)]


def test_pairs_within_keeps_group_order():
    pairs = pairs_within(PEOPLE, first=[False, True, False], second=[True, False, True])

    assert [(a, b) for a, b, _ in pairs] == [(1, 0)]
    assert pairs[0][2] == pytest.approx(1.5)


def test_sixty_frames_close_together_are_one_contact():
    contacts = PairTimer(minimum_s=1.0, grace_s=1.0)

    for frame in range(60):
        rows = [(0, 1, 1.2)] if frame % 2 else [(1, 0, 1.0)]
        contacts.update(frame, frame / 30, [7, 9], rows)
    (contact,) = contacts.close_all()

    assert (contact.first_id, contact.second_id) == (7, 9)
    assert contact.duration_s == pytest.approx(59 / 30)
    assert contact.closest_m == pytest.approx(1.0)
    assert contacts.contacts_per_track() == {7: 1, 9: 1}


def test_ordered_pairs_keep_who_is_first():
    contacts = PairTimer(minimum_s=0.0, ordered=True)

    contacts.update(0, 0.0, [7, 9], [(1, 0, 1.0)])
    (contact,) = contacts.close_all()

    assert (contact.first_id, contact.second_id) == (9, 7)


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
    spell = Spell(1, 4, 0, "rak", 10, 1.0, 40, 4.123456, 2.0004)
    path = tmp_path / "out" / "spells.csv"

    with RecordWriter(path, ["spell_id", "group_name", "active_s", "span_s"]) as w:
        w.write([spell])

    assert read_rows(path) == [
        ["spell_id", "group_name", "active_s", "span_s"],
        ["1", "rak", "2.0", "3.123"],
    ]


def test_record_writer_takes_columns_from_a_dataclass_and_blanks_none(tmp_path):
    spell = Spell(2, 5, None, "", 0, 0.0, 9, 0.9, 0.5)
    path = tmp_path / "spells.csv"

    with RecordWriter(path, Spell) as writer:
        writer.write([spell])

    assert read_rows(path)[0][:3] == ["spell_id", "track_id", "group"]
    assert read_rows(path)[1][:4] == ["2", "5", "", ""]


def test_record_writer_leaves_a_header_when_nothing_happened(tmp_path):
    path = tmp_path / "kosong.csv"

    with RecordWriter(path, ["a", "b"]) as writer:
        writer.write([])

    assert read_rows(path) == [["a", "b"]]
    with pytest.raises(RuntimeError):
        RecordWriter(path, ["a"]).write([])


# --------------------------------------------------------------------------
# Gambar (zul[vision])
# --------------------------------------------------------------------------


@pytest.fixture
def draw():
    pytest.importorskip("cv2")
    from zul.computer_vision import draw

    return draw


def blank(width=200, height=120):
    return np.zeros((height, width, 3), dtype=np.uint8)


def test_colours_are_stable_per_track_and_parse_hex(draw):
    assert draw.bgr("#FF8000") == (0, 128, 255)
    assert draw.track_color(5) == draw.track_color(5)
    assert draw.track_color(1) != draw.track_color(2)


def test_corner_text_sticks_to_the_chosen_corner(draw):
    left = draw.draw_corner_text(blank(), ["kiri"])
    right = draw.draw_corner_text(blank(), ["kanan"], corner=draw.Corner.TOP_RIGHT)
    bottom = draw.draw_corner_text(blank(), ["bawah"], corner=draw.Corner.BOTTOM_LEFT)

    assert left[:60, :100].any() and not left[:, 100:].any()
    assert right[:60, 100:].any() and not right[:, :100].any()
    assert bottom[60:, :100].any() and not bottom[:60].any()


def test_skeleton_skips_hidden_keypoints_and_empty_frames(draw):
    scene = np.zeros((200, 200, 3), dtype=np.uint8)
    xy, conf = person()

    assert draw.draw_skeleton(scene, None) is scene
    draw.draw_skeleton(scene, xy[None], conf[None])
    assert scene[0, 0].tolist() == [0, 0, 0]
    assert scene[100, 100].any()


def test_line_counter_draws_the_line_and_its_counts(draw):
    line = LineCounter((20, 60), (180, 60))
    walk(line, 1, [80, 40, 40, 40, 40], x=100)
    scene = blank()

    draw.draw_line_counter(scene, line)

    assert line.in_count == 1
    assert scene[60, 25].any()
    assert scene[61:, 60:140].any(), "keterangan di sisi keluar, di bawah garis"
    assert scene[30:58, 100].any(), "panah ke sisi masuk, di atas garis"


def test_polygon_zone_draws_its_count_in_the_middle(draw):
    zone = PolygonZone([[20, 20], [180, 20], [180, 100], [20, 100]], "rak")
    zone.update(np.array([[50, 50]]), [3])
    scene = blank()

    draw.draw_polygon_zone(scene, zone)

    assert scene[20, 100].any()
    assert scene[60, 100].any()
    assert scene[0, 0].tolist() == [0, 0, 0]


def test_trace_keeps_recent_points_and_forgets_lost_tracks(draw):
    trace = draw.TrackTrace(length=3)
    for x in (10, 20, 30, 40):
        trace.update(np.array([[x, 50]]), [1])
    scene = draw.draw_traces(blank(), trace)

    assert list(trace.paths[1]) == [(20.0, 50.0), (30.0, 50.0), (40.0, 50.0)]
    assert scene[50, 25].any() and not scene[50, 12].any()
    for _ in range(3):
        trace.update(np.empty((0, 2)), [])
    assert trace.paths == {}


def test_heatmap_marks_where_people_stood(draw):
    heat = draw.HeatMap(200, 120, radius=10)
    for _ in range(5):
        heat.update(np.array([[50, 60]]))
    heat.update(np.array([[150, 60]]))
    scene = draw.draw_heatmap(blank(), heat)

    assert heat.values[60, 50] == 5 and heat.values[60, 150] == 1
    assert scene[60, 50].any() and not scene[5, 5].any()
    assert draw.draw_heatmap(blank(), draw.HeatMap(10, 10)).max() == 0


# --------------------------------------------------------------------------
# Masker, Blur, Dan Pixelate (zul[vision])
# --------------------------------------------------------------------------


@pytest.fixture
def masks():
    pytest.importorskip("cv2")
    from zul.computer_vision import masks

    return masks


def test_polygon_mask_keeps_or_blacks_out_the_inside(masks):
    square = [[10, 10], [30, 10], [30, 30], [10, 30]]
    keep = masks.polygon_mask([square], 40, 40, keep_inside=True)
    drop = masks.polygon_mask([square], 40, 40)
    image = np.full((40, 40, 3), 200, dtype=np.uint8)

    assert (keep[20, 20, 0], keep[0, 0, 0]) == (255, 0)
    assert (drop[20, 20, 0], drop[0, 0, 0]) == (0, 255)
    assert masks.apply_mask(image, keep)[0, 0, 0] == 0
    assert masks.apply_mask(image, None) is image
    assert masks.combine_masks(None, None) is None
    assert masks.combine_masks(keep, drop).max() == 0


def checkerboard():
    cells = (np.indices((40, 40)).sum(axis=0) % 2) * 255
    return np.repeat(cells[:, :, None], 3, axis=2).astype(np.uint8)


def test_blur_changes_only_inside_the_box(masks):
    scene = checkerboard()
    original = scene.copy()

    masks.blur_boxes(scene, np.array([[10, 10, 30, 30], [35, 35, 90, 90]]))

    assert scene[20, 20].tolist() != original[20, 20].tolist()
    assert np.array_equal(scene[:10], original[:10])
    assert np.array_equal(scene[:, :10], original[:, :10])


def test_pixelate_turns_the_box_into_blocks(masks):
    scene = np.random.default_rng(0).integers(0, 255, (40, 40, 3), dtype=np.uint8)
    original = scene.copy()

    masks.pixelate_boxes(scene, np.array([[0, 0, 20, 20]]), pixel_size=10)

    assert len({tuple(scene[r, c]) for r in range(10) for c in range(10)}) == 1
    assert np.array_equal(scene[20:], original[20:])
    assert masks.pixelate_boxes(scene, np.array([[50, 50, 60, 60]])) is scene


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
    pytest.importorskip("ultralytics")
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


# --------------------------------------------------------------------------
# Adapter
# --------------------------------------------------------------------------


def test_yaml_adapter_reads_writes_and_reports_the_line():
    from zul.adapters import yaml as yaml_adapter

    data = yaml_adapter.loads("b: 1\na: [x, y]\n")

    assert data == {"b": 1, "a": ["x", "y"]}
    assert yaml_adapter.dumps(data) == "b: 1\na:\n- x\n- y\n"
    with pytest.raises(yaml_adapter.YamlError) as error:
        yaml_adapter.loads("a: [1, 2\n")
    assert error.value.line == 2


def test_image_files_round_trip_through_the_adapter(tmp_path):
    pytest.importorskip("cv2")
    from zul.computer_vision import draw
    from zul.computer_vision.video import read_image, save_image

    frame = np.zeros((40, 120, 3), dtype=np.uint8)
    draw.draw_text(frame, "zul", (5, 30), scale=0.8, thickness=2)
    path = save_image(tmp_path / "baru" / "teks.png", frame)

    assert frame.any()
    assert np.array_equal(read_image(path), frame)
    with pytest.raises(FileNotFoundError):
        read_image(tmp_path / "tidak_ada.png")


def test_unknown_colormap_names_are_rejected():
    pytest.importorskip("cv2")
    from zul.computer_vision import draw

    heat = draw.HeatMap(10, 10, radius=2)
    heat.update(np.array([[5, 5]]))

    with pytest.raises(ValueError, match="jet"):
        draw.draw_heatmap(np.zeros((10, 10, 3), dtype=np.uint8), heat, colormap="x")


def test_ultralytics_internals_used_by_the_adapter_still_exist():
    pytest.importorskip("ultralytics")
    from ultralytics.trackers.byte_tracker import BYTETracker

    from zul.adapters import ultralytics as yolo

    assert issubclass(yolo.ZulBYTETracker, BYTETracker)
    for method in ("update", "get_dists", "init_track"):
        assert callable(getattr(BYTETracker, method))
    assert callable(yolo.attempt_download_asset)
