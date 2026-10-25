"""PyBullet world: corridor, robot collision body, depth camera. No drift or control here."""

import numpy as np
import pybullet as p

import config as C


def depth_to_metres(buf):
    # PyBullet's depth buffer is non-linear in [0, 1]; this gives metric z-depth
    return C.FAR * C.NEAR / (C.FAR - (C.FAR - C.NEAR) * buf)


def _box(center, half, visible=True):
    col = p.createCollisionShape(p.GEOM_BOX, halfExtents=half)
    vis = p.createVisualShape(p.GEOM_BOX, halfExtents=half) if visible else -1
    return p.createMultiBody(0, col, vis, basePosition=center)


def create_world(gui=False):
    """Connect, build a closed corridor and the robot body. Returns a dict of body ids."""
    # DIRECT (headless) for all experiments; GUI only from debug scripts. One client per process.
    p.connect(p.GUI if gui else p.DIRECT)
    cx = (C.CORRIDOR_X_MIN + C.CORRIDOR_X_MAX) / 2
    hx = (C.CORRIDOR_X_MAX - C.CORRIDOR_X_MIN) / 2
    hw, ht = C.CORRIDOR_WIDTH / 2, C.WALL_THICKNESS / 2
    hh = C.WALL_HEIGHT / 2
    side = hw + ht
    left = _box([cx, side, hh], [hx, ht, hh])
    right = _box([cx, -side, hh], [hx, ht, hh])
    # floor and ceiling: PyBullet returns NaN depth for rays that hit nothing
    _box([cx, 0, -ht], [hx, side, ht])
    ceiling = _box([cx, 0, C.WALL_HEIGHT + ht], [hx, side, ht])
    # no visual shape, so the robot never shows up in its own depth image
    half = [C.ROBOT_LENGTH / 2, C.ROBOT_WIDTH / 2, C.ROBOT_HEIGHT / 2]
    robot = _box([0, 0, C.ROBOT_HEIGHT / 2], half, visible=False)
    return {"robot": robot, "walls": (left, right), "ceiling": ceiling}


def close_world():
    p.disconnect()


def set_robot_pose(world, x, y, heading):
    # kinematic robot: we place it every step, PyBullet never simulates it
    quat = p.getQuaternionFromEuler([0, 0, heading])
    p.resetBasePositionAndOrientation(world["robot"], [x, y, C.ROBOT_HEIGHT / 2], quat)


def in_collision(world):
    # getContactPoints skips static-static pairs, so use closest points (negative gap = overlap)
    for wall in world["walls"]:
        for pt in p.getClosestPoints(world["robot"], wall, distance=0.01):
            if pt[8] <= 0:
                return True
    return False


def render_depth(x, y, heading):
    """Metric depth image (IMG_H, IMG_W) from a forward camera at the given TRUE pose."""
    eye = [x, y, C.CAMERA_HEIGHT]
    target = [x + np.cos(heading), y + np.sin(heading), C.CAMERA_HEIGHT]
    view = p.computeViewMatrix(eye, target, [0, 0, 1])
    proj = p.computeProjectionMatrixFOV(C.FOV_V_DEG, C.IMG_W / C.IMG_H, C.NEAR, C.FAR)
    out = p.getCameraImage(C.IMG_W, C.IMG_H, view, proj, renderer=p.ER_TINY_RENDERER)
    return depth_to_metres(np.array(out[3]).reshape(C.IMG_H, C.IMG_W))


def add_depth_noise(depth, sigma, rng):
    # Gaussian noise on metric depth, clipped to what the sensor could report
    if sigma == 0:
        return depth
    return np.clip(depth + rng.normal(0.0, sigma, depth.shape), C.NEAR, C.FAR)
