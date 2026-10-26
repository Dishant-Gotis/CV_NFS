"""
VelocityCV — Hand Gesture Recognition
Scale-invariant classification of hand closedness (fist), palm shrink/openness, and tilt.
"""

import math
from typing import Any, Dict, List, Tuple


def euclidean_dist(p1: Any, p2: Any) -> float:
    """Calculates 2D/3D euclidean distance between two landmarks."""
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    dz = getattr(p1, "z", 0.0) - getattr(p2, "z", 0.0)
    return math.sqrt(dx * dx + dy * dy + dz * dz)


class GestureClassifier:
    """Extracts scale-invariant hand closedness and palm openness."""

    def __init__(self, pinch_threshold: float = 0.35):
        self.pinch_threshold = pinch_threshold

    def calculate_hand_size(self, landmarks: List[Any]) -> float:
        """Hand scale metric: distance from wrist (0) to middle-finger base MCP (9)."""
        wrist = landmarks[0]
        middle_mcp = landmarks[9]
        return max(1e-4, euclidean_dist(wrist, middle_mcp))

    def is_finger_extended(self, landmarks: List[Any], finger_idx: int) -> bool:
        """Checks if a given finger is extended using distance from wrist."""
        wrist = landmarks[0]
        finger_map = {
            1: (8, 6),    # Index: (tip, pip)
            2: (12, 10),  # Middle
            3: (16, 14),  # Ring
            4: (20, 18),  # Pinky
        }

        if finger_idx == 0:
            # Thumb
            thumb_tip = landmarks[4]
            thumb_ip = landmarks[3]
            index_mcp = landmarks[5]
            return euclidean_dist(thumb_tip, index_mcp) > euclidean_dist(thumb_ip, index_mcp) * 1.1

        tip_idx, pip_idx = finger_map[finger_idx]
        tip = landmarks[tip_idx]
        pip = landmarks[pip_idx]
        return euclidean_dist(tip, wrist) > euclidean_dist(pip, wrist) * 1.12

    def is_hand_closed(self, landmarks: List[Any], hand_size: float) -> bool:
        """Determines if the hand is curled into a closed fist.

        Condition: at most 1 finger extended and average fingertip distance to wrist is low.
        """
        wrist = landmarks[0]
        extended_count = sum(self.is_finger_extended(landmarks, i) for i in range(5))

        finger_tips = [landmarks[8], landmarks[12], landmarks[16], landmarks[20]]
        avg_tip_dist = sum(euclidean_dist(t, wrist) for t in finger_tips) / (4.0 * hand_size)

        return (extended_count <= 1) and (avg_tip_dist < 1.38)

    def calculate_palm_openness(self, landmarks: List[Any], hand_size: float) -> float:
        """Calculates normalized palm openness (0.0 to 1.0).

        When palm is shrunk / fingers drawn inward -> lower value.
        When palm is wide open with fingers extended -> 1.0 (full speed).
        """
        wrist = landmarks[0]
        finger_tips = [landmarks[4], landmarks[8], landmarks[12], landmarks[16], landmarks[20]]
        avg_tip_dist = sum(euclidean_dist(t, wrist) for t in finger_tips) / (5.0 * hand_size)

        # In a fully closed hand: ratio ~ 1.1 - 1.25
        # In a relaxed / shrunk palm: ratio ~ 1.35 - 1.6
        # In a wide open palm: ratio ~ 1.85 - 2.3
        min_spread = 1.25
        max_spread = 1.95

        openness = (avg_tip_dist - min_spread) / (max_spread - min_spread)
        return max(0.0, min(1.0, openness))

    def calculate_steering_angle(self, landmarks: List[Any], neutral_angle: float = 0.0) -> float:
        """Calculates hand roll angle in degrees relative to vertical (upright)."""
        wrist = landmarks[0]
        middle_mcp = landmarks[9]

        vx = middle_mcp.x - wrist.x
        vy = middle_mcp.y - wrist.y

        angle_rad = math.atan2(vx, -vy)
        return math.degrees(angle_rad) - neutral_angle

    def classify_gesture(self, landmarks: List[Any], hand_size: float) -> str:
        """Legacy helper for single-hand gestures."""
        if self.is_hand_closed(landmarks, hand_size):
            return "fist"

        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        if (euclidean_dist(thumb_tip, index_tip) / hand_size) < self.pinch_threshold:
            return "pinch"

        extended = sum(self.is_finger_extended(landmarks, i) for i in range(5))
        if extended >= 4:
            return "open_palm"

        return "neutral"
