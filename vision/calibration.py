"""
VelocityCV — Neutral Pose Calibration
Records baseline hand roll angle and scale during relaxed position.
"""

import time
from typing import List, Optional
import numpy as np


class Calibrator:
    def __init__(self, duration_seconds: float = 3.0):
        self.duration_seconds = duration_seconds
        self.is_calibrating = False
        self.start_time = 0.0
        self.angles: List[float] = []
        self.sizes: List[float] = []

        self.neutral_angle: float = 0.0
        self.neutral_size: float = 0.25
        self.calibrated: bool = False

    def start(self) -> None:
        self.is_calibrating = True
        self.start_time = time.monotonic()
        self.angles.clear()
        self.sizes.clear()

    def add_sample(self, raw_angle: float, hand_size: float) -> bool:
        """Adds a sample during calibration window. Returns True when calibration finishes."""
        if not self.is_calibrating:
            return False

        self.angles.append(raw_angle)
        self.sizes.append(hand_size)

        elapsed = time.monotonic() - self.start_time
        if elapsed >= self.duration_seconds and len(self.angles) >= 10:
            self.neutral_angle = float(np.median(self.angles))
            self.neutral_size = float(np.median(self.sizes))
            self.calibrated = True
            self.is_calibrating = False
            return True

        return False

    @property
    def progress(self) -> float:
        """Returns 0.0 to 1.0 progress through calibration."""
        if not self.is_calibrating:
            return 1.0 if self.calibrated else 0.0
        elapsed = time.monotonic() - self.start_time
        return min(1.0, elapsed / self.duration_seconds)
