"""Per-trial metrics. Everything here is measured on the TRUE pose, never the ODOM pose."""

import math

import config as C

# the corridor is symmetric about y = 0, so the centreline is y = 0 and the goal lies on it
CENTRELINE_Y = 0.0


def wrap_angle(a):
    # keeps a heading error in (-pi, pi] so 2*pi + 0.1 reads as 0.1, not 6.38
    return math.atan2(math.sin(a), math.cos(a))


def trial_metrics(true_pose, max_abs_y, collided):
    """Metrics dict for one finished trial (fit_fail_frac and runtime_s are added by the runner)."""
    goal_x = C.START_X + C.SUBGOAL_DIST
    miss = math.hypot(goal_x - true_pose["x"], CENTRELINE_Y - true_pose["y"])
    lat = true_pose["y"] - CENTRELINE_Y
    return {
        "final_lat_err": lat,  # signed; take abs() in summaries
        "final_head_err_deg": math.degrees(wrap_angle(true_pose["th"])),
        "max_lat_err": max_abs_y,
        "collided": collided,
        "dist_travelled": true_pose["x"] - C.START_X,
        # the source paper's metric: how far outside the safety radius around the goal we ended
        "drift_paper": max(0.0, miss - C.DRIFT_SAFETY_RADIUS),
        # bool(): the poses are NumPy floats, and a NumPy bool breaks `is True` and JSON dumps
        "success": bool((not collided) and abs(lat) < C.SUCCESS_LAT_M),
    }
