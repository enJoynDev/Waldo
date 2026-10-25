import config as C
import control as K

GOOD = {"ok": True, "confidence": 1.0, "offset": 0.3, "heading": 0.0}
BAD = {"ok": False, "confidence": 0.0, "offset": float("nan"), "heading": float("nan")}


def test_robot_left_of_centre_steers_right():
    assert K.correction("C_lat", 0.3, 0.0) < 0


def test_robot_turned_left_steers_right():
    assert K.correction("C_head", 0.0, 0.1) < 0


def test_modes_use_only_their_own_terms():
    assert K.correction("C_lat", 0.0, 0.5) == 0.0
    assert K.correction("C_head", 0.5, 0.0) == 0.0
    both = K.correction("C_both", 0.1, 0.05)
    assert both == K.correction("C_lat", 0.1, 0.0) + K.correction("C_head", 0.0, 0.05)


def test_output_is_clipped():
    assert K.correction("C_both", 5.0, 5.0) == -C.OMEGA_MAX
    assert K.correction("C_both", -5.0, -5.0) == C.OMEGA_MAX


def test_confident_estimate_sets_correction():
    ctrl = K.new_controller()
    assert K.update(ctrl, "C_both", GOOD)
    assert ctrl["w_corr"] == K.correction("C_both", 0.3, 0.0)


def test_low_confidence_holds_then_falls_back():
    ctrl = K.new_controller()
    K.update(ctrl, "C_both", GOOD)
    held = ctrl["w_corr"]
    for _ in range(C.CONTROL_HOLD_FRAMES):
        assert not K.update(ctrl, "C_both", BAD)
        assert ctrl["w_corr"] == held
    K.update(ctrl, "C_both", BAD)
    assert ctrl["w_corr"] == 0.0


def test_estimate_below_threshold_is_not_used():
    ctrl = K.new_controller()
    weak = dict(GOOD, confidence=C.CONF_THRESHOLD - 0.01)
    assert not K.update(ctrl, "C_both", weak)
    assert ctrl["w_corr"] == 0.0
