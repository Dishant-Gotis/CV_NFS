"""
VelocityCV — Vision Filters and Signal Processing
Implements One-Euro filter, exponential moving average, deadzones, hysteresis, and debounce.
"""

import math
import time
from typing import Any, Optional


class LowPassFilter:
    """Standard first-order low-pass filter."""

    def __init__(self, alpha: float = 0.5):
        self.alpha = alpha
        self.s: Optional[float] = None

    def filter(self, value: float, alpha: Optional[float] = None) -> float:
        if alpha is not None:
            self.alpha = alpha
        if self.s is None:
            self.s = value
        else:
            self.s = self.alpha * value + (1.0 - self.alpha) * self.s
        return self.s

    def reset(self) -> None:
        self.s = None


class OneEuroFilter:
    """Adaptive low-pass filter (1€ Filter).

    Removes high-frequency jitter at rest while preserving quick response during rapid movements.
    Reference: Casiez et al., CHI 2012.
    """

    def __init__(
        self,
        min_cutoff: float = 1.0,
        beta: float = 0.05,
        d_cutoff: float = 1.0,
    ):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_filt = LowPassFilter()
        self.dx_filt = LowPassFilter()
        self.last_time: Optional[float] = None

    def _alpha(self, cutoff: float, dt: float) -> float:
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def filter(self, x: float, timestamp: Optional[float] = None) -> float:
        if timestamp is None:
            timestamp = time.monotonic()

        if self.last_time is None:
            self.last_time = timestamp
            return self.x_filt.filter(x, 1.0)

        dt = max(1e-4, timestamp - self.last_time)
        self.last_time = timestamp

        # Estimate derivative
        prev_x = self.x_filt.s if self.x_filt.s is not None else x
        dx = (x - prev_x) / dt
        edx = self.dx_filt.filter(dx, self._alpha(self.d_cutoff, dt))

        # Dynamic cutoff frequency
        cutoff = self.min_cutoff + self.beta * abs(edx)
        return self.x_filt.filter(x, self._alpha(cutoff, dt))

    def reset(self) -> None:
        self.x_filt.reset()
        self.dx_filt.reset()
        self.last_time = None


def apply_deadzone_and_curve(
    angle: float,
    deadzone_deg: float = 8.0,
    max_angle_deg: float = 45.0,
    exponent: float = 1.3,
) -> float:
    """Maps raw tilt angle (in degrees) to normalized steering [-1.0, 1.0]."""
    abs_angle = abs(angle)
    if abs_angle < deadzone_deg:
        return 0.0

    # Scale between deadzone and max_angle
    span = max(1.0, max_angle_deg - deadzone_deg)
    normalized = min(1.0, (abs_angle - deadzone_deg) / span)

    # Response curve for finer center control
    curved = normalized ** exponent

    return math.copysign(curved, angle)


class HysteresisThreshold:
    """Maintains state with different enter and exit thresholds to avoid boundary flicker."""

    def __init__(self, enter_threshold: float, exit_threshold: float, start_active: bool = False):
        self.enter_threshold = enter_threshold
        self.exit_threshold = exit_threshold
        self.active = start_active

    def update(self, value: float) -> bool:
        if self.active:
            if value > self.exit_threshold:
                self.active = False
        else:
            if value < self.enter_threshold:
                self.active = True
        return self.active


class Debouncer:
    """Requires a signal to be held consecutively for N frames before changing output state."""

    def __init__(self, required_frames: int = 3, initial_state: Any = None):
        self.required_frames = required_frames
        self.current_state = initial_state
        self.pending_state = initial_state
        self.counter = 0

    def update(self, new_state: Any) -> Any:
        if new_state == self.current_state:
            self.counter = 0
            self.pending_state = new_state
            return self.current_state

        if new_state == self.pending_state:
            self.counter += 1
            if self.counter >= self.required_frames:
                self.current_state = new_state
                self.counter = 0
        else:
            self.pending_state = new_state
            self.counter = 1

        return self.current_state
