import pytest

import world as W


@pytest.fixture(scope="module")
def world():
    # one PyBullet client per test module, closed afterwards
    w = W.create_world()
    yield w
    W.close_world()
