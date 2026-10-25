import numpy as np
import pytest

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


def test_wall_points_drop_floor_and_ceiling_and_z():
    pts = np.array(
        [
            [2.0, 1.0, 0.5],  # wall
            [2.0, 0.0, 0.0],  # floor
            [2.0, 0.0, 1.0],  # ceiling
            [3.0, -1.0, 0.4],  # wall
        ]
    )
    out = P.wall_points_2d(pts)
    assert out.shape == (2, 2)
    assert np.allclose(out, [[2.0, 1.0], [3.0, -1.0]])


def test_only_side_wall_points_remain_in_empty_corridor(world):
    pts = P.depth_to_points(W.render_depth(0.0, 0.0, 0.0))
    xy = P.wall_points_2d(pts)
    assert len(xy) > 1000
    # floor and ceiling points would have |y| well below 1 m
    assert np.abs(xy[:, 1]).min() > 0.9


def _line_with_outliers(seed=0):
    rng = np.random.default_rng(seed)
    x = np.linspace(0.6, 8.0, 300)
    y = 0.05 * x + 0.9 + rng.normal(0.0, 0.01, x.size)
    outliers = np.column_stack([rng.uniform(0.6, 8.0, 100), rng.uniform(-1.0, 0.8, 100)])
    return np.vstack([np.column_stack([x, y]), outliers])


def test_ransac_recovers_known_line_despite_outliers():
    a, b, n = P.ransac_line(_line_with_outliers(), np.random.default_rng(1))
    assert abs(a - 0.05) < 0.01
    assert abs(b - 0.9) < 0.02
    assert n >= 290


def test_ransac_same_seed_same_result():
    xy = _line_with_outliers()
    assert P.ransac_line(xy, np.random.default_rng(1)) == P.ransac_line(
        xy, np.random.default_rng(1)
    )


def test_ransac_returns_none_with_too_few_points():
    assert P.ransac_line(_line_with_outliers()[:5], np.random.default_rng(1)) is None


def _wall_points(py, heading, n=200, seed=0):
    # points on the walls y = +1 and y = -1 seen from a robot at lateral position py
    rng = np.random.default_rng(seed)
    X = rng.uniform(1.0, 8.0, n)
    pts = []
    for wall_y in (1.0, -1.0):
        dx, dy = X - 0.0, wall_y - py
        c, s = np.cos(heading), np.sin(heading)
        pts.append(np.column_stack([dx * c + dy * s, -dx * s + dy * c]))
    return np.vstack(pts)


@pytest.mark.parametrize("py", [-0.4, 0.0, 0.3])
@pytest.mark.parametrize("heading_deg", [-8.0, 0.0, 5.0])
def test_estimate_from_points_recovers_known_pose(py, heading_deg):
    heading = np.radians(heading_deg)
    est = P.estimate_from_points(_wall_points(py, heading), np.random.default_rng(1))
    assert est["ok"]
    assert abs(est["offset"] - py) < 0.01
    assert abs(est["heading"] - heading) < np.radians(0.5)
    assert est["confidence"] > 0.9


def test_estimate_fails_with_only_one_wall():
    pts = _wall_points(0.0, 0.0)
    est = P.estimate_from_points(pts[pts[:, 1] > 0], np.random.default_rng(1))
    assert not est["ok"]
    assert est["confidence"] == 0.0


def test_estimate_pose_on_rendered_pose_grid(world):
    rng = np.random.default_rng(0)
    for y in (-0.4, 0.0, 0.3):
        for heading_deg in (-8.0, 0.0, 5.0):
            heading = np.radians(heading_deg)
            est = P.estimate_pose(W.render_depth(0.0, y, heading), rng)
            assert est["ok"]
            assert abs(est["offset"] - y) < 0.05
            assert abs(est["heading"] - heading) < np.radians(2.0)
