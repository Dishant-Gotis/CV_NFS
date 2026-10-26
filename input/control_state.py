"""
VelocityCV — Control State Contract
Strict data interface between vision layer and game engine.
"""

from dataclasses import dataclass
import time


@dataclass
class ControlState:
    """Represents the real-time normalized driving controls.

    Attributes:
        steering: -1.0 (full left) to +1.0 (full right)
        throttle: 0.0 (idle) to 1.0 (full throttle)
        brake: 0.0 (released) to 1.0 (full brake)
        nitro: True while nitro boost is triggered
        hand_detected: False when hand tracking is lost
        confidence: 0.0 to 1.0 tracking confidence score
        timestamp: monotonic time of source frame capture
    """
    steering: float = 0.0
    throttle: float = 0.0
    brake: float = 0.0
    nitro: bool = False
    hand_detected: bool = False
    confidence: float = 0.0
    timestamp: float = 0.0

    @classmethod
    def default(cls) -> "ControlState":
        return cls(timestamp=time.monotonic())
