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
    u, v = np.meshgrid(np.arange(C.IMG_W) + 0.5, np.arange(C.IMG_H) + 0.5)
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
