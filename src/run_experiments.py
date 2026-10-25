"""Run every experiment condition in parallel and write results/raw.csv (or stress.csv)."""

import itertools
import multiprocessing as mp
import sys
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
    "gyro_bias_deg_s",
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
KEY = ["mode", "d_eps", "s_lat", "gyro_bias_deg_s", "sigma_d", "seed"]
_world = None


def _cond(mode, d_eps, sigma_d, seed, s_lat=C.S_LAT_DEFAULT, bias=C.GYRO_BIAS_DEG_S):
    return (mode, d_eps, sigma_d, seed, s_lat, bias)


def build_conditions():
    """Main trials: the main sweep, then the depth-noise sweep (all at default skid and bias)."""
    main = itertools.product(C.MODES, C.D_EPS_LEVELS, (0.0,), C.SEEDS_REPORT)
    noisy = [s for s in C.SIGMA_D_LEVELS if s > 0]  # sigma_d = 0 is already in the main sweep
    depth = itertools.product(("C_both",), (C.DEPTH_SWEEP_D_EPS,), noisy, C.SEEDS_REPORT)
    return [_cond(*c) for c in itertools.chain(main, depth)]


def build_stress_conditions():
    """Stress trials: lateral-skid sweep (all modes) and gyro-bias sweep (B2, both signs)."""
    skid_levels = [s for s in C.S_LAT_LEVELS if s > 0]  # skid = 0 is already in the main sweep
    skid = [
        _cond(m, C.DEPTH_SWEEP_D_EPS, 0.0, seed, s_lat=s)
        for m, s, seed in itertools.product(C.MODES, skid_levels, C.SEEDS_REPORT)
    ]
    gyro = [
        _cond("B2", d, 0.0, seed, bias=b)
        for d, b, seed in itertools.product(
            C.STRESS_GYRO_D_EPS, C.GYRO_BIAS_SWEEP_DEG_S, C.SEEDS_REPORT
        )
    ]
    return skid + gyro


def run_one(world, run_id, condition):
    mode, d_eps, sigma_d, seed, s_lat, bias = condition
    params = D.make_params(d_eps=d_eps, s_lat=s_lat, gyro_bias_deg_s=bias)
    row = R.run_trial(world, mode, seed, params, sigma_d=sigma_d)
    row["run_id"] = run_id
    return {col: row[col] for col in COLUMNS}


def _init_worker():
    global _world
    _world = W.create_world()  # one PyBullet client per process


def _job(args):
    run_id, condition = args
    return run_one(_world, run_id, condition)


def main(stress=False):
    t0 = time.perf_counter()
    conditions = build_stress_conditions() if stress else build_conditions()
    out = C.STRESS_CSV if stress else C.RAW_CSV
    jobs = list(enumerate(conditions))
    workers = max(1, min(16, mp.cpu_count() - 2))
    with mp.Pool(workers, initializer=_init_worker) as pool:
        rows = list(tqdm(pool.imap_unordered(_job, jobs), total=len(jobs)))
    df = pd.DataFrame(rows, columns=COLUMNS).sort_values("run_id")
    if df.duplicated(KEY).any():
        raise RuntimeError(f"duplicate conditions in {out.name}")
    C.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"{len(df)} rows written to {out} in {time.perf_counter() - t0:.0f} s")


if __name__ == "__main__":
    main(stress="stress" in sys.argv[1:])
