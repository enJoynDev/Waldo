import pandas as pd
import pytest

import plot_results as P


def test_wilson_interval_for_zero_and_all():
    lo, hi = P.wilson(0, 30)
    assert lo == pytest.approx(0.0, abs=1e-9)
    assert 0.10 < hi < 0.13
    lo, hi = P.wilson(30, 30)
    assert hi == pytest.approx(1.0, abs=1e-9)
    assert 0.87 < lo < 0.90


def test_mean_ci_of_identical_values_has_zero_width():
    mean, half = P.mean_ci([2.0, 2.0, 2.0])
    assert mean == 2.0
    assert half == 0.0


def test_summary_table_counts_collisions_per_condition():
    df = pd.DataFrame(
        {
            "mode": ["B1"] * 4,
            "d_eps": [0.01] * 4,
            "sigma_d": [0.0] * 4,
            "seed": range(4),
            "abs_lat": [0.5, 0.6, 0.1, 0.2],
            "max_lat_err": [0.5, 0.6, 0.1, 0.2],
            "final_head_err_deg": [1.0, -1.0, 0.5, -0.5],
            "collided": [True, True, False, False],
            "success": [False, False, True, True],
            "fit_fail_frac": [float("nan")] * 4,
            "runtime_s": [0.1] * 4,
        }
    )
    row = P.summary_table(df).iloc[0]
    assert row["n"] == 4
    assert row["collisions"] == 2
    assert row["successes"] == 2
    assert row["abs_lat_mean"] == pytest.approx(0.35)
