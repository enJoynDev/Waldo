import pytest

import config as C
import drift as D
import run_trial as R

COLUMNS = {
    "seed", "mode", "d_eps", "s_lat", "sigma_w", "sigma_d", "final_lat_err",
    "final_head_err_deg", "max_lat_err", "collided", "dist_travelled", "drift_paper",
    "success", "fit_fail_frac", "runtime_s",
}  # fmt: skip


def trial(world, seed=0, **kw):
    return R.run_trial(world, "B1", seed, D.make_params(**kw))


def test_row_has_the_columns_in_the_experiment_spec(world):
    assert set(trial(world, d_eps=0.005)) == COLUMNS


def test_zero_drift_zero_noise_is_a_success(world):
    r = trial(world, d_eps=0.0, sigma_w=0.0)
    assert r["success"] is True and r["collided"] is False
    assert r["dist_travelled"] == pytest.approx(C.SUBGOAL_DIST, abs=0.01)


def test_baseline_collision_boundary(world):
    # EXPERIMENTS.md section 6: the baseline should start colliding between 0.5% and 1%
    assert trial(world, d_eps=0.005, sigma_w=0.0)["collided"] is False
    r = trial(world, d_eps=0.01, sigma_w=0.0)
    assert r["collided"] is True and 7.5 < r["dist_travelled"] < 8.5


def test_same_seed_gives_identical_rows(world):
    a, b = trial(world, 4, d_eps=0.005), trial(world, 4, d_eps=0.005)
    for row in (a, b):
        row.pop("runtime_s"), row.pop("fit_fail_frac")  # wall time varies and NaN != NaN
    assert a == b


def test_trial_after_a_collision_starts_clean(world):
    trial(world, d_eps=0.02, sigma_w=0.0)  # ends in a collision
    r = trial(world, d_eps=0.0, sigma_w=0.0)
    assert r["collided"] is False and r["success"] is True


def test_unknown_mode_is_refused(world):
    with pytest.raises(ValueError):
        R.run_trial(world, "B3", 0, D.make_params())
