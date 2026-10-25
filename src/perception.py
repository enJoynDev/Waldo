"""Perception: turn a depth image into corridor-wall measurements."""

import math

import numpy as np

import config as C


def depth_to_points(depth):
    """Back-project a metric depth image to 3D points in the robot frame.

    Frame: x forward, y left, z up (height above the floor). The camera sits at
    (0, 0, CAMERA_HEIGHT), looks along +x and has no tilt. The render gives depth along
    the optical axis, so x = depth directly. Readings that are NaN, closer than CAMERA_MIN_DEPTH,
    or at the far clip (FAR, meaning "nothing hit") are dropped. Returns an (N, 3) array.
    """
    f = (C.IMG_W / 2) / math.tan(math.radians(C.FOV_H_DEG) / 2)  # focal length in pixels
    # PyBullet's depth image puts the ray for pixel (col, row) through the integer index,
    # not the pixel centre: adding 0.5 gave a 0.34 degree heading bias (found in the sweep)
    u, v = np.meshgrid(np.arange(C.IMG_W), np.arange(C.IMG_H))
    x = depth
    y = -(u - C.IMG_W / 2) / f * depth  # column right of centre means robot-right, so negative y
    z = C.CAMERA_HEIGHT - (v - C.IMG_H / 2) / f * depth  # row below centre means lower
    keep = np.isfinite(depth) & (depth >= C.CAMERA_MIN_DEPTH) & (depth < C.CAMERA_MAX_DEPTH)
    return np.stack([x[keep], y[keep], z[keep]], axis=1)


def wall_points_2d(points):
    """Keep only wall-height points and drop z: top-down (x, y) points, shape (N, 2)."""
    keep = (points[:, 2] > C.WALL_Z_MIN) & (points[:, 2] < C.WALL_Z_MAX)
    return points[keep][:, :2]


def ransac_line(xy, rng):
    """Fit y = a*x + b to (N, 2) points with RANSAC.

    Returns (a, b, n_inliers), or None if there are fewer than RANSAC_MIN_POINTS points.
    Each iteration fits a line through two random points; the line with the most points
    within RANSAC_THRESHOLD (vertical distance, metres) wins and is refitted by least
    squares on its inliers.
    """
    n = len(xy)
    if n < C.RANSAC_MIN_POINTS:
        return None
    x, y = xy[:, 0], xy[:, 1]
    i, j = rng.integers(0, n, size=(2, C.RANSAC_ITERS))
    dx = x[j] - x[i]
    ok = np.abs(dx) > 1e-6  # a pair with equal x gives no usable line
    i, j, dx = i[ok], j[ok], dx[ok]
    if len(i) == 0:
        return None
    a = (y[j] - y[i]) / dx
    b = y[i] - a * x[i]
    resid = np.abs(y[None, :] - (a[:, None] * x[None, :] + b[:, None]))  # (iters, N)
    inliers = resid < C.RANSAC_THRESHOLD
    best = np.argmax(inliers.sum(axis=1))
    mask = inliers[best]
    a, b = np.polyfit(x[mask], y[mask], 1)
    return float(a), float(b), int(mask.sum())


def estimate_from_points(xy, rng):
    """Offset, heading error and confidence from top-down wall points.

    Sign convention matches TRUE pose: offset is the robot's y (left positive) relative to
    the corridor centre, heading is its angle (left positive) relative to the corridor axis.
    The walls are found by sequential RANSAC (strongest line, remove its inliers, fit again)
    rather than by the sign of y, because a turned robot sees a near wall cross y = 0.
    The line with the larger intercept is the left wall.
    On failure (second wall missing) returns NaN offset/heading, confidence 0, ok False.
    """
    fail = {"offset": float("nan"), "heading": float("nan"), "confidence": 0.0, "ok": False}
    first = ransac_line(xy, rng)
    if first is None:
        return fail
    a1, b1, _ = first
    on_first = np.abs(xy[:, 1] - (a1 * xy[:, 0] + b1)) < C.RANSAC_THRESHOLD
    second = ransac_line(xy[~on_first], rng)
    if second is None:
        return fail
    a2, b2, n2 = second
    (a_l, b_l), (a_r, b_r) = sorted([(a1, b1), (a2, b2)], key=lambda f: -f[1])
    heading = -math.atan((a_l + a_r) / 2)
    cos_h = math.cos(heading)
    offset = -(b_l + b_r) * cos_h / 2
    width = (b_l - b_r) * cos_h
    inlier_frac = (on_first.sum() + n2) / len(xy)  # share of wall points the two lines explain
    width_ok = max(0.0, 1.0 - abs(width - C.CORRIDOR_WIDTH) / C.CONF_WIDTH_TOL)
    return {"offset": offset, "heading": heading, "confidence": inlier_frac * width_ok, "ok": True}


def estimate_pose(depth, rng):
    """Full perception pipeline: depth image to offset, heading error and confidence."""
    return estimate_from_points(wall_points_2d(depth_to_points(depth)), rng)
