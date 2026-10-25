"""Paired statistics: is the corrected method better than each baseline, seed by seed?"""

import pandas as pd
from scipy import stats

import config as C


def _load(path):
    df = pd.read_csv(path)
    df["abs_lat"] = df["final_lat_err"].abs()
    return df


def _rows(df, mode, **cond):
    mask = df["mode"] == mode
    for key, value in cond.items():
        mask &= df[key] == value
    return df[mask].set_index("seed").sort_index()


def compare(a, b, comparison, condition):
    """a is the method, b the baseline; rows are indexed by seed, so the pairs are per seed."""
    if not a.index.equals(b.index):
        raise ValueError(f"seeds do not match for {comparison} at {condition}")
    diff = b["abs_lat"] - a["abs_lat"]  # positive means a is better
    p = stats.wilcoxon(diff).pvalue if (diff != 0).any() else 1.0
    a_ok, b_ok = a["success"].astype(bool), b["success"].astype(bool)
    only_a, only_b = int((a_ok & ~b_ok).sum()), int((~a_ok & b_ok).sum())
    p_sign = stats.binomtest(only_a, only_a + only_b, 0.5).pvalue if only_a + only_b else 1.0
    return {
        "comparison": comparison,
        "condition": condition,
        "n": len(diff),
        "median_a": a["abs_lat"].median(),
        "median_b": b["abs_lat"].median(),
        "median_diff": diff.median(),
        "a_better_seeds": int((diff > 0).sum()),
        "p_wilcoxon": p,
        "success_a": int(a_ok.sum()),
        "success_b": int(b_ok.sum()),
        "only_a_succeeds": only_a,
        "only_b_succeeds": only_b,
        "p_sign": p_sign,
    }


def build(main, stress):
    out = []
    for d in C.D_EPS_LEVELS:
        a = _rows(main, "C_both", d_eps=d, sigma_d=0)
        for base in ("B2", "B1", "C_lat", "C_head"):
            b = _rows(main, base, d_eps=d, sigma_d=0)
            out.append(compare(a, b, f"C_both vs {base}", f"d_eps={d}"))
    for s in (s for s in C.S_LAT_LEVELS if s > 0):
        a = _rows(stress, "C_both", d_eps=C.DEPTH_SWEEP_D_EPS, s_lat=s)
        for base in ("B2", "C_head", "C_lat"):
            b = _rows(stress, base, d_eps=C.DEPTH_SWEEP_D_EPS, s_lat=s)
            out.append(compare(a, b, f"C_both vs {base}", f"skid={s}, d_eps={C.DEPTH_SWEEP_D_EPS}"))
    for d in C.STRESS_GYRO_D_EPS:
        a = _rows(main, "C_both", d_eps=d, sigma_d=0)
        for bias in C.GYRO_BIAS_SWEEP_DEG_S:
            b = _rows(stress, "B2", d_eps=d, gyro_bias_deg_s=bias, s_lat=0)
            out.append(compare(a, b, "C_both vs B2", f"bias={bias}, d_eps={d}"))
    df = pd.DataFrame(out)
    df["p_bonferroni"] = (df["p_wilcoxon"] * len(df)).clip(upper=1.0)
    return df


def main():
    table = build(_load(C.RAW_CSV), _load(C.STRESS_CSV))
    table.to_csv(C.RESULTS_DIR / "stats.csv", index=False)
    show = ["comparison", "condition", "median_a", "median_b", "a_better_seeds", "p_bonferroni"]
    print(table[show].round(4).to_string(index=False))
    print(f"\n{len(table)} tests; {int((table['p_bonferroni'] < 0.05).sum())} significant at 0.05")


if __name__ == "__main__":
    main()
