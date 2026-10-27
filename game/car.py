"""
VelocityCV — Player Car Arcade Physics
Handles throttle, braking, centrifugal curve drift, nitro boost, and road border collision.
Border collision = GAME OVER (crash).
"""

import math
from typing import Any, Dict


class PlayerCar:
    def __init__(self, config: Dict[str, Any]):
        game_cfg = config.get("game", {})
        self.base_max_speed: float = float(game_cfg.get("max_speed", 280.0))
        self.base_accel: float = float(game_cfg.get("acceleration", 150.0))
        self.base_brake: float = float(game_cfg.get("braking", 280.0))
        self.decel: float = float(game_cfg.get("deceleration", 50.0))
        self.offroad_decel: float = float(game_cfg.get("offroad_deceleration", 190.0))
        self.centrifugal_factor: float = float(game_cfg.get("centrifugal_force", 0.30))

        nitro_cfg = game_cfg.get("nitro", {})
        self.nitro_capacity: float = float(nitro_cfg.get("capacity", 100.0))
        self.nitro_meter: float = self.nitro_capacity
        self.nitro_drain_rate: float = float(nitro_cfg.get("drain_rate", 35.0))
        self.nitro_regen_rate: float = float(nitro_cfg.get("regen_rate", 10.0))
        self.nitro_speed_boost: float = float(nitro_cfg.get("speed_boost_factor", 1.30))
        self.nitro_accel_boost: float = float(nitro_cfg.get("acceleration_boost_factor", 1.6))

        # Dynamic State
        self.x: float = 0.0              # -1.0 (left edge) to 1.0 (right edge)
        self.z: float = 0.0              # World Z position along track
        self.speed: float = 0.0          # Current speed in mph scale
        self.max_speed: float = self.base_max_speed
        self.accel: float = self.base_accel

        self.steering: float = 0.0
        self.is_nitro_active: bool = False
        self.is_offroad: bool = False
        self.is_braking: bool = False
        self.screen_shake: float = 0.0

        # Road border collision
        self.border_limit: float = 1.12
        self.is_border_collision: bool = False
        self.border_collision_side: int = 0
        self.border_sparks: bool = False

        # Vehicle collision dynamics (smooth impulse physics, zero teleportation)
        self.lateral_velocity: float = 0.0
        self.car_collision_sparks: bool = False
        self.car_collision_side: float = 0.0
        self.collision_impact_timer: float = 0.0

        # Game Over state
        self.game_over: bool = False
        self.crash_timer: float = 0.0

        # Chassis animation
        self.roll_angle: float = 0.0
        self.pitch_offset: float = 0.0

        # Race timing & progress
        self.race_time: float = 0.0
        self.lap: int = 0
        self.total_distance: float = 0.0

    @property
    def speed_ratio(self) -> float:
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
        # If game over, just decay shake and do nothing else
        if self.game_over:
            self.crash_timer += dt
            self.screen_shake = max(0.0, self.screen_shake - 8.0 * dt)
            self.speed = max(0.0, self.speed - 200.0 * dt)
            return

        self.steering = steering_input
        self.is_braking = brake_input > 0.1
        self.is_border_collision = False
        self.border_sparks = False

        self.is_offroad = abs(self.x) > 1.0

        # Nitro Boost
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
            self.speed = max(0.0, self.speed - self.decel * dt)

        if brake_input > 0.0:
            self.speed = max(0.0, self.speed - self.base_brake * brake_input * dt)

        # Off-road drag
        if self.is_offroad and abs(self.x) <= self.border_limit:
            max_offroad_speed = self.base_max_speed * 0.50
            if self.speed > max_offroad_speed:
                self.speed = max(max_offroad_speed, self.speed - self.offroad_decel * dt)

        # No screen shake (rock-solid camera)
        self.screen_shake = 0.0

        # Clamp speed
        self.speed = max(0.0, min(self.max_speed, self.speed))

        # Advance track position and lap count
        self.z += self.speed * 12.0 * dt
        if track_total_length > 0:
            if self.z >= track_total_length:
                self.lap += 1
                self.z %= track_total_length
            elif self.z < 0:
                self.z += track_total_length

        self.total_distance = self.lap * track_total_length + self.z

        # Lateral steering
        speed_factor = self.speed / self.base_max_speed
        self.x += self.steering * speed_factor * 2.3 * dt

        # Smooth lateral momentum from vehicle impacts (physics impulse, zero teleportation)
        if abs(self.lateral_velocity) > 0.001:
            self.x += self.lateral_velocity * dt
            self.lateral_velocity *= math.exp(-7.0 * dt)
        else:
            self.lateral_velocity = 0.0

        # Collision impact timer decay
        if self.collision_impact_timer > 0.0:
            self.collision_impact_timer = max(0.0, self.collision_impact_timer - dt)
            if self.collision_impact_timer <= 0.0:
                self.car_collision_sparks = False
            # Car-to-car collisions keep the player in the race, never bumping into game-over
            self.x = max(-0.95, min(0.95, self.x))

        # Centrifugal force
        if current_curve != 0.0 and self.speed > 5.0:
            centrifugal_drift = current_curve * (speed_factor ** 1.8) * self.centrifugal_factor * dt
            self.x -= centrifugal_drift

        # ── BORDER COLLISION = GAME OVER (Only when manually driving off the track) ──
        if abs(self.x) >= self.border_limit and self.collision_impact_timer <= 0.0:
            self.is_border_collision = True
            self.border_sparks = True
            self.border_collision_side = -1 if self.x < 0 else 1

            # CRASH - Game Over
            self.game_over = True
            self.crash_timer = 0.0
            self.screen_shake = 0.0

            # Clamp at border
            self.x = math.copysign(self.border_limit, self.x)
            return

        # Hard clamp
        self.x = max(-1.20, min(1.20, self.x))

        # Chassis Dynamics
        target_roll = self.steering * 8.0
        self.roll_angle += (target_roll - self.roll_angle) * 12.0 * dt

        target_pitch = -4.0 if self.is_braking else (3.0 if throttle_input > 0.5 else 0.0)
        self.pitch_offset += (target_pitch - self.pitch_offset) * 10.0 * dt

    def add_nitro_bonus(self, amount: float = 25.0) -> None:
        self.nitro_meter = min(self.nitro_capacity, self.nitro_meter + amount)
