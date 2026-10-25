"""Perception accuracy vs depth noise, on a grid of known poses (tuning seeds only)."""

import numpy as np
import pandas as pd

import config as C
import perception as P
import world as W


def collect():
    """One row per (sigma_d, seed, pose): estimate vs truth. Renders each pose once."""
    renders = {}
    for y in C.PERCEPTION_GRID_Y:
        for head_deg in C.PERCEPTION_GRID_HEAD_DEG:
            renders[(y, head_deg)] = W.render_depth(0.0, y, np.radians(head_deg))
    rows = []
    for sigma_d in C.SIGMA_D_LEVELS:
        for seed in C.SEEDS_TUNE:
            depth_rng, ransac_rng = (
                np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(2)
            )
            for (y, head_deg), depth in renders.items():
                est = P.estimate_pose(W.add_depth_noise(depth, sigma_d, depth_rng), ransac_rng)
                rows.append(
                    {
                        "sigma_d": sigma_d,
                        "seed": seed,
                        "y": y,
                        "head_deg": head_deg,
                        "ok": est["ok"],
                        "confidence": est["confidence"],
                        "offset_err": abs(est["offset"] - y),
                        "head_err_deg": abs(np.degrees(est["heading"]) - head_deg),
                    }
                )
    return pd.DataFrame(rows)


def summarise(df):
    """Per noise level: failure rate, median and 95th-percentile errors, confidence spread."""
    out = []
    for sigma_d, g in df.groupby("sigma_d"):
        good = g[g["ok"]]
        out.append(
            {
                "sigma_d": sigma_d,
                "n": len(g),
                "fail_rate": 1 - g["ok"].mean(),
                "offset_med": good["offset_err"].median(),
                "offset_p95": good["offset_err"].quantile(0.95),
                "head_med_deg": good["head_err_deg"].median(),
                "head_p95_deg": good["head_err_deg"].quantile(0.95),
                "conf_p05": g["confidence"].quantile(0.05),
                "conf_p50": g["confidence"].median(),
            }
        )
    return pd.DataFrame(out)


def plot(summary, path):
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    panels = [
        (axes[0], "offset_med", "offset_p95", "Lateral offset error (m)"),
        (axes[1], "head_med_deg", "head_p95_deg", "Heading error (deg)"),
    ]
    targets = [C.PERCEPTION_OFFSET_TARGET, C.PERCEPTION_HEAD_TARGET_DEG]
    x = summary["sigma_d"]
    for (ax, med, p95, label), target in zip(panels, targets, strict=True):
        ax.plot(x, summary[med], "o-", color="#2a6fb0", lw=2, label="median")
        ax.plot(x, summary[p95], "s--", color="#c4571a", lw=2, label="95th percentile")
        ax.axhline(target, color="gray", lw=1, ls=":")
        ax.text(x.iloc[-1], target, "target", va="bottom", ha="right", color="gray")
        ax.set_xlabel("Depth noise sigma (m)")
        ax.set_ylabel(label)
        ax.set_ylim(bottom=0)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(frameon=False)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)


def main():
    W.create_world()
    df = collect()
    C.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(C.RESULTS_DIR / "perception_noise.csv", index=False)
    summary = summarise(df)
    print(summary.round(4).to_string(index=False))
    plot(summary, C.FIGURES_DIR / "perception_vs_noise.png")


if __name__ == "__main__":
    main()
