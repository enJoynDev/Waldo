"""Run every experiment condition in parallel and write results/raw.csv."""

import itertools
import multiprocessing as mp
import time

import pandas as pd
from tqdm import tqdm

import config as C
import drift as D
import run_trial as R
import world as W

COLUMNS = [
    "run_id",
    "seed",
    "mode",
    "d_eps",
    "s_lat",
    "sigma_w",
    "sigma_d",
    "final_lat_err",
    "final_head_err_deg",
    "max_lat_err",
    "collided",
    "dist_travelled",
    "drift_paper",
    "success",
    "fit_fail_frac",
    "runtime_s",
]
_world = None


def build_conditions():
    """All (mode, d_eps, sigma_d, seed) trials: the main sweep, then the depth-noise sweep."""
    main = itertools.product(C.MODES, C.D_EPS_LEVELS, (0.0,), C.SEEDS_REPORT)
    noisy = [s for s in C.SIGMA_D_LEVELS if s > 0]  # sigma_d = 0 is already in the main sweep
    depth = itertools.product(("C_both",), (C.DEPTH_SWEEP_D_EPS,), noisy, C.SEEDS_REPORT)
    return list(main) + list(depth)


def run_one(world, run_id, condition):
    mode, d_eps, sigma_d, seed = condition
    row = R.run_trial(world, mode, seed, D.make_params(d_eps=d_eps), sigma_d=sigma_d)
    row["run_id"] = run_id
    return {col: row[col] for col in COLUMNS}


def _init_worker():
    global _world
    _world = W.create_world()  # one PyBullet client per process


def _job(args):
    run_id, condition = args
    return run_one(_world, run_id, condition)


def main():
    t0 = time.perf_counter()
    jobs = list(enumerate(build_conditions()))
    workers = max(1, min(16, mp.cpu_count() - 2))
    with mp.Pool(workers, initializer=_init_worker) as pool:
        rows = list(tqdm(pool.imap_unordered(_job, jobs), total=len(jobs)))
    df = pd.DataFrame(rows, columns=COLUMNS).sort_values("run_id")
    if df.duplicated(["mode", "d_eps", "sigma_d", "seed"]).any():
        raise RuntimeError("duplicate conditions in raw.csv")
    C.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(C.RAW_CSV, index=False)
    print(f"{len(df)} rows written to {C.RAW_CSV} in {time.perf_counter() - t0:.0f} s")


if __name__ == "__main__":
    main()
