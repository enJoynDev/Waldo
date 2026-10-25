"""One closed-loop trial -> one metrics dict. Sprint 1 covers B1 (odometry only) only."""

import time

import config as C
import drift as D
import metrics as M
import world as W


def _command(mode, state):
    # B1 trusts odometry: drive straight at nominal speed and never steer
    if mode == "B1":
        return C.SPEED, 0.0
    raise NotImplementedError(f"mode {mode} arrives in a later sprint")


def run_trial(world, mode, seed, params, sigma_d=C.SIGMA_D_DEFAULT, on_step=None):
    """Run one trial in an existing world. Returns one row of results.

    on_step(state) is an optional hook called after every step (used by the GUI debug script).
    """
    t0 = time.perf_counter()
    state, noise = D.new_state(), D.make_noise(seed)
    W.set_robot_pose(world, C.START_X, C.START_Y, C.START_HEADING)  # undo the previous trial
    max_abs_y, collided = 0.0, False
    # the controller only reads ODOM; TRUE drives the simulator and the metrics
    while state["odom"]["x"] < C.SUBGOAL_DIST and state["t"] < C.MAX_TRIAL_TIME:
        v, w = _command(mode, state)
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
    row["fit_fail_frac"] = float("nan")  # B1 never fits walls, so this is not applicable
    row["runtime_s"] = time.perf_counter() - t0
    return row


def main():
    world = W.create_world()  # one PyBullet client per process
    print("B1, seed 0, no noise: d_eps  final_y  head_deg  collided  dist  success")
    for d_eps in C.D_EPS_LEVELS:
        params = D.make_params(d_eps=d_eps, sigma_w=0.0)
        r = run_trial(world, "B1", 0, params)
        print(
            f"  {d_eps:.4f}  {r['final_lat_err']:+.3f}  {r['final_head_err_deg']:+6.2f}  "
            f"{r['collided']!s:5}  {r['dist_travelled']:.2f}  {r['success']}"
        )
    W.close_world()


if __name__ == "__main__":
    main()
