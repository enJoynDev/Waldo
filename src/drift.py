"""Drift model: TRUE pose (what really happens) vs ODOM pose (what the controller believes)."""

import math

import numpy as np

import config as C


def make_params(
    d_eps=C.D_EPS_DEFAULT,
    s_lat=C.S_LAT_DEFAULT,
    sigma_w=C.SIGMA_W_DEFAULT,
    gyro_bias_deg_s=C.GYRO_BIAS_DEG_S,
):
    return {"d_eps": d_eps, "s_lat": s_lat, "sigma_w": sigma_w, "gyro_bias_deg_s": gyro_bias_deg_s}


def make_noise(seed):
    # one child stream per noise source, all drawn up front: every mode run with the same seed
    # sees identical noise even if a trial ends early, which keeps comparisons paired
    wheel, gyro, depth = (np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(3))
    return {
        "wheel": wheel.standard_normal((C.NOISE_N, 2)),  # unit normals, scaled by sigma_w later
        "gyro": gyro.standard_normal(C.NOISE_N),
        "depth_rng": depth,
    }


def new_state():
    start = {"x": C.START_X, "y": C.START_Y, "th": C.START_HEADING}
    # TRUE and ODOM are separate dicts on purpose: mixing them invalidates every result
    return {"true": dict(start), "odom": dict(start), "gyro_th": C.START_HEADING, "t": 0.0}


def _advance(pose, v, omega, v_side, dt):
    # midpoint heading keeps the integration second-order accurate for constant omega
    mid = pose["th"] + 0.5 * omega * dt
    pose["x"] += (v * math.cos(mid) - v_side * math.sin(mid)) * dt
    pose["y"] += (v * math.sin(mid) + v_side * math.cos(mid)) * dt
    pose["th"] += omega * dt


def step(state, v_cmd, w_cmd, params, noise):
    """Advance one DT in place. v_cmd, w_cmd: commanded forward speed and yaw rate."""
    k = min(int(state["t"] / C.NOISE_PERIOD), C.NOISE_N - 1)
    half_b = C.WHEEL_BASE / 2
    vl, vr = v_cmd - w_cmd * half_b, v_cmd + w_cmd * half_b  # commanded wheel speeds
    # actual wheel speeds: scale mismatch (split symmetrically) and random noise, TRUE only
    sw = params["sigma_w"]
    vl_t = vl * (1 - params["d_eps"] / 2) * (1 + sw * noise["wheel"][k, 0])
    vr_t = vr * (1 + params["d_eps"] / 2) * (1 + sw * noise["wheel"][k, 1])
    v_t, w_t = (vl_t + vr_t) / 2, (vr_t - vl_t) / C.WHEEL_BASE
    _advance(state["true"], v_t, w_t, params["s_lat"] * v_t, C.DT)
    # odometry integrates the commanded motion, so it never sees the injected error
    _advance(state["odom"], v_cmd, w_cmd, 0.0, C.DT)
    # gyro reads the TRUE yaw rate plus a constant bias and white noise (used by B2 only)
    bias = math.radians(params["gyro_bias_deg_s"])
    state["gyro_th"] += (w_t + bias + math.radians(C.GYRO_NOISE_DEG_S) * noise["gyro"][k]) * C.DT
    state["t"] += C.DT
    return state
