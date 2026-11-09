import pytest

from attendance_camera.config import Calibration
from attendance_camera.counting import CrossingCounter


def feed(counter, points, key=1, start=0):
    totals = [0, 0]
    for i, (x, y) in enumerate(points):
        values = counter.update([(key, x, y)], start + i * 0.1)
        totals = [a + b for a, b in zip(totals, values)]
    return tuple(totals)


def test_entry_exit_and_jitter():
    counter = CrossingCounter(Calibration())
    assert feed(counter, [(0.5, y) for y in [0.3, 0.3, 0.49, 0.51, 0.48, 0.52, 0.7, 0.7]]) == (1, 0)
    assert feed(counter, [(0.5, y) for y in [0.7, 0.7, 0.3, 0.3]], start=1) == (0, 1)


def test_first_sighting_and_expired_id_are_not_crossings():
    counter = CrossingCounter(Calibration())
    assert feed(counter, [(0.5, 0.3)] * 3) == (0, 0)
    assert feed(counter, [(0.5, 0.7)] * 3, start=10) == (0, 0)


def test_exiting_region_does_not_count_a_walk_around_boundary():
    counter = CrossingCounter(Calibration())
    assert feed(counter, [(0.5, 0.3), (0.5, 0.3), (1, 0.5), (0.5, 0.7), (0.5, 0.7)]) == (0, 0)


def test_multiple_people_and_reversed_direction():
    counter = CrossingCounter(Calibration(axis="x", inside="negative"))
    for now in (0, 0.1):
        assert counter.update([(1, 0.8, 0.4), (2, 0.2, 0.6)], now) == (0, 0)
    assert counter.update([(1, 0.2, 0.4), (2, 0.8, 0.6)], 0.2) == (0, 0)
    assert counter.update([(1, 0.2, 0.4), (2, 0.8, 0.6)], 0.3) == (1, 1)


@pytest.mark.parametrize(
    "values",
    [
        {"x_min": 0.8, "x_max": 0.2},
        {"position": float("nan")},
        {"axis": "z"},
        {"deadband": 0.15, "position": 0.1},
    ],
)
def test_rejects_invalid_calibration(values):
    with pytest.raises(ValueError):
        Calibration(**values)
