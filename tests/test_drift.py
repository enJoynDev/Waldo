import math

import numpy as np
import pytest

import config as C
import drift as D


def drive_b1(seed, **kw):
    # open-loop straight drive using only the drift model, stopping on ODOM distance
    state, params, noise = D.new_state(), D.make_params(**kw), D.make_noise(seed)
    while state["odom"]["x"] < C.SUBGOAL_DIST:
        D.step(state, C.SPEED, 0.0, params, noise)
    return state


@pytest.mark.parametrize("d_eps", [0.0025, 0.005, 0.01])
def test_analytic_drift_check(d_eps):
    # the required gate before trusting any sweep: y ~ L^2 * d_eps / (2b) at small drift
    y = drive_b1(0, d_eps=d_eps, sigma_w=0.0)["true"]["y"]
    formula = C.SUBGOAL_DIST**2 * d_eps / (2 * C.WHEEL_BASE)
    assert y == pytest.approx(formula, rel=0.02)


def test_matches_exact_circular_arc_even_at_large_drift():
    d_eps = 0.02
    radius = C.WHEEL_BASE / d_eps
    exact = radius * (1 - math.cos(C.SUBGOAL_DIST / radius))
    assert drive_b1(0, d_eps=d_eps, sigma_w=0.0)["true"]["y"] == pytest.approx(exact, rel=0.005)


def test_odometry_never_sees_the_injected_drift():
    s = drive_b1(0, d_eps=0.01, sigma_w=0.0, s_lat=0.01)
    assert s["odom"]["y"] == 0.0 and s["odom"]["th"] == 0.0
    assert abs(s["true"]["y"]) > 0.5  # while the true robot really drifted


def test_lateral_skid():
    y = drive_b1(0, d_eps=0.0, sigma_w=0.0, s_lat=0.01)["true"]["y"]
    assert y == pytest.approx(0.01 * C.SUBGOAL_DIST, rel=0.02)


def test_same_seed_same_result_different_seed_differs():
    a, b = drive_b1(3, d_eps=0.005), drive_b1(3, d_eps=0.005)
    assert a["true"] == b["true"]
    assert drive_b1(4, d_eps=0.005)["true"] != a["true"]


def test_noise_is_identical_across_calls_for_paired_comparison():
    n1, n2 = D.make_noise(11), D.make_noise(11)
    assert np.array_equal(n1["wheel"], n2["wheel"])
    assert np.array_equal(n1["gyro"], n2["gyro"])
    assert n1["depth_rng"].random() == n2["depth_rng"].random()


def test_gyro_tracks_true_heading_without_bias_or_noise(monkeypatch):
    monkeypatch.setattr(C, "GYRO_NOISE_DEG_S", 0.0)
    s = drive_b1(0, d_eps=0.01, sigma_w=0.0, gyro_bias_deg_s=0.0)
    assert s["gyro_th"] == pytest.approx(s["true"]["th"], abs=1e-9)


def test_gyro_bias_accumulates_linearly(monkeypatch):
    monkeypatch.setattr(C, "GYRO_NOISE_DEG_S", 0.0)
    s = drive_b1(0, d_eps=0.0, sigma_w=0.0, gyro_bias_deg_s=0.1)
    assert s["gyro_th"] - s["true"]["th"] == pytest.approx(math.radians(0.1) * s["t"], rel=1e-6)


def test_wheel_noise_spread_matches_hand_estimate():
    # 1% wheel noise over 10 m should spread the final lateral error by about 0.1 m
    ys = [drive_b1(seed, d_eps=0.0)["true"]["y"] for seed in range(100)]
    assert 0.06 < np.std(ys) < 0.15
