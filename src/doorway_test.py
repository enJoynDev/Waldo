"""Doorway test: does the confidence gate reject frames when one wall has a gap?"""

from pathlib import Path

import numpy as np
import pandas as pd

import control as K
import drift as D
import world as W
from run_trial import run_trial

SEEDS = range(10)
D_EPS = 0.01
BINS = np.arange(0.0, 11.0, 1.0)  # 1 m bins of true x
OUT = Path("results") / "doorway.csv"


def run_set(doorway):
    """C_both on every seed in one world. Returns (trial rows, [(true x, estimate used)])."""
    world = W.create_world(doorway=doorway)
    log, cur = [], {"x": 0.0}
    original = K.update

    def spy(ctrl, mode, est):
        used = bool(original(ctrl, mode, est))
        log.append((cur["x"], used))
        return used

    def track(state):
        cur["x"] = state["true"]["x"]

    K.update = spy
    try:
        rows = [
            run_trial(world, "C_both", s, D.make_params(d_eps=D_EPS), on_step=track) for s in SEEDS
        ]
    finally:
        K.update = original
        W.close_world()  # one PyBullet client per process
    return rows, log


def reject_by_bin(log):
    x = np.array([a for a, _ in log])
    rejected = np.array([not u for _, u in log])
    frames, _ = np.histogram(x, BINS)
    rej, _ = np.histogram(x[rejected], BINS)
    return frames, np.divide(rej, frames, out=np.zeros(len(frames)), where=frames > 0)


def main():
    tables = []
    for name, doorway in (("normal", None), ("doorway", 1)):
        rows, log = run_set(doorway)
        df = pd.DataFrame(rows)
        print(
            f"\n{name}: |final lateral err| mean {df['final_lat_err'].abs().mean():.4f} m, "
            f"collisions {int(df['collided'].sum())}/{len(df)}, "
            f"success {int(df['success'].sum())}/{len(df)}, "
            f"rejected frames {df['fit_fail_frac'].mean():.2f}"
        )
        frames, frac = reject_by_bin(log)
        for lo, n, f in zip(BINS[:-1], frames, frac, strict=True):
            print(f"  x {lo:4.1f}-{lo + 1:4.1f} m  frames {n:4d}  rejected {f:5.2f}")
            tables.append({"world": name, "x_lo": lo, "frames": n, "rejected_frac": f})
    OUT.parent.mkdir(exist_ok=True)
    pd.DataFrame(tables).to_csv(OUT, index=False)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
