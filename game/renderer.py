"""
VelocityCV — Classic 90s Arcade Renderer
Faithful recreation of classic 90s arcade racers (Pole Position / OutRun):
- Vivid blue sky with pixelated drifting clouds and green mountain horizon ridge
- High-contrast asphalt highway with alternating red/white striped rumble curbs
- Classic overhead START/FINISH truss gantry with checkered banner and traffic lights
- Authentic arcade formula racer and traffic vehicles
- Clean retro arcade HUD: TOP, SCORE, TIME, LAP, SPEED matching the reference visual
"""

import math
import random
from typing import Any, Dict, List, Optional, Tuple
import pygame
from .car import PlayerCar
from .road import RoadSegment, Track


class ArcadeRenderer:
    def __init__(self, screen: pygame.Surface, config: Dict[str, Any]):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.config = config

        self.draw_distance = 160
        self.camera_height = 800.0
        self.camera_depth = 0.84

        self.sky_offset = 0.0

        # Authentic 90s Arcade Colors
        self.c_sky_blue = (35, 120, 230)
        self.c_mountain_dark = (25, 75, 30)
        self.c_mountain_light = (38, 105, 42)
        self.c_white = (255, 255, 255)
        self.c_yellow = (255, 240, 0)
        self.c_cyan = (0, 240, 255)
        self.c_red = (230, 20, 20)

        # Clouds
        self.clouds = [
            {"x": random.randint(0, self.width), "y": random.randint(35, 140), "w": random.randint(80, 140), "h": random.randint(30, 50)}
            for _ in range(6)
        ]

        # Retro Arcade Fonts
        pygame.font.init()
        self.font_arcade_big = pygame.font.SysFont("impact", 32)
        self.font_arcade_mid = pygame.font.SysFont("impact", 22)
        self.font_arcade_small = pygame.font.SysFont("consolas", 14, bold=True)

        self.show_camera_panel = config.get("camera_panel", {}).get("enabled", True)

    def render(
        self,
        car: PlayerCar,
        track: Track,
        control_state: Any,
        dt: float,
        camera_frame_surf: Optional[pygame.Surface] = None,
        traffic_mgr: Optional[Any] = None,
    ) -> None:
        """Renders complete 90s arcade frame."""
        base_segment = track.find_segment(car.z)
        base_percent = (car.z % track.segment_length) / track.segment_length

        # 1. Sky, Mountains, and Drifting Clouds
        self._render_sky_and_mountains(base_segment.curve, car.speed_ratio, dt)

        # 2. Road Projection (Full painter's algorithm from far to near)
        self._render_road(car, track, base_segment, base_percent, traffic_mgr)

        # 3. Player Classic Arcade Formula Racer
        self._render_player_car(car)

        # 4. Clean 90s Arcade HUD (Matching Image 2)
        self._render_arcade_hud(car, control_state)

        # 5. Optical Sensor Inset Panel (Upright Mirrored Feed)
        if self.show_camera_panel:
            self._render_camera_inset(camera_frame_surf, control_state)

    def _render_sky_and_mountains(self, curve: float, speed_ratio: float, dt: float) -> None:
        horizon_y = int(self.height * 0.50)

        # Vivid Blue Sky
        self.screen.fill(self.c_sky_blue, (0, 0, self.width, horizon_y))

        # Parallax displacement
        self.sky_offset += curve * speed_ratio * 35.0 * dt

        # Drifting Fluffy Pixel Clouds
        for c in self.clouds:
            cx = int((c["x"] - self.sky_offset * 0.4) % (self.width + 160)) - 80
            cy = c["y"]
            cw = c["w"]
            ch = c["h"]
            # Pixelated blocky cloud clumps
            pygame.draw.ellipse(self.screen, self.c_white, (cx, cy, cw, ch))
            pygame.draw.ellipse(self.screen, self.c_white, (cx + 20, cy - 12, cw - 30, ch + 8))
            pygame.draw.ellipse(self.screen, self.c_white, (cx - 15, cy + 4, cw - 40, ch - 8))

        # Green Mountain Ridge Horizon
        pts_mountain = [(0, horizon_y)]
        step = 60
        for i in range(0, self.width + step * 2, step):
            shift_x = i - int(self.sky_offset) % step
            h_var = int(math.sin(i * 0.015 + self.sky_offset * 0.01) * 28 + 36)
            pts_mountain.append((shift_x, horizon_y - h_var))
        pts_mountain.append((self.width, horizon_y))
        pygame.draw.polygon(self.screen, self.c_mountain_dark, pts_mountain)

        # Foreground low pine tree line
        for tx in range(0, self.width + 40, 24):
            shifted_tx = (tx - int(self.sky_offset * 1.2)) % (self.width + 40) - 20
            pygame.draw.polygon(
                self.screen,
                self.c_mountain_light,
                [(shifted_tx, horizon_y), (shifted_tx + 12, horizon_y - 20), (shifted_tx + 24, horizon_y)],
            )

    def _render_road(
        self,
        car: PlayerCar,
        track: Track,
        base_segment: RoadSegment,
        base_percent: float,
        traffic_mgr: Optional[Any] = None,
    ) -> None:
        """Projects and draws road segments using clean back-to-front painter's algorithm."""
        total_segments = len(track.segments)
        camera_x = car.x * track.road_width
        camera_y = self.camera_height + base_segment.p1.world_y
        camera_z = car.z

        dx = -(base_segment.curve * base_percent)
        x = 0.0

        visible_segs = []

        # Project visible segments from near to far
        for n in range(self.draw_distance):
            seg_idx = (base_segment.index + n) % total_segments
            segment = track.segments[seg_idx]

            loop_offset = track.total_length if seg_idx < base_segment.index else 0.0

            segment.p1.project(
                camera_x - x,
                camera_y,
                camera_z - loop_offset,
                self.camera_depth,
                self.width,
                self.height,
                track.road_width,
            )

            # Linear curve accumulation (avoids O(N^2) curvature explosion)
            x += segment.curve * 0.55

            segment.p2.project(
                camera_x - x,
                camera_y,
                camera_z - loop_offset,
                self.camera_depth,
                self.width,
                self.height,
                track.road_width,
            )

            # Only collect segments in front of camera
            if segment.p1.scale > 0.0:
                visible_segs.append(segment)

        horizon_y = int(self.height * 0.50)

        # Draw in reverse order: from farthest down to nearest (front-most)
        for segment in reversed(visible_segs):
            p1 = segment.p1
            p2 = segment.p2

            # Clamp coordinates to horizon and screen bottom
            y1 = max(horizon_y, min(self.height, p1.screen_y))
            y2 = max(horizon_y, min(self.height, p2.screen_y))

            if y1 <= y2:
                continue

            # 1. Lush Green Grass Field
            pygame.draw.polygon(
                self.screen,
                segment.color_grass,
                [(0, y2), (self.width, y2), (self.width, y1), (0, y1)],
            )

            # 2. Red & White Striped Rumble Curbs
            rw1 = p1.screen_w * 1.16
            rw2 = p2.screen_w * 1.16
            pygame.draw.polygon(
                self.screen,
                segment.color_rumble,
                [
                    (p1.screen_x - rw1, y1),
                    (p1.screen_x + rw1, y1),
                    (p2.screen_x + rw2, y2),
                    (p2.screen_x - rw2, y2),
                ],
            )

            # 3. Clean Gray Asphalt Road Bed
            pygame.draw.polygon(
                self.screen,
                segment.color_road,
                [
                    (p1.screen_x - p1.screen_w, y1),
                    (p1.screen_x + p1.screen_w, y1),
                    (p2.screen_x + p2.screen_w, y2),
                    (p2.screen_x - p2.screen_w, y2),
                ],
            )

            # 4. Crisp White Dashed Center Lane Line
            if segment.color_lane == (255, 255, 255):
                lane_w1 = max(3, int(p1.screen_w * 0.024))
                lane_w2 = max(2, int(p2.screen_w * 0.024))
                pygame.draw.polygon(
                    self.screen,
                    self.c_white,
                    [
                        (p1.screen_x - lane_w1, y1),
                        (p1.screen_x + lane_w1, y1),
                        (p2.screen_x + lane_w2, y2),
                        (p2.screen_x - lane_w2, y2),
                    ],
                )

            # 5. AI Traffic Vehicles
            if traffic_mgr:
                traffic_mgr.render_traffic_on_segment(self.screen, segment, self.camera_depth, self.width, self.height)

            # 6. Roadside Scenery (Start Gantry, Trees, Billboards)
            if segment.scenery and p1.scale > 0.002:
                for item in segment.scenery:
                    self._render_scenery_object(item, p1, y1)

    def _render_scenery_object(self, item: Any, point: Any, base_y: int) -> None:
        """Renders classic 90s arcade overhead gantries and roadside props."""
        scale = point.scale * 1200.0 * item.scale_factor

        if item.sprite_type in ("start_gantry", "finish_gantry"):
            # Overhead START/FINISH truss gantry arch across the entire highway
            gantry_w = int(point.screen_w * 2.3)
            gantry_h = int(120 * scale)
            gx = point.screen_x - gantry_w // 2
            gy = base_y - gantry_h

            if gantry_w < 10 or gantry_h < 10:
                return

            # Blue metal lattice support towers on left and right
            tower_w = max(4, int(18 * scale))
            pygame.draw.rect(self.screen, (0, 110, 220), (gx, gy, tower_w, gantry_h))
            pygame.draw.rect(self.screen, (0, 110, 220), (gx + gantry_w - tower_w, gy, tower_w, gantry_h))

            # Cross truss lattice lines
            for step_y in range(gy, gy + gantry_h, max(6, int(20 * scale))):
                pygame.draw.line(self.screen, self.c_white, (gx, step_y), (gx + tower_w, step_y + 10), 1)
                pygame.draw.line(self.screen, self.c_white, (gx + gantry_w - tower_w, step_y), (gx + gantry_w, step_y + 10), 1)

            # Yellow Checkered "START" Banner
            banner_w = gantry_w - tower_w * 2
            banner_h = max(8, int(42 * scale))
            banner_x = gx + tower_w
            banner_y = gy + int(10 * scale)

            pygame.draw.rect(self.screen, self.c_yellow, (banner_x, banner_y, banner_w, banner_h))
            pygame.draw.rect(self.screen, (20, 20, 20), (banner_x, banner_y, banner_w, banner_h), 2)

            # Checkered end caps
            chk_w = max(4, int(28 * scale))
            self._draw_checkered_rect(banner_x, banner_y, chk_w, banner_h, int(7 * scale))
            self._draw_checkered_rect(banner_x + banner_w - chk_w, banner_y, chk_w, banner_h, int(7 * scale))

            # Bold Red "START" text
            if scale > 0.4:
                lbl = self.font_arcade_big.render("START", True, self.c_red)
                scaled_lbl = pygame.transform.rotozoom(lbl, 0, scale * 0.8)
                lx = banner_x + banner_w // 2 - scaled_lbl.get_width() // 2
                ly = banner_y + banner_h // 2 - scaled_lbl.get_height() // 2
                self.screen.blit(scaled_lbl, (lx, ly))

            # Traffic light box (Red, Amber, Green)
            tl_w = max(6, int(60 * scale))
            tl_h = max(3, int(20 * scale))
            tl_x = banner_x + banner_w // 2 - tl_w // 2
            tl_y = banner_y + banner_h + max(2, int(4 * scale))
            pygame.draw.rect(self.screen, (0, 160, 220), (tl_x, tl_y, tl_w, tl_h))
            r = max(2, int(6 * scale))
            pygame.draw.circle(self.screen, (230, 30, 30), (tl_x + int(tl_w * 0.2), tl_y + tl_h // 2), r)
            pygame.draw.circle(self.screen, (240, 200, 30), (tl_x + int(tl_w * 0.5), tl_y + tl_h // 2), r)
            pygame.draw.circle(self.screen, (30, 230, 60), (tl_x + int(tl_w * 0.8), tl_y + tl_h // 2), r)

        elif item.sprite_type == "palm_tree":
            px = int(point.screen_x + (item.offset * point.screen_w))
            th = max(10, int(85 * scale))
            tw = max(3, int(8 * scale))
            # Trunk
            pygame.draw.rect(self.screen, (140, 90, 50), (px - tw // 2, base_y - th, tw, th))
            # Fronds
            leaf_r = max(6, int(28 * scale))
            pygame.draw.circle(self.screen, (35, 150, 45), (px, base_y - th), leaf_r)
            pygame.draw.circle(self.screen, (50, 180, 60), (px - leaf_r // 2, base_y - th + 4), leaf_r // 2)
            pygame.draw.circle(self.screen, (50, 180, 60), (px + leaf_r // 2, base_y - th + 4), leaf_r // 2)

    def _draw_checkered_rect(self, x: int, y: int, w: int, h: int, size: int) -> None:
        size = max(2, size)
        for cx in range(x, x + w, size):
            for cy in range(y, y + h, size):
                col = (20, 20, 20) if ((cx - x) // size + (cy - y) // size) % 2 == 0 else self.c_white
                rw = min(size, x + w - cx)
                rh = min(size, y + h - cy)
                pygame.draw.rect(self.screen, col, (cx, cy, rw, rh))

    def _render_player_car(self, car: PlayerCar) -> None:
        """Renders authentic 90s arcade Formula race car (inspired by Image 2)."""
        car_w = 190
        car_h = 76
        cx = self.width // 2
        cy = int(self.height * 0.84)
        tilt = int(car.steering * 8)

        # 1. Wide Exposed Rear Racing Slicks (Left and Right Tires)
        tire_w = 40
        tire_h = 44
        # Left tire
        pygame.draw.rect(self.screen, (18, 18, 22), (cx - car_w // 2 + tilt, cy + car_h - tire_h, tire_w, tire_h), border_radius=4)
        pygame.draw.rect(self.screen, (60, 60, 70), (cx - car_w // 2 + tilt + 8, cy + car_h - tire_h + 8, tire_w - 16, tire_h - 16), border_radius=3)
        # Right tire
        pygame.draw.rect(self.screen, (18, 18, 22), (cx + car_w // 2 - tire_w + tilt, cy + car_h - tire_h, tire_w, tire_h), border_radius=4)
        pygame.draw.rect(self.screen, (60, 60, 70), (cx + car_w // 2 - tire_w + tilt + 8, cy + car_h - tire_h + 8, tire_w - 16, tire_h - 16), border_radius=3)

        # 2. Main Formula Chassis Body (Vibrant Orange & Blue like Image 2)
        body_w = car_w - 60
        body_rect = pygame.Rect(cx - body_w // 2 + tilt, cy + 24, body_w, car_h - 32)
        pygame.draw.rect(self.screen, (0, 110, 230), body_rect, border_radius=6)
        # Center orange racing stripe
        pygame.draw.rect(self.screen, (255, 140, 0), (cx - 18 + tilt, cy + 24, 36, car_h - 32))

        # 3. High Downforce Rear Wing (Purple/Magenta and Yellow)
        wing_w = car_w - 20
        wing_h = 16
        pygame.draw.rect(self.screen, (160, 20, 200), (cx - wing_w // 2 + tilt, cy + 10, wing_w, wing_h), border_radius=3)
        pygame.draw.rect(self.screen, self.c_yellow, (cx - wing_w // 2 + tilt, cy + 10, wing_w, 4))
        # Wing endplates
        pygame.draw.rect(self.screen, (220, 20, 20), (cx - wing_w // 2 + tilt, cy + 4, 8, wing_h + 12))
        pygame.draw.rect(self.screen, (220, 20, 20), (cx + wing_w // 2 - 8 + tilt, cy + 4, 8, wing_h + 12))

        # 4. Driver Cockpit & Yellow Helmet
        cockpit_rect = pygame.Rect(cx - 20 + tilt, cy + 8, 40, 22)
        pygame.draw.ellipse(self.screen, (25, 25, 35), cockpit_rect)
        # Yellow racing helmet
        pygame.draw.circle(self.screen, (255, 230, 20), (cx + tilt, cy + 16), 11)
        pygame.draw.rect(self.screen, (20, 20, 20), (cx - 8 + tilt, cy + 14, 16, 5))  # Visor

        # 5. Dual Rear Brake / Exhaust Lights
        b_col = (255, 255, 255) if car.is_braking else (240, 25, 25)
        pygame.draw.rect(self.screen, b_col, (cx - 36 + tilt, cy + car_h - 18, 14, 10), border_radius=2)
        pygame.draw.rect(self.screen, b_col, (cx + 22 + tilt, cy + car_h - 18, 14, 10), border_radius=2)

    def _render_arcade_hud(self, car: PlayerCar, control_state: Any) -> None:
        """Exact reproduction of classic 90s arcade HUD seen in reference Image 2."""
        # Top Row: TOP  11120      TIME      LAP  0'00
        # Row 2:   SCORE 11120       75       SPEED 0mph

        # Column 1: TOP & SCORE
        lbl_top = self.font_arcade_mid.render("TOP", True, self.c_cyan)
        val_top = self.font_arcade_mid.render("11120", True, self.c_cyan)
        self.screen.blit(lbl_top, (80, 20))
        self.screen.blit(val_top, (180, 20))

        score_val = f"{int(car.z * 0.15):05d}"
        lbl_score = self.font_arcade_mid.render("SCORE", True, self.c_cyan)
        val_score = self.font_arcade_mid.render(score_val, True, self.c_cyan)
        self.screen.blit(lbl_score, (60, 52))
        self.screen.blit(val_score, (180, 52))

        # Column 2 (Center): TIME
        lbl_time = self.font_arcade_mid.render("TIME", True, self.c_cyan)
        self.screen.blit(lbl_time, (self.width // 2 - lbl_time.get_width() // 2, 20))

        # Time countdown number in large yellow arcade font
        time_left = max(0, 75 - int(getattr(car, "race_time", 0.0)))
        val_time = self.font_arcade_big.render(f"{time_left:02d}", True, self.c_yellow)
        self.screen.blit(val_time, (self.width // 2 - val_time.get_width() // 2, 48))

        # Column 3 (Right): LAP & SPEED
        lbl_lap = self.font_arcade_mid.render("LAP", True, self.c_cyan)
        val_lap = self.font_arcade_mid.render("0'00", True, self.c_cyan)
        self.screen.blit(lbl_lap, (self.width - 290, 20))
        self.screen.blit(val_lap, (self.width - 150, 20))

        spd_val = f"{int(car.speed)}mph"
        lbl_speed = self.font_arcade_mid.render("SPEED", True, self.c_cyan)
        val_speed = self.font_arcade_mid.render(spd_val, True, self.c_white)
        self.screen.blit(lbl_speed, (self.width - 290, 52))
        self.screen.blit(val_speed, (self.width - 150, 52))

    def _render_camera_inset(self, camera_frame_surf: Optional[pygame.Surface], control_state: Any) -> None:
        """Draws upright, non-inverted camera preview in clean corner frame."""
        inset_w = 280
        inset_h = 210
        inset_x = 24
        inset_y = self.height - inset_h - 20

        # Frame border
        pygame.draw.rect(self.screen, (20, 20, 25), (inset_x - 3, inset_y - 3, inset_w + 6, inset_h + 6), border_radius=4)
        pygame.draw.rect(self.screen, self.c_cyan, (inset_x - 2, inset_y - 2, inset_w + 4, inset_h + 4), 2, border_radius=4)

        if camera_frame_surf is not None:
            scaled = pygame.transform.smoothscale(camera_frame_surf, (inset_w, inset_h))
            self.screen.blit(scaled, (inset_x, inset_y))
        else:
            pygame.draw.rect(self.screen, (30, 30, 35), (inset_x, inset_y, inset_w, inset_h))
            msg = self.font_arcade_small.render("CAMERA SENSOR", True, self.c_yellow)
            self.screen.blit(msg, (inset_x + 70, inset_y + inset_h // 2 - 8))


# Backward compatibility alias
CyberpunkRenderer = ArcadeRenderer
