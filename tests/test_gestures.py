"""
VelocityCV — Unit Tests for Dual-Hand Gestures
Tests hand closedness (fist), palm openness / shrink calculation, and steering roll.
"""

from dataclasses import dataclass
import pytest
from vision.gestures import GestureClassifier


@dataclass
class SyntheticPoint:
    x: float
    y: float
    z: float = 0.0


def create_base_landmarks() -> list:
    pts = [SyntheticPoint(0.5, 0.8, 0.0) for _ in range(21)]
    pts[0] = SyntheticPoint(0.5, 0.8, 0.0)

    # Thumb
    pts[1] = SyntheticPoint(0.45, 0.75, 0.0)
    pts[2] = SyntheticPoint(0.40, 0.70, 0.0)
    pts[3] = SyntheticPoint(0.36, 0.65, 0.0)
    pts[4] = SyntheticPoint(0.32, 0.60, 0.0)

    # Index
    pts[5] = SyntheticPoint(0.45, 0.60, 0.0)
    pts[6] = SyntheticPoint(0.44, 0.50, 0.0)
    pts[7] = SyntheticPoint(0.43, 0.40, 0.0)
    pts[8] = SyntheticPoint(0.42, 0.30, 0.0)

    # Middle
    pts[9] = SyntheticPoint(0.50, 0.58, 0.0)
    pts[10] = SyntheticPoint(0.50, 0.48, 0.0)
    pts[11] = SyntheticPoint(0.50, 0.38, 0.0)
    pts[12] = SyntheticPoint(0.50, 0.28, 0.0)

    # Ring
    pts[13] = SyntheticPoint(0.55, 0.60, 0.0)
    pts[14] = SyntheticPoint(0.56, 0.50, 0.0)
    pts[15] = SyntheticPoint(0.57, 0.40, 0.0)
    pts[16] = SyntheticPoint(0.58, 0.30, 0.0)

    # Pinky
    pts[17] = SyntheticPoint(0.60, 0.63, 0.0)
    pts[18] = SyntheticPoint(0.62, 0.54, 0.0)
    pts[19] = SyntheticPoint(0.64, 0.45, 0.0)
    pts[20] = SyntheticPoint(0.66, 0.35, 0.0)

    return pts


@pytest.fixture
def classifier() -> GestureClassifier:
    return GestureClassifier(pinch_threshold=0.35)


def test_open_palm_and_shrink(classifier: GestureClassifier) -> None:
    landmarks = create_base_landmarks()
    size = classifier.calculate_hand_size(landmarks)

    # Wide open palm
    openness = classifier.calculate_palm_openness(landmarks, size)
    assert openness > 0.75
    assert not classifier.is_hand_closed(landmarks, size)

    # Shrunk palm (fingertips drawn closer)
    for i in (4, 8, 12, 16, 20):
        landmarks[i].y += 0.18
    shrunk_openness = classifier.calculate_palm_openness(landmarks, size)
    assert shrunk_openness < openness


def test_closed_fist(classifier: GestureClassifier) -> None:
    landmarks = create_base_landmarks()
    # Curl all fingers close to palm/wrist
    landmarks[4] = SyntheticPoint(0.46, 0.68, 0.0)
    landmarks[8] = SyntheticPoint(0.45, 0.62, 0.0)
    landmarks[12] = SyntheticPoint(0.50, 0.60, 0.0)
    landmarks[16] = SyntheticPoint(0.55, 0.62, 0.0)
    landmarks[20] = SyntheticPoint(0.60, 0.65, 0.0)

    size = classifier.calculate_hand_size(landmarks)
    assert classifier.is_hand_closed(landmarks, size)
    assert classifier.calculate_palm_openness(landmarks, size) == 0.0
