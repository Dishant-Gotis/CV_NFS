"""
VelocityCV — Classic 90s Arcade AI Traffic
Renders competing Formula arcade cars navigating highway lanes.
"""

import math
import random
from typing import Any, Dict, List, Optional, Tuple
import pygame
from .road import Track


class TrafficCar:
    def __init__(self, z: float, lane_x: float, speed: float, color: Tuple[int, int, int]):
        self.z = z
        self.x = lane_x
        self.speed = speed
        self.color = color
        self.has_been_passed = False
        self.near_miss_awarded = False


class TrafficManager:
    def __init__(self, track: Track, max_traffic: int = 12):
        self.track = track
        self.max_traffic = max_traffic
        self.cars: List[TrafficCar] = []
        self.traffic_colors = [
            (220, 20, 20),   # Ferrari Red
            (0, 110, 230),   # Williams Blue
            (240, 220, 20),  # Lotus Yellow
            (30, 180, 50),   # Green
            (255, 120, 0),   # McLaren Orange
        ]
        self._spawn_initial_traffic()

    def _spawn_initial_traffic(self) -> None:
        lanes = [-0.62, 0.0, 0.62]
        for i in range(self.max_traffic):
            dist = 1800.0 + i * 1100.0
            lane = random.choice(lanes)
            spd = random.uniform(85.0, 160.0)
            col = random.choice(self.traffic_colors)
            self.cars.append(TrafficCar(z=dist, lane_x=lane, speed=spd, color=col))

    def update(self, player_z: float, dt: float) -> None:
        lanes = [-0.62, 0.0, 0.62]
        for car in self.cars:
            car.z += car.speed * 12.0 * dt
            if self.track.total_length > 0:
                car.z = car.z % self.track.total_length

            dz = car.z - player_z
            if self.track.total_length > 0:
                if dz < -self.track.total_length / 2:
                    dz += self.track.total_length
                elif dz > self.track.total_length / 2:
                    dz -= self.track.total_length

            if dz < -600.0:
                car.z = (player_z + random.uniform(2800.0, 5000.0)) % self.track.total_length
                car.x = random.choice(lanes)
                car.speed = random.uniform(85.0, 165.0)
                car.color = random.choice(self.traffic_colors)
                car.near_miss_awarded = False
                car.has_been_passed = False

    def render_traffic_on_segment(
        self,
        surface: pygame.Surface,
        segment: Any,
        camera_depth: float,
        screen_w: int,
        screen_h: int,
    ) -> None:
        p1 = segment.p1
        if p1.scale <= 0.002:
            return

        seg_z_min = segment.p1.world_z
        seg_z_max = segment.p2.world_z

        for car in self.cars:
            if seg_z_min <= car.z < seg_z_max:
                car_screen_x = int(p1.screen_x + (car.x * p1.screen_w))
                car_screen_y = p1.screen_y

                scale = p1.scale * 1200.0
                cw = max(8, int(150 * scale))
                ch = max(4, int(58 * scale))

                # Wide Formula Rear Slicks
                tw = max(3, int(cw * 0.22))
                th = max(3, int(ch * 0.55))
                pygame.draw.rect(surface, (20, 20, 25), (car_screen_x - cw // 2, car_screen_y - th, tw, th))
                pygame.draw.rect(surface, (20, 20, 25), (car_screen_x + cw // 2 - tw, car_screen_y - th, tw, th))

                # Main Colorful Formula Body
                bw = int(cw * 0.65)
                bh = int(ch * 0.45)
                pygame.draw.rect(surface, car.color, (car_screen_x - bw // 2, car_screen_y - bh - 4, bw, bh), border_radius=2)

                # Rear Wing
                ww = int(cw * 0.85)
                wh = max(2, int(ch * 0.2))
                pygame.draw.rect(surface, (240, 240, 30), (car_screen_x - ww // 2, car_screen_y - ch, ww, wh))

                # Yellow Driver Helmet
                hr = max(2, int(6 * scale))
                pygame.draw.circle(surface, (255, 220, 20), (car_screen_x, car_screen_y - bh - 6), hr)
