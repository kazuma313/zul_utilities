from conftest import BASE_CONFIG, people

from cctv.analytics import SceneAnalytics
from cctv.settings import load_scene_config

PERIOD = 0.1


def run_frames(analytics, frames):
    """`frames` berisi pasangan (kotak, id) untuk setiap frame."""
    finished = []
    for number, (boxes, ids) in enumerate(frames):
        update = analytics.update(number, number * PERIOD, people(boxes, ids))
        finished.append(update.finished)
    finished.append(analytics.finish())
    return finished


def test_crossings_are_counted_once_in_each_direction(write_scene):
    analytics = SceneAnalytics(load_scene_config(BASE_CONFIG, write_scene()), PERIOD)
    frames = []
    for step in range(20):
        down = 60 + step * 8  # kaki dari y=100 ke y=252: melintasi garis y=120
        up = 230 - step * 8
        frames.append(([[40, down - 40, 60, down], [200, up - 40, 220, up]], [1, 2]))

    finished = run_frames(analytics, frames)
    crossings = [c for f in finished for c in f.crossings]

    assert sorted(c.track_id for c in crossings) == [1, 2]
    assert {c.direction for c in crossings} == {"masuk", "keluar"}
    assert analytics.summary()["garis"]["pintu"] == {"masuk": 1, "keluar": 1}


def test_only_people_who_stay_long_enough_count_as_stopped(write_scene):
    analytics = SceneAnalytics(load_scene_config(BASE_CONFIG, write_scene()), PERIOD)
    frames = []
    for step in range(30):
        boxes, ids = [[100, 20, 120, 60]], [3]  # 3 detik di zona "depan"
        if step < 5:
            boxes.append([200, 20, 220, 60])  # 0,5 detik di zona yang sama
            ids.append(4)
        frames.append((boxes, ids))

    run_frames(analytics, frames)
    zone = analytics.summary()["zona"]["depan"]

    assert zone["pengunjung"] == 2
    assert zone["berhenti_minimal_2_detik"] == 1
    assert zone["memperhatikan"] == 0  # tanpa keypoint, tidak ada arah hadap


def test_people_close_to_each_other_become_a_contact(write_scene):
    analytics = SceneAnalytics(
        load_scene_config(BASE_CONFIG, write_scene(proximity=2.0)), PERIOD
    )
    frames = [([[100, 140, 130, 230], [140, 140, 170, 230]], [5, 6])] * 20

    finished = run_frames(analytics, frames)
    contacts = [c for f in finished for c in f.contacts]

    assert [(c.first_id, c.second_id) for c in contacts] == [(5, 6)]
    assert analytics.summary()["kontak"] == 1


def test_a_frame_without_people_changes_nothing(write_scene):
    analytics = SceneAnalytics(load_scene_config(BASE_CONFIG, write_scene()), PERIOD)

    update = analytics.update(0, 0.0, people([], []))

    assert update.membership == [] and update.pairs == []
    assert analytics.summary()["garis"]["pintu"] == {"masuk": 0, "keluar": 0}
