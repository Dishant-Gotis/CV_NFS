"""
VelocityCV — 4-Car Grand Prix Competitors & Leaderboard
Manages the 3 AI competitor cars (Scuderia #2, Lotus #3, Benetton #4)
competing alongside the Player (#1) on a persistent starting grid and circuit.
"""

import math
import random
from typing import Any, Dict, List, Optional, Tuple
from .road import Track


class OpponentCar:
    def __init__(
        self,
        z: float,
        lane_x: float,
        base_speed: float = 195.0,
        color: Tuple[int, int, int] = (220, 20, 20),
        number: int = 2,
        name: str = "COMPETITOR",
        speed: Optional[float] = None,
    ):
        self.z = z
        self.x = lane_x
        self.target_x = lane_x
        self.base_speed = speed if speed is not None else base_speed
        self.current_speed = 0.0  # Starts stationary on grid, accelerates on green
        self.max_speed = self.base_speed
        self.color = color
        self.number = number
        self.name = name

        # Race progress
        self.lap = 0
        self.total_distance = z

        # AI Behavior timers
        self.lane_timer = random.uniform(3.0, 7.0)
        self.draft_boost = 0.0
        self.near_miss_awarded = False
        self.tilt = 0.0
        self.lateral_velocity = 0.0
        self.collision_timer = 0.0

    def update(
        self,
        player_z: float,
        track: Track,
        is_racing: bool,
        dt: float,
        other_opponents: Optional[List["OpponentCar"]] = None,
    ) -> None:
        """Updates competitive AI racing, acceleration, cornering, and lane choices."""
        if not is_racing:
            self.tilt = 0.0
            return

        track_length = track.total_length

        # 1. Acceleration from starting grid
        accel_rate = 85.0
        if self.current_speed < self.max_speed:
            self.current_speed = min(self.max_speed, self.current_speed + accel_rate * dt)

        # 2. Cornering speed adjustment
        cur_seg = track.find_segment(self.z)
        if abs(cur_seg.curve) > 1.2:
            # Brake slightly for realistic corner entry
            target_corner_speed = self.base_speed * (0.80 if abs(cur_seg.curve) > 2.0 else 0.88)
            if self.current_speed > target_corner_speed:
                self.current_speed = max(target_corner_speed, self.current_speed - 120.0 * dt)
        else:
            # Accelerate on straights
            if self.current_speed < self.base_speed:
                self.current_speed = min(self.base_speed, self.current_speed + accel_rate * dt)

        # 3. Dynamic pack racing (keeps all 4 cars in an exciting battle)
        dz_to_player = self.z - player_z
        if track_length > 0:
            if dz_to_player < -track_length / 2:
                dz_to_player += track_length
            elif dz_to_player > track_length / 2:
                dz_to_player -= track_length

        if dz_to_player > 1400.0:
            # Far ahead: cruise slightly so player can contest the lead
            self.max_speed = self.base_speed * 0.90
        elif dz_to_player < -800.0:
            # Far behind: push with drafting pace to catch back up
            self.max_speed = self.base_speed * 1.15
            self.current_speed = min(self.max_speed, self.current_speed + 70.0 * dt)
        else:
            self.max_speed = self.base_speed

        # 4. Advance track position
        self.z += self.current_speed * 12.0 * dt
        if track_length > 0:
            if self.z >= track_length:
                self.lap += 1
                self.z %= track_length
            elif self.z < 0:
                self.z += track_length

        self.total_distance = self.lap * track_length + self.z

        # 5. Lane steering & overtakes
        self.lane_timer -= dt
        if self.lane_timer <= 0.0:
            self.lane_timer = random.uniform(3.5, 7.5)
            lanes = [-0.45, 0.0, 0.45]
            # Avoid picking the same lane
            available = [l for l in lanes if abs(l - self.target_x) > 0.15]
            if available:
                self.target_x = random.choice(available)

        # Smooth steering towards target lane
        lane_diff = self.target_x - self.x
        self.x += lane_diff * min(1.0, 2.5 * dt)

        # Smooth impact momentum from vehicle collisions
        if abs(self.lateral_velocity) > 0.001:
            self.x += self.lateral_velocity * dt
            self.x = max(-0.85, min(0.85, self.x))
            self.lateral_velocity *= math.exp(-7.0 * dt)
        else:
            self.lateral_velocity = 0.0

        if self.collision_timer > 0.0:
            self.collision_timer = max(0.0, self.collision_timer - dt)
        else:
            self.tilt = max(-1.0, min(1.0, lane_diff * 4.0))


# Compatibility alias
TrafficCar = OpponentCar


class TrafficManager:
    """Manages the 3 AI competitor cars and real-time Grand Prix Leaderboard."""

    def __init__(self, track: Track, max_traffic: int = 3):
        self.track = track
        self.cars: List[OpponentCar] = []
        self.reset_starting_grid()

    def reset_starting_grid(self) -> None:
        """Positions the 3 AI competitors on the starting grid directly in front of the Player (#1)."""
        self.cars.clear()

        # Grid layout (Player is at z=0.0, lane=0.35 in 4th):
        # 1st Pole: Scuderia #2 at z=160 (lane -0.35)
        # 2nd:      Lotus #3    at z=110 (lane 0.35)
        # 3rd:      Benetton #4 at z=55  (lane -0.35)
        competitors = [
            OpponentCar(
                z=160.0,
                lane_x=-0.35,
                base_speed=212.0,
                color=(235, 30, 30),
                number=2,
                name="SCUDERIA",
            ),
            OpponentCar(
                z=110.0,
                lane_x=0.35,
                base_speed=202.0,
                color=(250, 215, 20),
                number=3,
                name="LOTUS",
            ),
            OpponentCar(
                z=55.0,
                lane_x=-0.35,
                base_speed=192.0,
                color=(20, 185, 60),
                number=4,
                name="BENETTON",
            ),
        ]
        self.cars.extend(competitors)

    def update(self, player_z: float, dt: float, is_racing: bool = True) -> None:
        """Updates all 3 AI cars."""
        for car in self.cars:
            car.update(player_z, self.track, is_racing, dt, other_opponents=self.cars)

    def get_leaderboard(self, player_car: Any) -> List[Dict[str, Any]]:
        """Calculates real-time race standings for all 4 cars (Player + 3 AI).

        Returns:
            List of 4 entries sorted 1st to 4th by total track progress.
        """
        all_cars = []

        # 1. Add Player
        player_dist = getattr(player_car, "total_distance", player_car.z)
        all_cars.append({
            "number": 1,
            "name": "PLAYER",
            "color": (0, 115, 235),
            "is_player": True,
            "speed": player_car.speed,
            "total_distance": player_dist,
            "z": player_car.z,
            "lap": getattr(player_car, "lap", 0),
        })

        # 2. Add 3 AI Competitors
        for c in self.cars:
            all_cars.append({
                "number": c.number,
                "name": c.name,
                "color": c.color,
                "is_player": False,
                "speed": c.current_speed,
                "total_distance": c.total_distance,
                "z": c.z,
                "lap": c.lap,
            })

        # 3. Sort by total distance descending
        all_cars.sort(key=lambda x: x["total_distance"], reverse=True)

        # 4. Annotate positions and gaps
        leader_dist = all_cars[0]["total_distance"]
        for idx, entry in enumerate(all_cars):
            entry["position"] = idx + 1
            if idx == 0:
                entry["gap_str"] = "LEADER"
            else:
                gap_m = int(leader_dist - entry["total_distance"])
                entry["gap_str"] = f"-{gap_m}m"

        return all_cars
