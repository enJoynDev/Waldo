"""Sprint 3 checks on the tuning seeds: the DoD comparison and the trajectory plot."""

import multiprocessing as mp

import pandas as pd
from tqdm import tqdm

import config as C
import drift as D
import run_trial as R
import world as W

D_EPS = 0.01  # the Sprint 3 DoD drift level
CASES = (("B1", 0.0), ("B2", 0.0), ("C_both", 0.0), ("C_both", 0.05))  # (mode, sigma_d)
PLOT_SEEDS = C.SEEDS_TUNE[:5]
_world = None


def _init_worker():
    global _world
    _world = W.create_world()  # one PyBullet client per process


def _job(args):
    mode, sigma_d, seed = args
    r = R.run_trial(_world, mode, seed, D.make_params(d_eps=D_EPS), sigma_d=sigma_d)
    return {
        "mode": mode,
        "sigma_d": sigma_d,
        "seed": seed,
        "abs_lat": abs(r["final_lat_err"]),
        "max_lat": r["max_lat_err"],
        "collided": r["collided"],
        "success": r["success"],
        "fit_fail": r["fit_fail_frac"],
    }


def summarise(df):
    return (
        df.groupby(["mode", "sigma_d"], sort=False)
        .agg(
            n=("seed", "size"),
            collisions=("collided", "sum"),
            successes=("success", "sum"),
            abs_lat=("abs_lat", "mean"),
            max_lat=("max_lat", "mean"),
            fit_fail=("fit_fail", "mean"),
        )
        .reset_index()
    )


def trajectory(world, mode, seed):
    """TRUE (x, y) path of one trial, sampled every 0.1 s."""
    xs, ys, count = [], [], [0]

    def on_step(state):
        count[0] += 1
        if count[0] % 24 == 0:  # 24 steps of 1/240 s
            xs.append(state["true"]["x"])
            ys.append(state["true"]["y"])

    R.run_trial(world, mode, seed, D.make_params(d_eps=D_EPS), on_step=on_step)
    return xs, ys


def plot(world, path):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 2.8))
    for i, seed in enumerate(PLOT_SEEDS):
        for mode, color in (("B1", "#c4571a"), ("C_both", "#2a6fb0")):
            xs, ys = trajectory(world, mode, seed)
            ax.plot(xs, ys, color=color, lw=1.6, label=mode if i == 0 else None)
    half = C.CORRIDOR_WIDTH / 2
    for y in (half, -half):
        ax.axhline(y, color="black", lw=2)  # walls
    for y in (C.CLEARANCE, -C.CLEARANCE):
        ax.axhline(y, color="gray", lw=1, ls=":")  # robot centre at this y means it touches
    ax.text(0.1, C.CLEARANCE + 0.03, "collision limit", color="gray", va="bottom")
    ax.set_xlim(0, C.SUBGOAL_DIST)
    ax.set_ylim(-half - 0.1, half + 0.1)
    ax.set_xlabel("Forward distance x (m)")
    ax.set_ylabel("Lateral position y (m)")
    ax.set_aspect("equal")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="lower left")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)


def main():
    jobs = [(m, s, seed) for (m, s) in CASES for seed in C.SEEDS_TUNE]
    workers = max(1, min(16, mp.cpu_count() - 2))
    with mp.Pool(workers, initializer=_init_worker) as pool:
        rows = list(tqdm(pool.imap_unordered(_job, jobs), total=len(jobs)))
    df = pd.DataFrame(rows)
    C.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(C.RESULTS_DIR / "sprint3_check.csv", index=False)
    print(summarise(df).round(4).to_string(index=False))
    world = W.create_world()
    plot(world, C.FIGURES_DIR / "sprint3_trajectories.png")
    W.close_world()


if __name__ == "__main__":
    main()
