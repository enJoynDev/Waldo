"""One closed-loop trial in any mode -> one metrics dict."""

import time

import numpy as np

import config as C
import control as K
import drift as D
import metrics as M
import perception as P
import world as W

DEPTH_MODES = ("C_lat", "C_head", "C_both")


def _command(mode, state, ctrl):
    # B1 trusts odometry: drive straight and never steer
    if mode == "B1":
        return C.SPEED, 0.0
    # B2 holds the simulated gyro heading at the start heading
    if mode == "B2":
        heading = M.wrap_angle(state["gyro_th"] - C.START_HEADING)
        return C.SPEED, K.correction("B2", 0.0, heading)
    # C modes steer with the latest wall-based correction, held between camera frames
    return C.SPEED, ctrl["w_corr"]


def run_trial(world, mode, seed, params, sigma_d=C.SIGMA_D_DEFAULT, on_step=None):
    """Run one trial in an existing world. Returns one row of results.

    on_step(state) is an optional hook called after every step (used by the GUI debug script).
    """
    if mode not in C.MODES:
        raise ValueError(f"unknown mode {mode!r}, expected one of {C.MODES}")
    t0 = time.perf_counter()
    state, noise = D.new_state(), D.make_noise(seed)
    # RANSAC gets its own stream; child 3 leaves the three streams in make_noise unchanged
    ransac_rng = np.random.default_rng(np.random.SeedSequence(seed).spawn(4)[3])
    ctrl = K.new_controller()
    W.set_robot_pose(world, C.START_X, C.START_Y, C.START_HEADING)  # undo the previous trial
    max_abs_y, collided = 0.0, False
    frames, used, next_frame = 0, 0, 0
    # the controller never reads TRUE pose: B1 uses nothing, B2 the gyro, C modes the camera
    while state["odom"]["x"] < C.SUBGOAL_DIST and state["t"] < C.MAX_TRIAL_TIME:
        if mode in DEPTH_MODES and state["t"] >= next_frame * C.CAMERA_PERIOD - 1e-9:
            t = state["true"]  # the camera sits on the real robot, so it renders from TRUE
            depth = W.render_depth(t["x"], t["y"], t["th"])
            depth = W.add_depth_noise(depth, sigma_d, noise["depth_rng"])
            used += int(K.update(ctrl, mode, P.estimate_pose(depth, ransac_rng)))
            frames += 1
            next_frame += 1
        v, w = _command(mode, state, ctrl)
        D.step(state, v, w, params, noise)
        true = state["true"]
        W.set_robot_pose(world, true["x"], true["y"], true["th"])
        max_abs_y = max(max_abs_y, abs(true["y"]))
        if on_step:
            on_step(state)
        if W.in_collision(world):
            collided = True
            break
    row = {
        "seed": seed,
        "mode": mode,
        "d_eps": params["d_eps"],
        "s_lat": params["s_lat"],
        "sigma_w": params["sigma_w"],
        "sigma_d": sigma_d,
    }
    row.update(M.trial_metrics(state["true"], max_abs_y, collided))
    # share of camera frames where the estimate was not used (low confidence or failed fit)
    row["fit_fail_frac"] = 1 - used / frames if frames else float("nan")
    row["runtime_s"] = time.perf_counter() - t0
    return row


def main():
    world = W.create_world()  # one PyBullet client per process
    print("seed 0, d_eps 1%, default noise: mode  final_y  head_deg  collided  dist  success  fail")
    for mode in C.MODES:
        r = run_trial(world, mode, 0, D.make_params(d_eps=0.01))
        print(
            f"  {mode:7} {r['final_lat_err']:+.3f}  {r['final_head_err_deg']:+6.2f}  "
            f"{r['collided']!s:5}  {r['dist_travelled']:.2f}  {r['success']!s:5}  "
            f"{r['fit_fail_frac']:.2f}  {r['runtime_s']:.1f}s"
        )
    W.close_world()


if __name__ == "__main__":
    main()
