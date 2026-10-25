import pytest

import config as C
import drift as D
import run_trial as R

SEED = 0


def test_c_both_stays_centred_without_drift(world):
    r = R.run_trial(world, "C_both", SEED, D.make_params(d_eps=0.0))
    assert not r["collided"]
    assert r["max_lat_err"] < 0.05


def test_c_both_survives_the_drift_that_crashes_b1(world):
    params = D.make_params(d_eps=0.01)
    b1 = R.run_trial(world, "B1", SEED, params)
    c = R.run_trial(world, "C_both", SEED, params)
    assert b1["collided"]
    assert not c["collided"]
    assert c["success"]
    assert abs(c["final_lat_err"]) < abs(b1["final_lat_err"])


def test_low_confidence_everywhere_falls_back_to_odometry_only(world, monkeypatch):
    monkeypatch.setattr(C, "CONF_THRESHOLD", 2.0)  # no estimate can reach this
    params = D.make_params(d_eps=0.005)
    b1 = R.run_trial(world, "B1", SEED, params)
    c = R.run_trial(world, "C_both", SEED, params)
    assert c["fit_fail_frac"] == pytest.approx(1.0)
    for key in ("final_lat_err", "final_head_err_deg", "max_lat_err", "dist_travelled"):
        assert c[key] == b1[key]


def test_c_both_same_seed_same_result(world):
    params = D.make_params(d_eps=0.005)
    a = R.run_trial(world, "C_both", SEED, params, sigma_d=0.02)
    b = R.run_trial(world, "C_both", SEED, params, sigma_d=0.02)
    a.pop("runtime_s")
    b.pop("runtime_s")
    assert a == b
