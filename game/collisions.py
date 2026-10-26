"""
VelocityCV — Collision Detection & Near-Miss System
Calculates 3D proximity between the player and traffic cars.
"""

from typing import Tuple
from .car import PlayerCar
from .traffic import TrafficCar, TrafficManager


class CollisionSystem:
    def __init__(self, invulnerability_seconds: float = 1.5):
        self.invulnerability_seconds = invulnerability_seconds
        self.invulnerable_timer = 0.0

    def update(self, player: PlayerCar, traffic_mgr: TrafficManager, dt: float) -> Tuple[bool, bool]:
        """Checks for collision or near-miss.

        Returns:
            (collision_occurred, near_miss_occurred)
        """
        if self.invulnerable_timer > 0.0:
            self.invulnerable_timer = max(0.0, self.invulnerable_timer - dt)

        collision_hit = False
        near_miss_hit = False

        for traffic in traffic_mgr.cars:
            dz = traffic.z - player.z
            dx = abs(player.x - traffic.x)

            # Check overlap in depth (-50 < dz < 180)
            if -60.0 < dz < 190.0:
                if dx < 0.42:
                    # Direct Collision
                    if self.invulnerable_timer <= 0.0:
                        collision_hit = True
                        self.invulnerable_timer = self.invulnerability_seconds
                        # Apply impact physics
                        player.speed = max(30.0, player.speed * 0.35)
                        player.screen_shake = 22.0
                        break
                elif dx < 0.82 and not traffic.near_miss_awarded and player.speed > traffic.speed:
                    # Close Near-Miss Pass
                    traffic.near_miss_awarded = True
                    near_miss_hit = True
                    player.add_nitro_bonus(25.0)

        return collision_hit, near_miss_hit
