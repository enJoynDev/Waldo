"""Demo: B1, B2 and C_both on the same seed in the PyBullet GUI, then a results table.

Run from the repo root:  python src\\demo.py [d_eps] [seed]     (defaults 0.01 and 0)
Red = B1 (odometry only), orange = B2 (odometry + gyro), teal = C_both (wall correction).
The grey lines are the start and the 10 m goal. The legend shows each result when its run ends.
"""

import sys
import time

import pybullet as p

import config as C
import drift as D
import run_trial as R
import world as W

MODES = ("B1", "B2", "C_both")
COLOURS = {"B1": [0.9, 0.1, 0.1], "B2": [1.0, 0.6, 0.0], "C_both": [0.0, 0.65, 0.7]}
LABELS = {"B1": "B1: odometry", "B2": "B2: + gyro", "C_both": "C_both: depth"}
SPEEDUP = 4  # playback speed relative to real time
DRAW_EVERY = 8  # steps between GUI updates
HIDE_UI = False  # hide PyBullet's Explorer and Params panels; set False if the previews vanish
TEXT_SIZE = 1.4


def legend_pos(row):
    scale = max(1.0, C.SUBGOAL_DIST / 10)
    return [0.5 + 1.0 * scale * row, C.CORRIDOR_WIDTH / 2 + 0.5, C.WALL_HEIGHT + 0.2]


def setup_view(world):
    # see-through ceiling so the corridor can be watched from above
    p.changeVisualShape(world["ceiling"], -1, rgbaColor=[1, 1, 1, 0])
    p.resetDebugVisualizerCamera(
        max(9.0, 0.9 * C.SUBGOAL_DIST), 90, -60, [C.SUBGOAL_DIST / 2, 0.0, 0.0]
    )
    p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0 if HIDE_UI else 1)
    # keep the robot's own colour and depth views, drop the segmentation one
    p.configureDebugVisualizer(p.COV_ENABLE_RGB_BUFFER_PREVIEW, 1)
    p.configureDebugVisualizer(p.COV_ENABLE_DEPTH_BUFFER_PREVIEW, 1)
    p.configureDebugVisualizer(p.COV_ENABLE_SEGMENTATION_MARK_PREVIEW, 1)


def draw_course():
    grey = [0.15, 0.15, 0.15]
    half = C.CORRIDOR_WIDTH / 2
    for x, name, y in (
        (C.START_X, "start", -2.6),
        (C.SUBGOAL_DIST, f"{C.SUBGOAL_DIST:.0f} m goal", -3.4),
    ):
        p.addUserDebugLine([x, -half, 0.03], [x, half, 0.03], grey, 6)
        p.addUserDebugText(name, [x, y, 0.03], grey, TEXT_SIZE)


def make_marker():
    # the real robot body has no visual shape (so the depth camera never sees it); draw a stand-in
    half = [C.ROBOT_LENGTH / 2, C.ROBOT_WIDTH / 2, C.ROBOT_HEIGHT / 2]
    look = p.createVisualShape(p.GEOM_BOX, halfExtents=half, rgbaColor=[0.25, 0.25, 0.25, 1])
    marker = p.createMultiBody(0, -1, look)
    quat = p.getQuaternionFromEuler([0, 0, C.START_HEADING])
    p.resetBasePositionAndOrientation(marker, [C.START_X, C.START_Y, C.ROBOT_HEIGHT / 2], quat)
    return marker


def run_mode(world, marker, mode, seed, params, readout):
    colour = COLOURS[mode]
    last = {"pt": (C.START_X, C.START_Y), "n": 0}
    t_start = time.perf_counter()

    def on_step(state):
        last["n"] += 1
        if last["n"] % DRAW_EVERY:
            return
        t = state["true"]
        quat = p.getQuaternionFromEuler([0, 0, t["th"]])
        p.resetBasePositionAndOrientation(marker, [t["x"], t["y"], C.ROBOT_HEIGHT / 2], quat)
        p.addUserDebugLine([*last["pt"], 0.03], [t["x"], t["y"], 0.03], colour, 4)
        last["pt"] = (t["x"], t["y"])
        p.addUserDebugText(
            f"now {mode}: x {t['x']:.1f} m, y {t['y']:+.3f} m",
            legend_pos(len(MODES)),
            textColorRGB=colour,
            textSize=TEXT_SIZE,
            replaceItemUniqueId=readout,
        )
        # sleep only for what is left of this step's real-time budget, so drawing cost
        # does not slow the playback
        if mode not in R.DEPTH_MODES and last["n"] % (6 * DRAW_EVERY) == 0:
            W.render_depth(t["x"], t["y"], t["th"])  # display only, fills the previews
        wait = t_start + state["t"] / SPEEDUP - time.perf_counter()
        if wait > 0:
            time.sleep(wait)

    return R.run_trial(world, mode, seed, params, on_step=on_step)


def outcome(mode, r):
    if r["collided"]:
        return f"{LABELS[mode]} | crashed at {r['dist_travelled']:.1f} m"
    return f"{LABELS[mode]} | {abs(r['final_lat_err']) * 100:.1f} cm off"


def main(d_eps=0.01, seed=0, goal=None, width=None):
    # in-process overrides for the demo only; config.py and saved results are not touched
    if goal is not None:
        C.SUBGOAL_DIST = goal
        C.CORRIDOR_X_MAX = max(C.CORRIDOR_X_MAX, goal + 2.0)
    if width is not None:
        C.CORRIDOR_WIDTH = width
    world = W.create_world(gui=True)
    setup_view(world)
    draw_course()
    marker = make_marker()
    legend = {}
    for k, mode in enumerate(MODES):
        legend[mode] = p.addUserDebugText(
            LABELS[mode], legend_pos(k), textColorRGB=COLOURS[mode], textSize=TEXT_SIZE
        )
    readout = p.addUserDebugText(
        "now: -", legend_pos(len(MODES)), textColorRGB=[0.2, 0.2, 0.2], textSize=TEXT_SIZE
    )
    params = D.make_params(d_eps=d_eps)
    rows = []
    for mode in MODES:
        input(f"\nPress Enter to run {LABELS[mode]} (d_eps={d_eps:.1%}, seed {seed})...")
        r = run_mode(world, marker, mode, seed, params, readout)
        rows.append(r)
        p.addUserDebugText(
            outcome(mode, r),
            legend_pos(MODES.index(mode)),
            textColorRGB=COLOURS[mode],
            textSize=TEXT_SIZE,
            replaceItemUniqueId=legend[mode],
        )
        print(f"  {mode}: final y {r['final_lat_err']:+.3f} m, collided {r['collided']}")
    p.addUserDebugText(
        "done",
        legend_pos(len(MODES)),
        textColorRGB=[0.2, 0.2, 0.2],
        textSize=TEXT_SIZE,
        replaceItemUniqueId=readout,
    )
    print(f"\n{'mode':8} {'final y (m)':>12} {'heading (deg)':>14} {'collided':>9} {'success':>8}")
    for r in rows:
        print(
            f"{r['mode']:8} {r['final_lat_err']:+12.3f} {r['final_head_err_deg']:+14.1f} "
            f"{r['collided']!s:>9} {r['success']!s:>8}"
        )
    input("\nPress Enter to close the window...")
    W.close_world()


if __name__ == "__main__":
    a = sys.argv[1:]
    main(
        float(a[0]) if len(a) > 0 else 0.01,
        int(a[1]) if len(a) > 1 else 0,
        float(a[2]) if len(a) > 2 else None,
        float(a[3]) if len(a) > 3 else None,
    )
