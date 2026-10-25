import math

import numpy as np
import pytest

import config as C
import world as W


def test_depth_buffer_endpoints():
    # buffer 0 is the near plane, buffer 1 is the far plane
    assert W.depth_to_metres(0.0) == pytest.approx(C.NEAR)
    assert W.depth_to_metres(1.0) == pytest.approx(C.FAR)


def test_depth_conversion_is_increasing():
    buf = np.linspace(0, 1, 50)
    assert np.all(np.diff(W.depth_to_metres(buf)) > 0)


def test_depth_image_is_clean(world):
    W.set_robot_pose(world, 0, 0, 0)
    d = W.render_depth(0, 0, 0)
    assert d.shape == (C.IMG_H, C.IMG_W)
    assert not np.isnan(d).any()  # the closed corridor must leave no ray without a hit
    assert d.min() >= C.NEAR and d.max() <= C.FAR + 1e-3


def test_wall_distance_matches_geometry(world):
    # leftmost pixel of the middle row looks along the FOV edge and hits the wall at y = 1
    d = W.render_depth(0, 0, 0)
    expected = (C.CORRIDOR_WIDTH / 2) / math.tan(math.radians(C.FOV_H_DEG / 2))
    assert d[C.IMG_H // 2, 0] == pytest.approx(expected, abs=0.02)
    assert d[C.IMG_H // 2, -1] == pytest.approx(expected, abs=0.02)


def test_wall_gets_closer_when_robot_moves_toward_it(world):
    centred = W.render_depth(0, 0, 0)[C.IMG_H // 2, 0]
    shifted = W.render_depth(0, 0.5, 0)[C.IMG_H // 2, 0]
    assert shifted == pytest.approx(centred / 2, abs=0.02)  # half the distance to the left wall


@pytest.mark.parametrize(
    "y, heading, hit",
    [(0.0, 0.0, False), (0.66, 0.0, False), (0.67, 0.0, True), (-0.67, 0.0, True)]
    + [(0.5, 0.3, False), (0.55, 0.3, True)],
)
def test_collision_threshold(world, y, heading, hit):
    W.set_robot_pose(world, 0, y, heading)
    assert W.in_collision(world) is hit


def test_depth_noise(world):
    d = W.render_depth(0, 0, 0)
    assert W.add_depth_noise(d, 0.0, np.random.default_rng(0)) is d
    a = W.add_depth_noise(d, 0.02, np.random.default_rng(1))
    b = W.add_depth_noise(d, 0.02, np.random.default_rng(1))
    assert np.array_equal(a, b)  # same rng seed gives the same noise
    inside = d < C.FAR - 0.5  # skip pixels clipped at the far plane
    assert (a - d)[inside].std() == pytest.approx(0.02, rel=0.1)
