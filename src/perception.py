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
