"""Demo: B1, B2 and C_both on the same seed in the PyBullet GUI, then a results table.

Run from the repo root:  python src\\demo.py [d_eps] [seed]     (defaults 0.01 and 0)
Red = B1 (odometry only), orange = B2 (odometry + gyro), green = C_both (depth correction).
"""

import sys
import time

import pybullet as p

import config as C
import drift as D
import run_trial as R
import world as W

MODES = ("B1", "B2", "C_both")
COLOURS = {"B1": [0.9, 0.1, 0.1], "B2": [1.0, 0.6, 0.0], "C_both": [0.0, 0.7, 0.2]}
LABELS = {
    "B1": "B1: odometry",
    "B2": "B2: + gyro",
    "C_both": "C_both: depth",
}
SPEEDUP = 4  # playback speed relative to real time
DRAW_EVERY = 8  # steps between GUI updates


def run_mode(world, marker, mode, seed, params):
    colour = COLOURS[mode]
    last = {"pt": (C.START_X, C.START_Y), "n": 0}

    def on_step(state):
        last["n"] += 1
        if last["n"] % DRAW_EVERY:
            return
        t = state["true"]
        quat = p.getQuaternionFromEuler([0, 0, t["th"]])
        p.resetBasePositionAndOrientation(marker, [t["x"], t["y"], C.ROBOT_HEIGHT / 2], quat)
        p.addUserDebugLine([*last["pt"], 0.03], [t["x"], t["y"], 0.03], colour, 4)
        last["pt"] = (t["x"], t["y"])
        time.sleep(DRAW_EVERY * C.DT / SPEEDUP)

    return R.run_trial(world, mode, seed, params, on_step=on_step)


def main(d_eps=0.01, seed=0):
    world = W.create_world(gui=True)
    # see-through ceiling so the corridor can be watched from above
    p.changeVisualShape(world["ceiling"], -1, rgbaColor=[1, 1, 1, 0])
    p.resetDebugVisualizerCamera(9.0, 90, -60, [5.0, 0.0, 0.0])
    # the real robot body has no visual shape (so the depth camera never sees it); draw a stand-in
    half = [C.ROBOT_LENGTH / 2, C.ROBOT_WIDTH / 2, C.ROBOT_HEIGHT / 2]
    look = p.createVisualShape(p.GEOM_BOX, halfExtents=half, rgbaColor=[0.3, 0.3, 0.9, 1])
    marker = p.createMultiBody(0, -1, look)
    for k, mode in enumerate(MODES):
        p.addUserDebugText(LABELS[mode], [0.5 + 0.8 * k, 1.3, 0.5], COLOURS[mode], 1.6)
    params = D.make_params(d_eps=d_eps)
    rows = []
    for mode in MODES:
        input(f"\nPress Enter to run {LABELS[mode]} (d_eps={d_eps:.1%}, seed {seed})...")
        rows.append(run_mode(world, marker, mode, seed, params))
        r = rows[-1]
        print(f"  {mode}: final y {r['final_lat_err']:+.3f} m, collided {r['collided']}")
    print(f"\n{'mode':8} {'final y (m)':>12} {'heading (deg)':>14} {'collided':>9} {'success':>8}")
    for r in rows:
        print(
            f"{r['mode']:8} {r['final_lat_err']:+12.3f} {r['final_head_err_deg']:+14.1f} "
            f"{r['collided']!s:>9} {r['success']!s:>8}"
        )
    input("\nPress Enter to close the window...")
    W.close_world()


if __name__ == "__main__":
    args = sys.argv[1:]
    main(float(args[0]) if args else 0.01, int(args[1]) if len(args) > 1 else 0)
