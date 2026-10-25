"""Controller: turn wall estimates into an angular-velocity correction."""

import numpy as np

import config as C

# which terms each mode uses: (lateral, heading)
_TERMS = {"C_lat": (1.0, 0.0), "C_head": (0.0, 1.0), "C_both": (1.0, 1.0)}


def correction(mode, offset, heading):
    """PD-style steering correction in rad/s, clipped to +-OMEGA_MAX.

    offset: robot y relative to the corridor centre (left positive, metres).
    heading: robot heading relative to the corridor axis (left positive, radians).
    Positive omega turns left, so a robot left of centre or turned left steers right (negative).
    """
    use_lat, use_head = _TERMS[mode]
    omega = -(use_lat * C.K_LAT * offset + use_head * C.K_HEAD * heading)
    return float(np.clip(omega, -C.OMEGA_MAX, C.OMEGA_MAX))


def new_controller():
    return {"w_corr": 0.0, "stale": 0}


def update(ctrl, mode, est):
    """Call once per camera frame with a wall estimate. Returns True if the estimate was used.

    A confident estimate sets the correction. Otherwise the last correction is held for
    CONTROL_HOLD_FRAMES frames, then dropped to zero (odometry-only behaviour).
    """
    if est["ok"] and est["confidence"] >= C.CONF_THRESHOLD:
        ctrl["w_corr"] = correction(mode, est["offset"], est["heading"])
        ctrl["stale"] = 0
        return True
    ctrl["stale"] += 1
    if ctrl["stale"] > C.CONTROL_HOLD_FRAMES:
        ctrl["w_corr"] = 0.0
    return False
