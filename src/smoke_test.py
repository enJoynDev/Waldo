"""Smoke test: PyBullet runs headless and renders a correct, NaN-free metric depth image.

Run from the repo root:  python src\\smoke_test.py
"""

import time

import numpy as np
import pybullet as p

# These values move to config.py in Sprint 1
W, H = 320, 240
FOV_DEG = 87.0  # assumed D455 horizontal FOV, verify against the datasheet
NEAR, FAR = 0.1, 10.0
CORRIDOR_W = 2.0
WALL_H = 1.0
WALL_X = 3.0  # known distance used to check the depth conversion
X0, X1 = -1.0, 12.0  # corridor spans x0..x1 so no ray escapes behind or beside the camera


def add_box(center, half_extents):
    # static box (mass 0) used for walls, floor, ceiling and the end target
    col = p.createCollisionShape(p.GEOM_BOX, halfExtents=half_extents)
    vis = p.createVisualShape(p.GEOM_BOX, halfExtents=half_extents, rgbaColor=[0.8, 0.8, 0.8, 1])
    return p.createMultiBody(0, col, vis, basePosition=center)


def depth_to_metres(buf):
    # PyBullet returns a non-linear depth buffer in [0, 1]; convert to metres (z-depth)
    return FAR * NEAR / (FAR - (FAR - NEAR) * buf)


def render_depth(eye, target):
    view = p.computeViewMatrix(eye, target, [0, 0, 1])
    # PyBullet takes a VERTICAL fov; convert from horizontal using the aspect ratio
    vfov = np.degrees(2 * np.arctan(np.tan(np.radians(FOV_DEG) / 2) * H / W))
    proj = p.computeProjectionMatrixFOV(vfov, W / H, NEAR, FAR)
    _, _, _, buf, _ = p.getCameraImage(W, H, view, proj, renderer=p.ER_TINY_RENDERER)
    return depth_to_metres(np.array(buf).reshape(H, W))


def build_corridor():
    cx, hx = (X0 + X1) / 2, (X1 - X0) / 2
    hw, hh = CORRIDOR_W / 2, WALL_H / 2
    add_box([cx, hw + 0.05, hh], [hx, 0.05, hh])  # left wall
    add_box([cx, -hw - 0.05, hh], [hx, 0.05, hh])  # right wall
    add_box([cx, 0, -0.05], [hx, hw + 0.1, 0.05])  # floor
    # ceiling: without it, rays that hit nothing return NaN in the depth buffer
    add_box([cx, 0, WALL_H + 0.05], [hx, hw + 0.1, 0.05])
    add_box([WALL_X + 0.05, 0, hh], [0.05, hw, hh])  # front face at x = WALL_X


def main():
    p.connect(p.DIRECT)  # headless, no window
    build_corridor()

    eye = [0.0, 0.0, 0.4]
    target = [1.0, 0.0, 0.4]
    depth = render_depth(eye, target)
    print(f"depth image shape: {depth.shape}")
    print(f"depth min/max (m): {np.nanmin(depth):.3f} / {np.nanmax(depth):.3f}")
    print(f"NaN pixels: {int(np.isnan(depth).sum())}")

    centre = depth[H // 2, W // 2]
    print(f"centre pixel depth: {centre:.3f} m (expected about {WALL_X:.3f})")
    # catches a wrong depth-buffer conversion, the most likely silent bug
    assert abs(centre - WALL_X) < 0.05, "depth conversion looks wrong"
    assert np.isfinite(depth).all(), "NaN depth: some rays hit nothing"
    assert depth.min() >= NEAR - 1e-3 and depth.max() <= FAR + 1e-3

    # timing: this number sizes the experiment sweep
    n = 20
    t0 = time.perf_counter()
    for _ in range(n):
        render_depth(eye, target)
    ms = (time.perf_counter() - t0) / n * 1000
    print(f"render time: {ms:.1f} ms per frame at {W}x{H}")
    print("SMOKE TEST PASSED")
    p.disconnect()


if __name__ == "__main__":
    main()
