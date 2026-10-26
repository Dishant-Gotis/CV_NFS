"""
VelocityCV — Unit Tests for Signal Filters
Tests One-Euro filter stability, deadzone curve, hysteresis, and debouncer.
"""

import pytest
from vision.filters import (
    Debouncer,
    HysteresisThreshold,
    OneEuroFilter,
    apply_deadzone_and_curve,
)


def test_deadzone_and_curve() -> None:
    # Within deadzone (8 deg default)
    assert apply_deadzone_and_curve(0.0) == 0.0
    assert apply_deadzone_and_curve(5.0) == 0.0
    assert apply_deadzone_and_curve(-7.9) == 0.0

    # Outside deadzone
    steer_pos = apply_deadzone_and_curve(25.0)
    assert 0.0 < steer_pos < 1.0

    steer_neg = apply_deadzone_and_curve(-25.0)
    assert -1.0 < steer_neg < 0.0
    assert pytest.approx(abs(steer_neg), 0.01) == steer_pos

    # Max clamp at 45 deg
    assert apply_deadzone_and_curve(45.0) == 1.0
    assert apply_deadzone_and_curve(60.0) == 1.0
    assert apply_deadzone_and_curve(-50.0) == -1.0


def test_one_euro_filter_smoothing() -> None:
    f = OneEuroFilter(min_cutoff=1.0, beta=0.05)
    t = 100.0

    # Start at 0
    val = f.filter(0.0, timestamp=t)
    assert val == 0.0

    # Step to 1.0
    t += 0.033
    val = f.filter(1.0, timestamp=t)
    # Filter should smooth the sudden jump (val < 1.0)
    assert 0.0 < val < 1.0

    # Hold at 1.0 over time -> converges to 1.0
    for _ in range(30):
        t += 0.033
        val = f.filter(1.0, timestamp=t)
    assert pytest.approx(val, 0.01) == 1.0


def test_hysteresis_threshold() -> None:
    h = HysteresisThreshold(enter_threshold=0.30, exit_threshold=0.40)
    assert not h.active

    # Move to 0.35: not below enter threshold -> stays inactive
    assert not h.update(0.35)

    # Cross below 0.30 -> becomes active
    assert h.update(0.25)
    assert h.active

    # Rises to 0.35 -> still active because exit threshold is 0.40
    assert h.update(0.35)
    assert h.active

    # Crosses above 0.40 -> becomes inactive
    assert not h.update(0.42)
    assert not h.active


def test_debouncer() -> None:
    d = Debouncer(required_frames=3, initial_state="neutral")

    # One frame of open_palm -> output still neutral
    assert d.update("open_palm") == "neutral"
    # Second frame
    assert d.update("open_palm") == "neutral"
    # Third consecutive frame -> state changes to open_palm
    assert d.update("open_palm") == "open_palm"
    # Stays open_palm
    assert d.update("open_palm") == "open_palm"

    # Single glitch frame to fist -> ignored
    assert d.update("fist") == "open_palm"
