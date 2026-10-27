"""
VelocityCV — Collision Detection & Drafting System
Calculates 3D proximity between player and competitors, handling direct impacts,
near-miss overtakes, and high-speed slipstream drafting.
"""

from typing import Tuple
from .car import PlayerCar
from .traffic import TrafficCar, TrafficManager


class CollisionSystem:
    def __init__(self, invulnerability_seconds: float = 1.2):
        self.invulnerability_seconds = invulnerability_seconds
        self.invulnerable_timer = 0.0
        self.is_drafting = False

    def update(self, player: PlayerCar, traffic_mgr: TrafficManager, dt: float) -> Tuple[bool, bool]:
        """Checks for direct collision, near-miss overtakes, and drafting slipstream.

        Returns:
            (collision_occurred, near_miss_occurred)
        """
        if self.invulnerable_timer > 0.0:
            self.invulnerable_timer = max(0.0, self.invulnerable_timer - dt)

        collision_hit = False
        near_miss_hit = False
        self.is_drafting = False

        for traffic in traffic_mgr.cars:
            dz = traffic.z - player.z
            dx = abs(player.x - traffic.x)

            # 1. Direct Vehicle Impact (Actual physical contact: -35 <= dz <= 65 and lateral overlap dx < 0.36)
            if -35.0 <= dz <= 65.0 and dx < 0.36:
                if self.invulnerable_timer <= 0.0:
                    collision_hit = True
                    self.invulnerable_timer = self.invulnerability_seconds

                    # Physical impact: smooth lateral bounce away from opponent (ZERO teleportation)
                    rebound_dir = -1.0 if player.x < traffic.x else 1.0

                    # Dampen rebound if player is already near the track shoulder to stay on track
                    if player.x < -0.70 and rebound_dir < 0:
                        rebound_dir = 0.4
                    elif player.x > 0.70 and rebound_dir > 0:
                        rebound_dir = -0.4

                    # Smooth lateral impulse on player
                    player.lateral_velocity = rebound_dir * 1.6
                    player.car_collision_sparks = True
                    player.car_collision_side = rebound_dir
                    player.collision_impact_timer = 0.35
                    player.roll_angle += -rebound_dir * 10.0

                    # Opponent car also reacts with physical recoil
                    traffic.lateral_velocity = -rebound_dir * 1.2
                    traffic.tilt = rebound_dir * 0.7
                    traffic.collision_timer = 0.35

                    # Momentum transfer: realistic deceleration instead of jarring sudden stop
                    speed_loss = min(player.speed * 0.18, 26.0)
                    player.speed = max(35.0, player.speed - speed_loss)
                    traffic.current_speed = min(traffic.max_speed * 1.12, traffic.current_speed + speed_loss * 0.6)
                    player.screen_shake = 0.0
                    break

            # 2. Clean near-miss overtake
            elif -20.0 <= dz <= 100.0 and dx < 0.82 and not traffic.near_miss_awarded and player.speed > traffic.current_speed:
                traffic.near_miss_awarded = True
                near_miss_hit = True
                player.add_nitro_bonus(25.0)

            # 3. Aerodynamic Slipstream / Drafting (directly behind opponent car)
            elif 50.0 < dz < 320.0 and dx < 0.25 and player.speed > 80.0:
                self.is_drafting = True
                player.speed = min(player.max_speed * 1.15, player.speed + 35.0 * dt)
                player.add_nitro_bonus(4.0 * dt)

        return collision_hit, near_miss_hit
