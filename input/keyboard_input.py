"""
VelocityCV — Keyboard Fallback Input Provider
Allows playing and testing without camera tracking.
"""

import time
import pygame
from .control_state import ControlState


class KeyboardInputProvider:
    """Translates Pygame keyboard state into a smooth ControlState."""

    def __init__(self, steer_speed: float = 3.5, return_speed: float = 4.5):
        self.steer_speed = steer_speed
        self.return_speed = return_speed
        self.current_steering: float = 0.0
        self.current_throttle: float = 0.0
        self.current_brake: float = 0.0
        self._last_time = time.monotonic()

    def update(self) -> ControlState:
        """Polls current keyboard keys and returns an updated ControlState."""
        now = time.monotonic()
        dt = max(0.001, min(0.1, now - self._last_time))
        self._last_time = now

        keys = pygame.key.get_pressed()

        # Steering
        target_steer = 0.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            target_steer -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            target_steer += 1.0

        if target_steer != 0.0:
            if target_steer > self.current_steering:
                self.current_steering = min(target_steer, self.current_steering + self.steer_speed * dt)
            else:
                self.current_steering = max(target_steer, self.current_steering - self.steer_speed * dt)
        else:
            # Return to center
            if self.current_steering > 0.0:
                self.current_steering = max(0.0, self.current_steering - self.return_speed * dt)
            elif self.current_steering < 0.0:
                self.current_steering = min(0.0, self.current_steering + self.return_speed * dt)

        # Throttle
        is_accel = keys[pygame.K_w] or keys[pygame.K_UP]
        if is_accel:
            self.current_throttle = min(1.0, self.current_throttle + 3.0 * dt)
        else:
            self.current_throttle = max(0.0, self.current_throttle - 4.0 * dt)

        # Brake
        is_brake = keys[pygame.K_s] or keys[pygame.K_DOWN]
        if is_brake:
            self.current_brake = min(1.0, self.current_brake + 5.0 * dt)
        else:
            self.current_brake = max(0.0, self.current_brake - 6.0 * dt)

        # Nitro
        nitro = bool(keys[pygame.K_SPACE])

        return ControlState(
            steering=float(self.current_steering),
            throttle=float(self.current_throttle),
            brake=float(self.current_brake),
            nitro=nitro,
            hand_detected=True,
            confidence=1.0,
            timestamp=now
        )
