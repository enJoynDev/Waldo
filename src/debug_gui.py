"""Debug only: watch one B1 trial in the PyBullet GUI.

Run from the repo root:  python src\\debug_gui.py [d_eps]     (default 0.01 = 1%)
Green line = TRUE path, blue line = ODOM path (what the robot believes), orange box = robot.
"""

import sys
import time

import pybullet as p

import config as C
import drift as D
import run_trial as R
import world as W

SPEEDUP = 4  # playback speed relative to real time
DRAW_EVERY = 8  # steps between GUI updates, about 30 per second of simulated time


def main(d_eps=0.01, gui=True):
    world = W.create_world(gui=gui)
    # see-through ceiling so the corridor can be watched from above
    p.changeVisualShape(world["ceiling"], -1, rgbaColor=[1, 1, 1, 0])
    p.resetDebugVisualizerCamera(9.0, 90, -60, [5.0, 0.0, 0.0])
    # the real robot body has no visual shape (so the depth camera never sees it); draw a stand-in
    half = [C.ROBOT_LENGTH / 2, C.ROBOT_WIDTH / 2, C.ROBOT_HEIGHT / 2]
    look = p.createVisualShape(p.GEOM_BOX, halfExtents=half, rgbaColor=[0.9, 0.4, 0.1, 1])
    marker = p.createMultiBody(0, -1, look)
    last = {"true": (C.START_X, C.START_Y), "odom": (C.START_X, C.START_Y), "n": 0}

    def on_step(state):
        last["n"] += 1
        if last["n"] % DRAW_EVERY:
            return
        t, o = state["true"], state["odom"]
        quat = p.getQuaternionFromEuler([0, 0, t["th"]])
        p.resetBasePositionAndOrientation(marker, [t["x"], t["y"], C.ROBOT_HEIGHT / 2], quat)
        p.addUserDebugLine([*last["true"], 0.02], [t["x"], t["y"], 0.02], [0, 0.7, 0], 3)
        p.addUserDebugLine([*last["odom"], 0.05], [o["x"], o["y"], 0.05], [0, 0.3, 1], 3)
        last["true"], last["odom"] = (t["x"], t["y"]), (o["x"], o["y"])
        if gui:
            time.sleep(DRAW_EVERY * C.DT / SPEEDUP)

    row = R.run_trial(world, "B1", 0, D.make_params(d_eps=d_eps, sigma_w=0.0), on_step=on_step)
    print(
        f"d_eps={d_eps}: final y={row['final_lat_err']:+.3f} m, "
        f"heading={row['final_head_err_deg']:+.1f} deg, collided={row['collided']}, "
        f"distance={row['dist_travelled']:.2f} m"
    )
    if gui:
        input("Press Enter to close the window...")
    W.close_world()
    return row


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 0.01)
