import math

import pytest

import metrics as M


def pose(x, y, th):
    return {"x": x, "y": y, "th": th}


def test_perfect_finish():
    m = M.trial_metrics(pose(10, 0, 0), 0.0, False)
    assert m["final_lat_err"] == 0 and m["drift_paper"] == 0 and m["success"] is True


def test_drifted_finish():
    m = M.trial_metrics(pose(9.947, 0.907, 0.1819), 0.907, False)
    assert m["final_head_err_deg"] == pytest.approx(math.degrees(0.1819))
    assert m["drift_paper"] == pytest.approx(math.hypot(0.053, 0.907) - 0.2)
    assert m["success"] is False


def test_collision_reports_distance_and_never_succeeds():
    m = M.trial_metrics(pose(6.0, 0.7, 0.1), 0.7, True)
    assert m["dist_travelled"] == 6.0 and m["collided"] is True and m["success"] is False
    assert M.trial_metrics(pose(10, 0, 0), 0.0, True)["success"] is False  # centred but hit a wall


def test_heading_is_wrapped():
    m = M.trial_metrics(pose(10, 0, 2 * math.pi + 0.1), 0.0, False)
    assert m["final_head_err_deg"] == pytest.approx(math.degrees(0.1))


@pytest.mark.parametrize(
    "y, success", [(0.149, True), (0.15, False), (-0.149, True), (-0.3, False)]
)
def test_success_threshold_is_strict_and_symmetric(y, success):
    assert M.trial_metrics(pose(10, y, 0), abs(y), False)["success"] is success


def test_lateral_error_keeps_its_sign():
    assert M.trial_metrics(pose(10, -0.3, 0), 0.3, False)["final_lat_err"] == -0.3


def test_paper_metric_is_zero_inside_the_safety_radius():
    assert M.trial_metrics(pose(9.9, 0.1, 0), 0.1, False)["drift_paper"] == 0
