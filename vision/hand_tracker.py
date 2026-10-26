"""
VelocityCV — MediaPipe Dual-Hand Tracker
Tracks both player hands in real time for dual-hand steering, braking, and speed modulation.
"""

from typing import Any, Dict, List, Optional, Tuple
import cv2
import mediapipe as mp
import numpy as np


class DetectedHand:
    def __init__(self, landmarks: List[Any], handedness: str, confidence: float):
        self.landmarks = landmarks
        self.handedness = handedness  # 'Left' or 'Right'
        self.confidence = confidence
        # Average X coordinate of hand on mirrored screen (0.0 = left edge, 1.0 = right edge)
        self.center_x = float(np.mean([lm.x for lm in landmarks]))
        self.center_y = float(np.mean([lm.y for lm in landmarks]))


class HandTracker:
    """Wraps MediaPipe Hands to detect up to 2 hands simultaneously."""

    def __init__(self, config: Dict[str, Any]):
        track_cfg = config.get("tracking", {})
        self.max_hands = int(track_cfg.get("max_hands", 2))
        self.min_detection_confidence = float(track_cfg.get("min_detection_confidence", 0.6))
        self.min_tracking_confidence = float(track_cfg.get("min_tracking_confidence", 0.6))

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=self.max_hands,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence,
        )

    def process_frame(
        self, bgr_frame: np.ndarray
    ) -> List[DetectedHand]:
        """Processes a single BGR camera frame and returns all detected hands."""
        if bgr_frame is None or bgr_frame.size == 0:
            return []

        rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False

        results = self.hands.process(rgb_frame)

        if not results.multi_hand_landmarks:
            return []

        detected: List[DetectedHand] = []
        for i, hand_lms in enumerate(results.multi_hand_landmarks):
            confidence = 0.90
            handedness = "Hand"
            if results.multi_handedness and i < len(results.multi_handedness):
                cls = results.multi_handedness[i].classification[0]
                confidence = float(cls.score)
                handedness = str(cls.label)

            detected.append(DetectedHand(
                landmarks=list(hand_lms.landmark),
                handedness=handedness,
                confidence=confidence,
            ))

        # Sort hands horizontally across mirrored screen (smaller X = left hand, larger X = right hand)
        detected.sort(key=lambda h: h.center_x)
        return detected

    def close(self) -> None:
        """Releases MediaPipe resources."""
        if hasattr(self, "hands") and self.hands:
            self.hands.close()
            self.hands = None
