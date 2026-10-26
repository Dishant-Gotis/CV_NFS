"""
VelocityCV — Unit Tests for Dual-Hand Control Mapper
Tests:
- Left hand closed -> steer left
- Right hand closed -> steer right
- Both hands closed -> brake
- Palm shrink -> throttle speed control
"""

from dataclasses import dataclass
import pytest
from game.config import DEFAULT_CONFIG
from vision.control_mapper import ControlMapper
from vision.hand_tracker import DetectedHand


@dataclass
class SyntheticPoint:
    x: float
    y: float
    z: float = 0.0


def make_open_landmarks(cx: float) -> list:
    pts = [SyntheticPoint(cx, 0.7, 0.0) for _ in range(21)]
    pts[0] = SyntheticPoint(cx, 0.7, 0.0)
    # MCPs
    pts[5] = SyntheticPoint(cx - 0.04, 0.55, 0.0)
    pts[9] = SyntheticPoint(cx, 0.52, 0.0)
    pts[13] = SyntheticPoint(cx + 0.04, 0.55, 0.0)
    pts[17] = SyntheticPoint(cx + 0.08, 0.58, 0.0)
    # PIPs
    pts[2] = SyntheticPoint(cx - 0.08, 0.58, 0.0)
    pts[6] = SyntheticPoint(cx - 0.04, 0.44, 0.0)
    pts[10] = SyntheticPoint(cx, 0.42, 0.0)
    pts[14] = SyntheticPoint(cx + 0.04, 0.44, 0.0)
    pts[18] = SyntheticPoint(cx + 0.08, 0.48, 0.0)
    # Extended fingertips
    pts[4] = SyntheticPoint(cx - 0.12, 0.50, 0.0)
    pts[8] = SyntheticPoint(cx - 0.04, 0.28, 0.0)
    pts[12] = SyntheticPoint(cx, 0.25, 0.0)
    pts[16] = SyntheticPoint(cx + 0.04, 0.28, 0.0)
    pts[20] = SyntheticPoint(cx + 0.08, 0.32, 0.0)
    return pts


def make_closed_landmarks(cx: float) -> list:
    pts = [SyntheticPoint(cx, 0.7, 0.0) for _ in range(21)]
    pts[0] = SyntheticPoint(cx, 0.7, 0.0)
    # MCPs
    pts[5] = SyntheticPoint(cx - 0.04, 0.55, 0.0)
    pts[9] = SyntheticPoint(cx, 0.52, 0.0)
    pts[13] = SyntheticPoint(cx + 0.04, 0.55, 0.0)
    pts[17] = SyntheticPoint(cx + 0.08, 0.58, 0.0)
    # PIPs (pointing up)
    pts[2] = SyntheticPoint(cx - 0.06, 0.60, 0.0)
    pts[6] = SyntheticPoint(cx - 0.04, 0.48, 0.0)
    pts[10] = SyntheticPoint(cx, 0.46, 0.0)
    pts[14] = SyntheticPoint(cx + 0.04, 0.48, 0.0)
    pts[18] = SyntheticPoint(cx + 0.08, 0.52, 0.0)
    # Curled fingertips (pointing down towards palm/wrist)
    pts[4] = SyntheticPoint(cx - 0.03, 0.65, 0.0)
    pts[8] = SyntheticPoint(cx - 0.04, 0.58, 0.0)
    pts[12] = SyntheticPoint(cx, 0.56, 0.0)
    pts[16] = SyntheticPoint(cx + 0.04, 0.58, 0.0)
    pts[20] = SyntheticPoint(cx + 0.08, 0.62, 0.0)
    return pts


@pytest.fixture
def mapper() -> ControlMapper:
    return ControlMapper(config=DEFAULT_CONFIG)


def test_dual_hand_steer_left(mapper: ControlMapper) -> None:
    # Left hand is closed, Right hand is open
    h_left = DetectedHand(landmarks=make_closed_landmarks(0.3), handedness="Left", confidence=0.95)
    h_right = DetectedHand(landmarks=make_open_landmarks(0.7), handedness="Right", confidence=0.95)

    t = 10.0
    for _ in range(10):
        t += 0.033
        state = mapper.process_hands([h_left, h_right], timestamp=t)

    assert state.steering < -0.3   # Steers left!
    assert state.brake == 0.0
    assert state.throttle > 0.0    # Right hand controls speed


def test_dual_hand_steer_right(mapper: ControlMapper) -> None:
    # Right hand is closed, Left hand is open
    h_left = DetectedHand(landmarks=make_open_landmarks(0.3), handedness="Left", confidence=0.95)
    h_right = DetectedHand(landmarks=make_closed_landmarks(0.7), handedness="Right", confidence=0.95)

    t = 10.0
    for _ in range(10):
        t += 0.033
        state = mapper.process_hands([h_left, h_right], timestamp=t)

    assert state.steering > 0.3    # Steers right!
    assert state.brake == 0.0
    assert state.throttle > 0.0    # Left hand controls speed


def test_dual_hand_both_closed_brake(mapper: ControlMapper) -> None:
    # Both hands closed -> BRAKE
    h_left = DetectedHand(landmarks=make_closed_landmarks(0.3), handedness="Left", confidence=0.95)
    h_right = DetectedHand(landmarks=make_closed_landmarks(0.7), handedness="Right", confidence=0.95)

    t = 10.0
    for _ in range(10):
        t += 0.033
        state = mapper.process_hands([h_left, h_right], timestamp=t)

    assert state.brake > 0.5       # Brake active!
    assert state.throttle == 0.0
