import numpy as np

import config as C
import perception as P
import world as W


def test_flat_wall_points_are_at_the_wall_distance():
    depth = np.full((C.IMG_H, C.IMG_W), 3.0)
    pts = P.depth_to_points(depth)
    assert pts.shape == (C.IMG_H * C.IMG_W, 3)
    assert np.allclose(pts[:, 0], 3.0)


def test_close_and_nan_readings_are_dropped():
    depth = np.full((C.IMG_H, C.IMG_W), 3.0)
    depth[0, 0] = np.nan
    depth[1, 1] = C.CAMERA_MIN_DEPTH - 0.01
    assert len(P.depth_to_points(depth)) == C.IMG_H * C.IMG_W - 2


def test_far_clip_readings_are_dropped():
    depth = np.full((C.IMG_H, C.IMG_W), 3.0)
    depth[5, 5] = C.CAMERA_MAX_DEPTH
    assert len(P.depth_to_points(depth)) == C.IMG_H * C.IMG_W - 1


def test_left_is_positive_y_and_up_is_positive_z():
    depth = np.full((C.IMG_H, C.IMG_W), 3.0)
    pts = P.depth_to_points(depth).reshape(C.IMG_H, C.IMG_W, 3)
    assert pts[60, 0, 1] > 0 > pts[60, -1, 1]
    assert pts[0, 80, 2] > C.CAMERA_HEIGHT > pts[-1, 80, 2]


def test_side_walls_land_at_plus_and_minus_one_metre(world):
    pts = P.depth_to_points(W.render_depth(0.0, 0.0, 0.0))
    # between floor and ceiling, near range only: the renderer's depth error grows with distance
    side = pts[(pts[:, 2] > 0.1) & (pts[:, 2] < 0.9) & (pts[:, 0] < 4.0)]
    left, right = side[side[:, 1] > 0.5], side[side[:, 1] < -0.5]
    assert len(left) > 100 and len(right) > 100
    assert np.abs(left[:, 1] - C.CORRIDOR_WIDTH / 2).max() < 0.03
    assert np.abs(right[:, 1] + C.CORRIDOR_WIDTH / 2).max() < 0.03
