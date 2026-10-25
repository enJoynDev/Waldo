import numpy as np
import pandas as pd
import pytest

import analysis as A

SEEDS = pd.Index(np.arange(30), name="seed")


def _frame(values, success=True):
    return pd.DataFrame({"abs_lat": values, "success": success}, index=SEEDS)


def test_clearly_better_method_is_significant_on_every_seed():
    rng = np.random.default_rng(0)
    a = _frame(0.005 + 0.001 * rng.random(30))
    b = _frame(0.1 + 0.01 * rng.random(30))
    r = A.compare(a, b, "x", "c")
    assert r["a_better_seeds"] == 30
    assert r["p_wilcoxon"] < 1e-6
    assert r["median_diff"] > 0


def test_identical_methods_give_p_of_one():
    a = _frame(np.linspace(0.01, 0.02, 30))
    r = A.compare(a, a.copy(), "same", "c")
    assert r["p_wilcoxon"] == 1.0
    assert r["a_better_seeds"] == 0


def test_discordant_successes_are_counted():
    a = _frame(0.01, success=True)
    b = _frame(0.2, success=[False] * 10 + [True] * 20)
    r = A.compare(a, b, "x", "c")
    assert r["only_a_succeeds"] == 10
    assert r["only_b_succeeds"] == 0
    assert r["p_sign"] == pytest.approx(2 * 0.5**10)


def test_mismatched_seeds_are_refused():
    a = _frame(0.01)
    b = _frame(0.02).iloc[:-1]
    with pytest.raises(ValueError):
        A.compare(a, b, "x", "c")
