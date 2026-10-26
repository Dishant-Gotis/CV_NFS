"""
VelocityCV — Player Car Arcade Physics
Handles throttle, braking, centrifugal curve drift, nitro boost, and off-road penalty.
"""

import math
from typing import Any, Dict


class PlayerCar:
    def __init__(self, config: Dict[str, Any]):
        game_cfg = config.get("game", {})
        self.base_max_speed: float = float(game_cfg.get("max_speed", 320.0))
        self.base_accel: float = float(game_cfg.get("acceleration", 140.0))
        self.base_brake: float = float(game_cfg.get("braking", 260.0))
        self.decel: float = float(game_cfg.get("deceleration", 45.0))
        self.offroad_decel: float = float(game_cfg.get("offroad_deceleration", 180.0))
        self.centrifugal_factor: float = float(game_cfg.get("centrifugal_force", 0.35))

        nitro_cfg = game_cfg.get("nitro", {})
        self.nitro_capacity: float = float(nitro_cfg.get("capacity", 100.0))
        self.nitro_meter: float = self.nitro_capacity
        self.nitro_drain_rate: float = float(nitro_cfg.get("drain_rate", 35.0))
        self.nitro_regen_rate: float = float(nitro_cfg.get("regen_rate", 8.0))
        self.nitro_speed_boost: float = float(nitro_cfg.get("speed_boost_factor", 1.35))
        self.nitro_accel_boost: float = float(nitro_cfg.get("acceleration_boost_factor", 1.8))

        # Dynamic State
        self.x: float = 0.0              # -1.0 (left edge) to 1.0 (right edge). Beyond = offroad
        self.z: float = 0.0              # World Z position along track
        self.speed: float = 0.0          # Current speed in km/h scale
        self.max_speed: float = self.base_max_speed
        self.accel: float = self.base_accel

        self.steering: float = 0.0       # Current smoothed steering input (-1.0 to 1.0)
        self.is_nitro_active: bool = False
        self.is_offroad: bool = False
        self.is_braking: bool = False
        self.screen_shake: float = 0.0

    @property
    def speed_ratio(self) -> float:
        """Returns normalized speed between 0.0 and 1.0."""
        return min(1.0, max(0.0, self.speed / (self.base_max_speed * self.nitro_speed_boost)))

    def update(
        self,
        steering_input: float,
        throttle_input: float,
        brake_input: float,
        nitro_requested: bool,
        current_curve: float,
        track_total_length: float,
        dt: float,
    ) -> None:
        """Advances physics by dt seconds."""
        self.steering = steering_input
        self.is_braking = brake_input > 0.1

        # Check offroad status
        self.is_offroad = abs(self.x) > 1.0

        # Handle Nitro Boost
        if nitro_requested and self.nitro_meter > 0 and throttle_input > 0.2:
            self.is_nitro_active = True
            self.nitro_meter = max(0.0, self.nitro_meter - self.nitro_drain_rate * dt)
            self.max_speed = self.base_max_speed * self.nitro_speed_boost
            self.accel = self.base_accel * self.nitro_accel_boost
        else:
            self.is_nitro_active = False
            self.max_speed = self.base_max_speed
            self.accel = self.base_accel
            if self.nitro_meter < self.nitro_capacity:
                self.nitro_meter = min(self.nitro_capacity, self.nitro_meter + self.nitro_regen_rate * dt)

        # Acceleration and Braking
        if throttle_input > 0.0:
            self.speed += self.accel * throttle_input * dt
        else:
            # Natural deceleration / coasting
            self.speed = max(0.0, self.speed - self.decel * dt)

        if brake_input > 0.0:
            self.speed = max(0.0, self.speed - self.base_brake * brake_input * dt)

        # Off-road speed clamp and deceleration
        if self.is_offroad:
            max_offroad_speed = self.base_max_speed * 0.35
            if self.speed > max_offroad_speed:
                self.speed = max(max_offroad_speed, self.speed - self.offroad_decel * dt)
            self.screen_shake = min(6.0, self.screen_shake + 12.0 * dt)
        else:
            self.screen_shake = max(0.0, self.screen_shake - 15.0 * dt)

        # Clamp speed
        self.speed = max(0.0, min(self.max_speed, self.speed))

        # Advance track position
        # Speed in km/h translated to world units (scaled for arcade feel)
        world_speed = self.speed * 12.0
        self.z += world_speed * dt
        if track_total_length > 0:
            self.z = self.z % track_total_length

        # Lateral steering movement (scaled by current speed)
        speed_factor = self.speed / self.base_max_speed
        self.x += self.steering * speed_factor * 2.2 * dt

        # Centrifugal force pushing outward on curves
        if current_curve != 0.0 and self.speed > 5.0:
            centrifugal_drift = current_curve * (speed_factor ** 1.8) * self.centrifugal_factor * dt
            self.x -= centrifugal_drift

        # Clamp lateral position to avoid flying into infinity
        self.x = max(-2.4, min(2.4, self.x))

    def add_nitro_bonus(self, amount: float = 25.0) -> None:
        """Awards nitro meter for near misses or stunts."""
        self.nitro_meter = min(self.nitro_capacity, self.nitro_meter + amount)
