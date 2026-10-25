"""Grid search for the controller gains on the tuning seeds (never the reported seeds)."""

import itertools
import multiprocessing as mp

import pandas as pd
from tqdm import tqdm

import config as C
import drift as D
import run_trial as R
import world as W

_world = None


def _init_worker():
    global _world
    _world = W.create_world()  # one PyBullet client per process


def _job(args):
    k_lat, k_head, d_eps, seed = args
    C.K_LAT, C.K_HEAD = k_lat, k_head  # control.py reads these at call time
    r = R.run_trial(_world, "C_both", seed, D.make_params(d_eps=d_eps))
    return {
        "k_lat": k_lat,
        "k_head": k_head,
        "d_eps": d_eps,
        "seed": seed,
        "abs_lat": abs(r["final_lat_err"]),
        "max_lat": r["max_lat_err"],
        "head_deg": abs(r["final_head_err_deg"]),
        "collided": r["collided"],
        "fit_fail": r["fit_fail_frac"],
    }


def summarise(df):
    """One row per gain pair: collisions and mean errors at each drift level."""
    s = (
        df.groupby(["k_lat", "k_head", "d_eps"])
        .agg(coll=("collided", "sum"), abs_lat=("abs_lat", "mean"), max_lat=("max_lat", "mean"))
        .reset_index()
    )
    wide = s.pivot(
        index=["k_lat", "k_head"], columns="d_eps", values=["coll", "abs_lat", "max_lat"]
    )
    wide.columns = [f"{name}_{d_eps}" for name, d_eps in wide.columns]
    return wide.reset_index().sort_values(f"abs_lat_{C.GAIN_GRID_D_EPS[-1]}")


def main():
    seeds = C.SEEDS_TUNE[: C.GAIN_GRID_N_SEEDS]
    jobs = list(itertools.product(C.GAIN_GRID_K_LAT, C.GAIN_GRID_K_HEAD, C.GAIN_GRID_D_EPS, seeds))
    workers = max(1, min(16, mp.cpu_count() - 2))
    with mp.Pool(workers, initializer=_init_worker) as pool:
        rows = list(tqdm(pool.imap_unordered(_job, jobs), total=len(jobs)))
    df = pd.DataFrame(rows)
    C.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(C.RESULTS_DIR / "tuning_gains.csv", index=False)
    print(summarise(df).round(4).to_string(index=False))


if __name__ == "__main__":
    main()
