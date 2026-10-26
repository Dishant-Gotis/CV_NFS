"""
VelocityCV — Dual-Hand Control Mapper
Implements the exact dual-hand driving logic:
- Left hand closed -> Steer left
- Right hand closed -> Steer right
- Both hands closed -> Brake
- Palm openness (shrink) -> Speed / Throttle control
"""

import math
import time
from typing import Any, Dict, List, Optional
import numpy as np
from input.control_state import ControlState
from .calibration import Calibrator
from .filters import LowPassFilter, OneEuroFilter
from .gestures import GestureClassifier
from .hand_tracker import DetectedHand


class ControlMapper:
    def __init__(self, config: Dict[str, Any]):
        controls_cfg = config.get("controls", {})
        dual_cfg = controls_cfg.get("dual_hand", {})
        hand_lost_cfg = controls_cfg.get("hand_lost", {})

        self.steer_speed = float(dual_cfg.get("steer_speed", 4.5))
        self.return_speed = float(dual_cfg.get("return_speed", 6.0))

        # Filters for silky-smooth control signals
        self.steer_filter = OneEuroFilter(min_cutoff=1.2, beta=0.08)
        self.throttle_filter = LowPassFilter(alpha=0.35)
        self.brake_filter = LowPassFilter(alpha=0.45)

        self.classifier = GestureClassifier()
        self.calibrator = Calibrator()

        self.grace_ms = float(hand_lost_cfg.get("grace_ms", 300.0))
        self.last_seen_time = time.monotonic()

        # Dynamic state
        self.current_steer = 0.0
        self.current_throttle = 0.0
        self.current_brake = 0.0

        # Readout state for UI
        self.left_hand_closed = False
        self.right_hand_closed = False
        self.left_openness = 0.0
        self.right_openness = 0.0

    def process_hands(
        self,
        hands: List[DetectedHand],
        timestamp: Optional[float] = None,
    ) -> ControlState:
        now = timestamp if timestamp is not None else time.monotonic()

        # 1. Hand Lost Handling
        if not hands:
            time_lost = (now - self.last_seen_time) * 1000.0
            if time_lost < self.grace_ms:
                return ControlState(
                    steering=float(self.current_steer),
                    throttle=float(self.current_throttle),
                    brake=float(self.current_brake),
                    nitro=False,
                    hand_detected=True,
                    confidence=0.5,
                    timestamp=now,
                )
            else:
                self.current_steer *= 0.85
                self.current_throttle *= 0.85
                self.current_brake = 0.0
                self.left_hand_closed = False
                self.right_hand_closed = False
                return ControlState(
                    steering=float(self.current_steer),
                    throttle=float(self.current_throttle),
                    brake=0.0,
                    nitro=False,
                    hand_detected=False,
                    confidence=0.0,
                    timestamp=now,
                )

        self.last_seen_time = now

        # Calibration step
        if self.calibrator.is_calibrating:
            avg_size = float(np.mean([self.classifier.calculate_hand_size(h.landmarks) for h in hands]))
            self.calibrator.add_sample(0.0, avg_size)

        # Identify Left and Right hands by X position on mirrored screen
        target_steer = 0.0
        target_throttle = 0.0
        target_brake = 0.0

        if len(hands) >= 2:
            # hands are pre-sorted by center_x: hands[0] = Left Hand, hands[1] = Right Hand
            h_left = hands[0]
            h_right = hands[1]

            size_left = self.classifier.calculate_hand_size(h_left.landmarks)
            size_right = self.classifier.calculate_hand_size(h_right.landmarks)

            self.left_hand_closed = self.classifier.is_hand_closed(h_left.landmarks, size_left)
            self.right_hand_closed = self.classifier.is_hand_closed(h_right.landmarks, size_right)

            self.left_openness = self.classifier.calculate_palm_openness(h_left.landmarks, size_left)
            self.right_openness = self.classifier.calculate_palm_openness(h_right.landmarks, size_right)

            # Case A: Both hands closed -> BRAKE
            if self.left_hand_closed and self.right_hand_closed:
                target_brake = 1.0
                target_throttle = 0.0
                target_steer = 0.0

            # Case B: Left closed, Right open -> STEER LEFT
            elif self.left_hand_closed and not self.right_hand_closed:
                target_steer = -1.0
                target_brake = 0.0
                # Right palm openness modulates speed
                target_throttle = self.right_openness

            # Case C: Right closed, Left open -> STEER RIGHT
            elif self.right_hand_closed and not self.left_hand_closed:
                target_steer = 1.0
                target_brake = 0.0
                # Left palm openness modulates speed
                target_throttle = self.left_openness

            # Case D: Both hands open -> DRIVE STRAIGHT
            else:
                target_steer = 0.0
                target_brake = 0.0
                # Average openness of both palms controls speed
                target_throttle = (self.left_openness + self.right_openness) / 2.0

        else:
            # Single hand visible fallback
            h = hands[0]
            size = self.classifier.calculate_hand_size(h.landmarks)
            is_closed = self.classifier.is_hand_closed(h.landmarks, size)
            openness = self.classifier.calculate_palm_openness(h.landmarks, size)

            if h.center_x < 0.42:
                # Left side
                self.left_hand_closed = is_closed
                self.right_hand_closed = False
                self.left_openness = openness
                if is_closed:
                    target_steer = -1.0
                    target_throttle = 0.45
                else:
                    target_steer = 0.0
                    target_throttle = openness
            elif h.center_x > 0.58:
                # Right side
                self.right_hand_closed = is_closed
                self.left_hand_closed = False
                self.right_openness = openness
                if is_closed:
                    target_steer = 1.0
                    target_throttle = 0.45
                else:
                    target_steer = 0.0
                    target_throttle = openness
            else:
                # Center
                if is_closed:
                    target_brake = 1.0
                    target_throttle = 0.0
                else:
                    target_throttle = openness

        # Smooth steering with 1€ filter
        dt = 0.033
        if target_steer != 0.0:
            if target_steer > self.current_steer:
                self.current_steer = min(target_steer, self.current_steer + self.steer_speed * dt)
            else:
                self.current_steer = max(target_steer, self.current_steer - self.steer_speed * dt)
        else:
            if self.current_steer > 0.0:
                self.current_steer = max(0.0, self.current_steer - self.return_speed * dt)
            elif self.current_steer < 0.0:
                self.current_steer = min(0.0, self.current_steer + self.return_speed * dt)

        # Smooth throttle and brake
        self.current_throttle = self.throttle_filter.filter(target_throttle)
        self.current_brake = self.brake_filter.filter(target_brake)

        # Nitro check: if palm is opened to maximum spread (> 0.9)
        nitro_active = (target_throttle > 0.88 and not self.left_hand_closed and not self.right_hand_closed)

        avg_conf = float(np.mean([h.confidence for h in hands]))

        return ControlState(
            steering=float(self.current_steer),
            throttle=float(self.current_throttle),
            brake=float(self.current_brake),
            nitro=nitro_active,
            hand_detected=True,
            confidence=avg_conf,
            timestamp=now,
        )

    # Legacy compatibility method for tests
    def process(self, landmarks: Optional[List[Any]], confidence: float = 0.0, timestamp: Optional[float] = None) -> ControlState:
        if landmarks is None:
            return self.process_hands([], timestamp)
        h = DetectedHand(landmarks=landmarks, handedness="Right", confidence=confidence)
        return self.process_hands([h], timestamp)
