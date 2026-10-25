"""Figures and summary table from results/raw.csv (figures 1, 2, 4, 5)."""

import numpy as np
import pandas as pd
from scipy import stats

import config as C

STYLE = {  # one colour and marker per mode, the same in every figure
    "B1": ("#c4571a", "o"),
    "B2": ("#7a7a7a", "s"),
    "C_lat": ("#2a9d8f", "^"),
    "C_head": ("#8e5ea2", "v"),
    "C_both": ("#2a6fb0", "D"),
}
EPS_LABELS = {0: "0", 0.0025: "0.25%", 0.005: "0.5%", 0.01: "1%", 0.02: "2%"}
LEGEND = {"frameon": False, "loc": "center left", "bbox_to_anchor": (1.01, 0.5)}


def load():
    df = pd.read_csv(C.RAW_CSV)
    df["abs_lat"] = df["final_lat_err"].abs()
    return df


def mean_ci(values):
    """Mean and 95% t-interval half-width."""
    n = len(values)
    mean = float(np.mean(values))
    if n < 2:
        return mean, 0.0
    return mean, float(stats.t.ppf(0.975, n - 1) * np.std(values, ddof=1) / np.sqrt(n))


def wilson(k, n, z=1.96):
    """Wilson score interval (low, high) for k successes out of n."""
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def summary_table(df):
    g = df.groupby(["mode", "d_eps", "sigma_d"], sort=False)
    return g.agg(
        n=("seed", "size"),
        abs_lat_mean=("abs_lat", "mean"),
        abs_lat_std=("abs_lat", "std"),
        max_lat_mean=("max_lat_err", "mean"),
        head_abs_mean=("final_head_err_deg", lambda s: s.abs().mean()),
        collisions=("collided", "sum"),
        successes=("success", "sum"),
        fit_fail=("fit_fail_frac", "mean"),
        runtime_s=("runtime_s", "mean"),
    ).reset_index()


def _finish(fig, ax, path):
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)


def fig1_lateral_error(df, path):
    import matplotlib.pyplot as plt

    main = df[df["sigma_d"] == 0]
    levels = list(C.D_EPS_LEVELS)
    fig, ax = plt.subplots(figsize=(8, 4))
    for mode, (color, marker) in STYLE.items():
        means, halves = [], []
        for d in levels:
            m, h = mean_ci(main[(main["mode"] == mode) & (main["d_eps"] == d)]["abs_lat"])
            means.append(m)
            halves.append(h)
        ax.errorbar(
            range(len(levels)),
            means,
            yerr=halves,
            color=color,
            marker=marker,
            lw=2,
            capsize=3,
            label=mode,
        )
    ax.set_yscale("log")
    ax.set_xticks(range(len(levels)), [EPS_LABELS[d] for d in levels])
    ax.set_xlabel("Wheel-scale mismatch d_eps")
    ax.set_ylabel("Final |lateral error| (m), mean and 95% CI")
    ax.legend(**LEGEND)
    ax.text(
        0,
        -0.2,
        "A trial that collides stops at the crash, so its error is measured there.",
        transform=ax.transAxes,
        fontsize=8,
        color="gray",
    )
    _finish(fig, ax, path)


def fig2_collision_rate(df, path):
    import matplotlib.pyplot as plt

    main = df[df["sigma_d"] == 0]
    levels = list(C.D_EPS_LEVELS)
    fig, ax = plt.subplots(figsize=(8, 4))
    for i, (mode, (color, marker)) in enumerate(STYLE.items()):
        rates, lows, highs = [], [], []
        for d in levels:
            g = main[(main["mode"] == mode) & (main["d_eps"] == d)]
            k, n = int(g["collided"].sum()), len(g)
            lo, hi = wilson(k, n)
            rates.append(k / n)
            lows.append(k / n - lo)
            highs.append(hi - k / n)
        x = (
            np.arange(len(levels)) + (i - 2) * 0.04
        )  # small offset so overlapping lines stay visible
        ax.errorbar(
            x, rates, yerr=[lows, highs], color=color, marker=marker, lw=2, capsize=3, label=mode
        )
    ax.set_xticks(range(len(levels)), [EPS_LABELS[d] for d in levels])
    ax.set_xlabel("Wheel-scale mismatch d_eps")
    ax.set_ylabel("Collision rate (Wilson 95% interval)")
    ax.set_ylim(-0.05, 1.05)
    ax.legend(**LEGEND)
    _finish(fig, ax, path)


def fig4_depth_noise(df, path):
    import matplotlib.pyplot as plt

    d = C.DEPTH_SWEEP_D_EPS
    sub = df[df["d_eps"] == d]
    sigmas = sorted(sub[sub["mode"] == "C_both"]["sigma_d"].unique())
    fig, ax = plt.subplots(figsize=(8, 4))
    means, halves = [], []
    for s in sigmas:
        m, h = mean_ci(sub[(sub["mode"] == "C_both") & (sub["sigma_d"] == s)]["abs_lat"])
        means.append(m)
        halves.append(h)
    color, marker = STYLE["C_both"]
    ax.errorbar(
        sigmas, means, yerr=halves, color=color, marker=marker, lw=2, capsize=3, label="C_both"
    )
    for mode in ("B1", "B2"):  # baselines do not use depth, so they are flat reference lines
        ref = mean_ci(sub[(sub["mode"] == mode) & (sub["sigma_d"] == 0)]["abs_lat"])[0]
        ax.axhline(ref, color=STYLE[mode][0], lw=1.5, ls="--", label=f"{mode} (no depth)")
    ax.set_yscale("log")
    ax.set_xlabel("Depth noise sigma_d (m)")
    ax.set_ylabel(f"Final |lateral error| (m), d_eps = {EPS_LABELS[d]}")
    ax.legend(**LEGEND)
    _finish(fig, ax, path)


def fig5_ablation(df, path):
    import matplotlib.pyplot as plt

    main = df[df["sigma_d"] == 0]
    modes = ["C_lat", "C_head", "C_both"]
    fig, ax = plt.subplots(figsize=(7, 4))
    width = 0.25
    for i, mode in enumerate(modes):
        means, halves = [], []
        for d in C.ABLATION_D_EPS:
            m, h = mean_ci(main[(main["mode"] == mode) & (main["d_eps"] == d)]["abs_lat"])
            means.append(m)
            halves.append(h)
        x = np.arange(len(C.ABLATION_D_EPS)) + (i - 1) * width
        ax.bar(x, means, width, yerr=halves, color=STYLE[mode][0], capsize=3, label=mode)
    ax.set_xticks(range(len(C.ABLATION_D_EPS)), [EPS_LABELS[d] for d in C.ABLATION_D_EPS])
    ax.set_xlabel("Wheel-scale mismatch d_eps")
    ax.set_ylabel("Final |lateral error| (m), mean and 95% CI")
    ax.legend(**LEGEND)
    _finish(fig, ax, path)


def main():
    df = load()
    table = summary_table(df)
    table.to_csv(C.RESULTS_DIR / "summary.csv", index=False)
    print(table.round(4).to_string(index=False))
    fig1_lateral_error(df, C.FIGURES_DIR / "fig1_lateral_error.png")
    fig2_collision_rate(df, C.FIGURES_DIR / "fig2_collision_rate.png")
    fig4_depth_noise(df, C.FIGURES_DIR / "fig4_depth_noise.png")
    fig5_ablation(df, C.FIGURES_DIR / "fig5_ablation.png")


if __name__ == "__main__":
    main()
