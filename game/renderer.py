"""
VelocityCV — High-Quality Classic 90s Arcade Renderer
Rock-solid OutRun pseudo-3D road projection, persistent 4-car Grand Prix competitors,
real-time 4-car Leaderboard HUD & Standings, roadside scenery, and zero screen-shake.
"""

import math
import random
from typing import Any, Dict, List, Optional, Tuple
import pygame
from .car import PlayerCar
from .road import RoadSegment, Track


class SparkParticle:
    __slots__ = ("x", "y", "vx", "vy", "color", "max_life", "life")

    def __init__(self, x: float, y: float, vx: float, vy: float, color: Tuple[int, int, int], life: float):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.max_life = life
        self.life = life

    def update(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 400.0 * dt  # gravity
        self.life -= dt
        return self.life > 0


class ArcadeRenderer:
    def __init__(self, screen: pygame.Surface, config: Dict[str, Any]):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.config = config

        self.draw_distance = 180
        self.camera_height = 1000.0
        # Camera depth for 75 deg FOV
        self.camera_depth = 1.0 / math.tan((75.0 / 2.0) * math.pi / 180.0)
        # Camera offset behind player car so player sits at screen bottom (y=720)
        self.camera_offset_z = self.camera_height * self.camera_depth

        self.sky_offset = 0.0

        # 90s Classic Arcade Palette
        self.SKY_TOP = (40, 115, 235)
        self.SKY_BOTTOM = (110, 185, 255)
        self.MOUNTAIN_FAR = (30, 80, 35)
        self.MOUNTAIN_NEAR = (45, 120, 50)
        self.TREE_LINE = (28, 95, 28)
        self.WHITE = (255, 255, 255)
        self.YELLOW = (255, 230, 0)
        self.CYAN = (0, 230, 255)
        self.RED = (230, 30, 30)
        self.GUARDRAIL = (185, 190, 200)

        # Clouds
        random.seed(42)
        self.clouds = [
            {"x": random.uniform(0, self.width), "y": random.uniform(20, 120),
             "w": random.uniform(90, 210), "h": random.uniform(32, 58)}
            for _ in range(8)
        ]
        random.seed()

        # Particles
        self.sparks: List[SparkParticle] = []

        # Fonts
        pygame.font.init()
        self.font_big = pygame.font.SysFont("impact", 38)
        self.font_mid = pygame.font.SysFont("impact", 26)
        self.font_small = pygame.font.SysFont("consolas", 16, bold=True)
        self.font_tiny = pygame.font.SysFont("consolas", 12, bold=True)
        self.font_pos = pygame.font.SysFont("impact", 48)

        self.show_camera_panel = config.get("camera_panel", {}).get("enabled", True)

        # Pre-rendered gradient sky surface
        self._sky_surf = pygame.Surface((self.width, self.height // 2))
        for y_line in range(self.height // 2):
            t = y_line / (self.height / 2)
            r = int(self.SKY_TOP[0] + (self.SKY_BOTTOM[0] - self.SKY_TOP[0]) * t)
            g = int(self.SKY_TOP[1] + (self.SKY_BOTTOM[1] - self.SKY_TOP[1]) * t)
            b = int(self.SKY_TOP[2] + (self.SKY_BOTTOM[2] - self.SKY_TOP[2]) * t)
            pygame.draw.line(self._sky_surf, (r, g, b), (0, y_line), (self.width, y_line))

    # ── Main Render Entry ──────────────────────────────────────────
    def render(
        self,
        car: PlayerCar,
        track: Track,
        control_state: Any,
        dt: float,
        camera_frame_surf: Optional[pygame.Surface] = None,
        traffic_mgr: Optional[Any] = None,
        game_state: str = "RACING",
        countdown_timer: float = 0.0,
    ) -> None:
        # NO SCREEN SHAKE (User requested: rock-solid camera to prevent glitch appearance)
        shake_x = 0
        shake_y = 0

        base_idx = int((car.z % track.total_length) / track.segment_length) % len(track.segments)
        base_segment = track.segments[base_idx]
        base_percent = ((car.z % track.total_length) % track.segment_length) / track.segment_length

        # 1. Sky & Parallax Horizon
        self._render_sky(base_segment.curve, car.speed_ratio, dt)

        # 2. Road & Scenery & Competitors (Authentic pseudo-3D)
        self._render_world(car, track, base_idx, base_percent, traffic_mgr)

        # 3. Exhaust & Spark Particles
        self._update_particles(car, dt)

        # 4. Player Car (Chassis & Cockpit)
        self._render_player_car(car)

        # 5. Game Over crash overlay
        if getattr(car, "game_over", False):
            self._render_crash_overlay()

        # 6. Border warning
        elif car.is_border_collision:
            self._render_border_warning(car.border_collision_side)

        # 7. Telemetry HUD with 4-Car Leaderboard
        self._render_hud(car, control_state, traffic_mgr)

        # 8. Camera / Vision sensor inset
        if self.show_camera_panel:
            self._render_camera_inset(camera_frame_surf, control_state)

    # ── Sky & Mountains ────────────────────────────────────────────
    def _render_sky(self, curve: float, speed_ratio: float, dt: float) -> None:
        horizon = self.height // 2

        # Gradient sky
        self.screen.blit(self._sky_surf, (0, 0))

        # Parallax offset
        self.sky_offset += curve * speed_ratio * 40.0 * dt

        # Clouds
        for c in self.clouds:
            cx = int((c["x"] - self.sky_offset * 0.3) % (self.width + 260)) - 130
            cy = int(c["y"])
            cw = int(c["w"])
            ch = int(c["h"])
            pygame.draw.ellipse(self.screen, (240, 244, 255), (cx, cy, cw, ch))
            pygame.draw.ellipse(self.screen, self.WHITE, (cx + cw // 6, cy - ch // 4, cw * 2 // 3, ch))
            pygame.draw.ellipse(self.screen, self.WHITE, (cx - cw // 6, cy + ch // 6, cw // 2, ch * 2 // 3))

        # Far mountain range
        pts = [(0, horizon)]
        for mx in range(0, self.width + 60, 40):
            sx = mx - int(self.sky_offset * 0.08) % 40
            mh = int(math.sin(mx * 0.012 + self.sky_offset * 0.003) * 40 + 50)
            pts.append((sx, horizon - mh))
        pts.append((self.width, horizon))
        pygame.draw.polygon(self.screen, self.MOUNTAIN_FAR, pts)

        # Near mountain range
        pts2 = [(0, horizon)]
        for mx in range(0, self.width + 60, 50):
            sx = mx - int(self.sky_offset * 0.15) % 50
            mh = int(math.sin(mx * 0.018 + 1.5 + self.sky_offset * 0.006) * 28 + 30)
            pts2.append((sx, horizon - mh))
        pts2.append((self.width, horizon))
        pygame.draw.polygon(self.screen, self.MOUNTAIN_NEAR, pts2)

        # Tree line
        for tx in range(0, self.width + 30, 18):
            sx = (tx - int(self.sky_offset * 1.0)) % (self.width + 30) - 15
            pygame.draw.polygon(
                self.screen, self.TREE_LINE,
                [(sx, horizon), (sx + 9, horizon - 20), (sx + 18, horizon)],
            )

    # ── Pseudo-3D Road & Competitor Rendering ──────────────────────
    def _render_world(
        self, car: PlayerCar, track: Track, base_idx: int,
        base_percent: float, traffic_mgr: Optional[Any],
    ) -> None:
        total = len(track.segments)
        base_segment = track.segments[base_idx]
        player_y = base_segment.p1.world_y + (base_segment.p2.world_y - base_segment.p1.world_y) * base_percent

        cam_x = car.x * track.road_width
        cam_y = self.camera_height + player_y
        cam_z = car.z - self.camera_offset_z
        horizon = self.height // 2

        # Camera segment index along track
        cam_base_idx = int((cam_z % track.total_length) / track.segment_length) % total
        cam_base_percent = ((cam_z % track.total_length) % track.segment_length) / track.segment_length

        # ── Step 1: Project Road Segments from Camera ──
        curve_x = 0.0
        dx = 0.0
        projected = []
        min_z = self.camera_offset_z

        for n in range(self.draw_distance):
            idx = (cam_base_idx + n) % total
            seg = track.segments[idx]

            # Distances from camera
            raw_z1 = n * track.segment_length - (cam_base_percent * track.segment_length)
            raw_z2 = (n + 1) * track.segment_length - (cam_base_percent * track.segment_length)

            cur_dx = dx
            dx += seg.curve
            curve_x += cur_dx

            # Segments completely behind the camera near clipping plane (y > 720)
            if raw_z2 <= min_z:
                projected.append({
                    "seg": seg, "n": n, "visible": False,
                    "scale1": 0.0, "scale2": 0.0,
                    "sx1": float(self.width / 2), "sy1": float(self.height), "sw1": 0.0,
                    "sx2": float(self.width / 2), "sy2": float(self.height), "sw2": 0.0,
                    "clip_y": float(self.height),
                })
                continue

            # Clip near point to camera near clipping plane
            z1 = max(min_z, raw_z1)
            z2 = raw_z2

            # Interpolate curve and elevation if segment straddles near clip plane
            t = (z1 - raw_z1) / (raw_z2 - raw_z1) if (raw_z2 != raw_z1 and raw_z1 < min_z) else 0.0
            near_curve_x = curve_x + t * dx
            near_world_y = seg.p1.world_y + t * (seg.p2.world_y - seg.p1.world_y)

            scale1 = self.camera_depth / z1
            sx1 = self.width / 2 + (scale1 * (near_curve_x - cam_x) * (self.width / 2))
            sy1 = horizon - (scale1 * (near_world_y - cam_y) * (self.height / 2))
            sw1 = scale1 * track.road_width * (self.width / 2)

            scale2 = self.camera_depth / z2
            far_curve_x = curve_x + dx
            sx2 = self.width / 2 + (scale2 * (far_curve_x - cam_x) * (self.width / 2))
            sy2 = horizon - (scale2 * (seg.p2.world_y - cam_y) * (self.height / 2))
            sw2 = scale2 * track.road_width * (self.width / 2)

            entry = {
                "seg": seg,
                "n": n,
                "visible": True,
                "z1": z1,
                "z2": z2,
                "sx1": sx1, "sy1": sy1, "sw1": sw1, "scale1": scale1,
                "sx2": sx2, "sy2": sy2, "sw2": sw2, "scale2": scale2,
                "clip_y": float(self.height),
            }
            projected.append(entry)

        # ── Step 2: Render Road Polygons NEAR-TO-FAR ──
        max_y = float(self.height)

        for entry in projected:
            if not entry.get("visible", False):
                continue

            y1 = int(entry["sy1"])
            y2 = int(entry["sy2"])

            entry["clip_y"] = max_y

            # If segment is behind a hill crest, skip drawing
            if y2 >= max_y:
                continue

            if y1 > max_y:
                y1 = int(max_y)

            sx1, sw1 = entry["sx1"], entry["sw1"]
            sx2, sw2 = entry["sx2"], entry["sw2"]
            seg = entry["seg"]

            # Grass slice spanning entire screen width
            pygame.draw.rect(self.screen, seg.color_grass, (0, y2, self.width, max(1, y1 - y2)))

            # Red & White rumble curbs strictly on outer shoulders (NEVER across the road)
            curb_w1 = max(2, int(sw1 * 0.16))
            curb_w2 = max(2, int(sw2 * 0.16))
            # Left shoulder curb
            pygame.draw.polygon(self.screen, seg.color_rumble, [
                (sx1 - sw1 - curb_w1, y1), (sx1 - sw1, y1),
                (sx2 - sw2, y2), (sx2 - sw2 - curb_w2, y2),
            ])
            # Right shoulder curb
            pygame.draw.polygon(self.screen, seg.color_rumble, [
                (sx1 + sw1, y1), (sx1 + sw1 + curb_w1, y1),
                (sx2 + sw2 + curb_w2, y2), (sx2 + sw2, y2),
            ])

            # Asphalt road surface
            pygame.draw.polygon(self.screen, seg.color_road, [
                (sx1 - sw1, y1), (sx1 + sw1, y1),
                (sx2 + sw2, y2), (sx2 - sw2, y2),
            ])

            # Start/Finish Checkered Grid Line (flat on asphalt at seg.index 0 and 1)
            if seg.index in (0, 1):
                num_checks = 12
                for c in range(num_checks):
                    u1 = -1.0 + (c / (num_checks / 2.0))
                    u2 = -1.0 + ((c + 1) / (num_checks / 2.0))
                    chk_col = self.WHITE if (c + seg.index) % 2 == 0 else (25, 25, 30)
                    cx1_a = sx1 + u1 * sw1
                    cx1_b = sx1 + u2 * sw1
                    cx2_a = sx2 + u1 * sw2
                    cx2_b = sx2 + u2 * sw2
                    pygame.draw.polygon(self.screen, chk_col, [
                        (cx1_a, y1), (cx1_b, y1),
                        (cx2_b, y2), (cx2_a, y2),
                    ])

            # White dashed center line
            elif seg.color_lane == (255, 255, 255):
                lw1 = max(2, int(sw1 * 0.024))
                lw2 = max(2, int(sw2 * 0.024))
                pygame.draw.polygon(self.screen, self.WHITE, [
                    (sx1 - lw1, y1), (sx1 + lw1, y1),
                    (sx2 + lw2, y2), (sx2 - lw2, y2),
                ])

            # Lane dividers (for 3-lane circuit)
            if seg.color_lane == (255, 255, 255) and seg.index not in (0, 1):
                for lane_frac in (-0.33, 0.33):
                    lx1 = sx1 + sw1 * lane_frac
                    lx2 = sx2 + sw2 * lane_frac
                    lw = max(1, int(sw1 * 0.012))
                    pygame.draw.polygon(self.screen, (220, 220, 220), [
                        (lx1 - lw, y1), (lx1 + lw, y1),
                        (lx2 + lw, y2), (lx2 - lw, y2),
                    ])

            # Guardrail crash barrier posts on sharp curves
            if abs(seg.curve) > 1.0 and entry["scale1"] > 0.0006:
                post_h = max(4, int(22 * entry["scale1"] * 1200))
                post_w = max(2, int(6 * entry["scale1"] * 1200))
                if seg.index % 3 == 0:
                    px_l = int(sx1 - sw1 - curb_w1 - post_w)
                    pygame.draw.rect(self.screen, self.GUARDRAIL, (px_l, y1 - post_h, post_w, post_h))
                    px_r = int(sx1 + sw1 + curb_w1)
                    pygame.draw.rect(self.screen, self.GUARDRAIL, (px_r, y1 - post_h, post_w, post_h))

            # Update highest point drawn (lowest numerical Y)
            max_y = float(y2)

        # ── Step 3: Render Roadside Scenery FAR-TO-NEAR ──
        for entry in reversed(projected):
            if not entry.get("visible", False):
                continue
            seg = entry["seg"]
            if seg.scenery and entry["scale1"] > 0.0002:
                self._render_scenery(entry)

        # ── Step 4: Render Competitor Cars FAR-TO-NEAR ──
        if traffic_mgr and traffic_mgr.cars:
            self._render_competitors(car, traffic_mgr, track, projected, cam_base_percent)

    # ── Roadside Scenery (Billboards, Palms, Pines) ────────────────
    def _render_scenery(self, entry: Dict) -> None:
        seg = entry["seg"]
        sx = entry["sx1"]
        sy = int(entry["sy1"])
        sw = entry["sw1"]
        scale = entry["scale1"]

        if scale < 0.0003 or scale > 0.0012:
            return

        for obj in seg.scenery:
            stype = obj.sprite_type
            offset = obj.offset

            if stype == "billboard":
                # Sponsor billboard
                bw = min(160, max(16, int(120 * scale * 1200)))
                bh = min(80, max(10, int(60 * scale * 1200)))
                bx = int(sx + offset * sw - bw // 2)
                by_ = sy - bh

                # Post
                pw = max(2, int(6 * scale * 1200))
                pygame.draw.rect(self.screen, (60, 60, 65), (bx + bw // 2 - pw // 2, by_ + bh, pw, max(6, int(20 * scale * 1200))))

                # Board
                pygame.draw.rect(self.screen, (15, 30, 80), (bx, by_, bw, bh), border_radius=3)
                pygame.draw.rect(self.screen, self.YELLOW, (bx, by_, bw, bh), max(1, int(2 * scale * 1200)), border_radius=3)

                if scale > 0.0008:
                    sponsors = ["SEGA", "VELOCITY", "OUTRUN", "TURBO"]
                    txt = self.font_tiny.render(sponsors[seg.index % len(sponsors)], True, self.WHITE)
                    self.screen.blit(txt, (bx + bw // 2 - txt.get_width() // 2, by_ + bh // 2 - txt.get_height() // 2))

            elif stype == "palm_tree":
                th = max(14, int(140 * scale * 1200))
                tx = int(sx + offset * sw)
                ty = sy
                tr_w = max(2, int(8 * scale * 1200))
                pygame.draw.line(self.screen, (110, 75, 45), (tx, ty), (tx + int(4 * scale * 1200), ty - th), tr_w)
                foliage_r = max(4, int(35 * scale * 1200))
                pygame.draw.circle(self.screen, (35, 140, 45), (tx + int(4 * scale * 1200), ty - th), foliage_r)
                pygame.draw.circle(self.screen, (50, 180, 60), (tx + int(4 * scale * 1200), ty - th), int(foliage_r * 0.7))

            elif stype == "pine_tree":
                th = max(14, int(130 * scale * 1200))
                tw = max(10, int(70 * scale * 1200))
                tx = int(sx + offset * sw)
                ty = sy
                for tier in range(3):
                    tier_y = ty - int(th * (0.35 + tier * 0.25))
                    tier_w = int(tw * (0.9 - tier * 0.22))
                    tier_h = int(th * 0.38)
                    pts = [
                        (tx - tier_w // 2, tier_y),
                        (tx, tier_y - tier_h),
                        (tx + tier_w // 2, tier_y),
                    ]
                    pygame.draw.polygon(self.screen, (25, 95, 35), pts)

    # ── Competitor Car Rendering (Persistent 3 AI Cars) ───────────
    def _render_competitors(
        self, car: PlayerCar, traffic_mgr: Any, track: Track,
        projected: List[Dict], cam_base_percent: float,
    ) -> None:
        visible_cars = []
        seg_len = track.segment_length
        num_proj = len(projected)

        for opp in traffic_mgr.cars:
            # Distance along track relative to player
            dz = opp.z - car.z
            if track.total_length > 0:
                if dz < -track.total_length / 2:
                    dz += track.total_length
                elif dz > track.total_length / 2:
                    dz -= track.total_length

            # Total distance from camera
            cam_dist = self.camera_offset_z + dz

            # Keep visible from near clip plane (screen bottom) up to draw distance
            if cam_dist < self.camera_offset_z * 0.85 or cam_dist > self.draw_distance * seg_len:
                continue

            scale = self.camera_depth / cam_dist

            # Find step along projected road segments
            cam_step = (cam_dist + cam_base_percent * seg_len) / seg_len
            n = int(cam_step)
            frac = cam_step - n

            if n < 0 or n >= num_proj:
                continue

            entry = projected[n]
            if not entry.get("visible", False):
                continue

            next_entry = projected[min(num_proj - 1, n + 1)]
            if not next_entry.get("visible", False):
                next_entry = entry

            scr_x = entry["sx1"] + (next_entry["sx1"] - entry["sx1"]) * frac
            scr_y = entry["sy1"] + (next_entry["sy1"] - entry["sy1"]) * frac
            scr_w = entry["sw1"] + (next_entry["sw1"] - entry["sw1"]) * frac

            car_x = scr_x + (opp.x * scr_w)
            car_y = scr_y

            visible_cars.append({
                "car": opp,
                "cam_dist": cam_dist,
                "cx": int(car_x),
                "cy": int(car_y),
                "scale": scale,
                "tilt": opp.tilt,
            })

        # Draw FAR-TO-NEAR (descending distance from camera)
        visible_cars.sort(key=lambda item: item["cam_dist"], reverse=True)

        for item in visible_cars:
            self._render_single_competitor_car(
                car=item["car"],
                cx=item["cx"],
                cy=item["cy"],
                scale=item["scale"],
                tilt_val=item["tilt"],
            )

    def _render_single_competitor_car(
        self, car: Any, cx: int, cy: int, scale: float, tilt_val: float,
    ) -> None:
        car_s = scale / 0.001
        cw = max(10, int(155 * car_s))
        ch = max(5, int(62 * car_s))
        tilt = int(tilt_val * car_s * 4.0)

        # 1. Ground Shadow
        sw = cw + max(4, int(10 * car_s))
        sh = max(3, int(12 * car_s))
        shadow_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 110), (0, 0, sw, sh))
        self.screen.blit(shadow_surf, (cx - sw // 2, cy - sh // 2))

        # 2. Wide Racing Tires
        tw = max(3, int(cw * 0.22))
        th = max(4, int(ch * 0.58))
        ty = cy - th
        tire_radius = max(1, int(3 * car_s))

        # Left & Right Tires
        pygame.draw.rect(self.screen, (20, 20, 25), (cx - cw // 2 + tilt, ty, tw, th), border_radius=tire_radius)
        pygame.draw.rect(self.screen, (20, 20, 25), (cx + cw // 2 - tw + tilt, ty, tw, th), border_radius=tire_radius)

        # 3. Main Aerodynamic Chassis Body
        bw = int(cw * 0.56)
        bh = int(ch * 0.50)
        by = cy - bh - max(2, int(4 * car_s))
        body_radius = max(2, int(4 * car_s))

        pygame.draw.rect(self.screen, car.color, (cx - bw // 2 + tilt, by, bw, bh), border_radius=body_radius)

        # Gloss highlight stripe
        hl = tuple(min(255, c + 60) for c in car.color)
        pygame.draw.rect(self.screen, hl, (cx - bw // 3 + tilt, by, bw * 2 // 3, max(2, bh // 3)))

        # 4. Rear Wing
        ww = int(cw * 0.82)
        wh = max(2, int(ch * 0.18))
        wy = cy - ch
        pygame.draw.rect(self.screen, (240, 230, 30), (cx - ww // 2 + tilt, wy, ww, wh))

        # Wing Endplates
        ew = max(2, int(4 * car_s))
        pygame.draw.rect(self.screen, car.color, (cx - ww // 2 + tilt, wy - 2, ew, wh + 5))
        pygame.draw.rect(self.screen, car.color, (cx + ww // 2 - ew + tilt, wy - 2, ew, wh + 5))

        # 5. Driver Helmet
        hr = max(2, int(6 * car_s))
        pygame.draw.circle(self.screen, (255, 220, 40), (cx + tilt, by + 2), hr)

        # 6. Car Number
        if scale > 0.0004:
            num_s = self.font_tiny.render(str(car.number), True, (255, 255, 255))
            self.screen.blit(num_s, (cx - num_s.get_width() // 2 + tilt, by + bh // 2 - num_s.get_height() // 2))

        # 7. Rear Rain/Brake Light
        rl = max(2, int(6 * car_s))
        pygame.draw.rect(
            self.screen, (255, 20, 20),
            (cx - rl // 2 + tilt, cy - max(3, int(8 * car_s)), rl, max(2, int(5 * car_s))),
        )

    # ── Particles ──────────────────────────────────────────────────
    def _update_particles(self, car: PlayerCar, dt: float) -> None:
        cx = self.width // 2
        cy = int(self.height * 0.84)

        # Border scraping sparks
        if car.border_sparks:
            spark_x = cx - 100 if car.border_collision_side < 0 else cx + 100
            for _ in range(8):
                vx = random.uniform(-200, -50) if car.border_collision_side < 0 else random.uniform(50, 200)
                vy = random.uniform(-200, -40)
                col = random.choice([(255, 240, 50), (255, 180, 30), (255, 100, 20), (255, 255, 200)])
                self.sparks.append(SparkParticle(spark_x, cy + 20, vx, vy, col, random.uniform(0.15, 0.35)))

        # Vehicle collision impact sparks & tire smoke (Shows physical contact clearly)
        if getattr(car, "car_collision_sparks", False):
            side = getattr(car, "car_collision_side", 1.0)
            spark_x = cx + int(side * 85)
            spark_y = cy + 25
            for _ in range(10):
                vx = side * random.uniform(80, 240) + random.uniform(-40, 40)
                vy = random.uniform(-180, -30)
                col = random.choice([(255, 255, 220), (255, 230, 40), (255, 160, 20), (255, 80, 10)])
                self.sparks.append(SparkParticle(spark_x, spark_y, vx, vy, col, random.uniform(0.18, 0.35)))
            for _ in range(3):
                col = random.choice([(210, 215, 225), (170, 175, 185)])
                self.sparks.append(SparkParticle(spark_x, spark_y + 10, side * random.uniform(20, 80), random.uniform(-60, -10), col, random.uniform(0.25, 0.45)))

        # Exhaust flames
        if car.speed > 30.0:
            for _ in range(2 if car.is_nitro_active else 1):
                ex = cx + random.choice([-25, 25])
                vy = random.uniform(60, 140)
                if car.is_nitro_active:
                    col = random.choice([(0, 200, 255), (130, 50, 255)])
                else:
                    col = random.choice([(255, 130, 20), (255, 70, 10)])
                self.sparks.append(SparkParticle(ex, cy + 50, random.uniform(-10, 10), vy, col, random.uniform(0.08, 0.18)))

        alive = []
        for p in self.sparks:
            if p.update(dt):
                alive.append(p)
                r = max(1, int(3 * (p.life / p.max_life)))
                pygame.draw.circle(self.screen, p.color, (int(p.x), int(p.y)), r)
        self.sparks = alive

    # ── Player Car Model (High-Quality 90s Arcade Cockpit View) ────
    def _render_player_car(self, car: PlayerCar) -> None:
        cx = self.width // 2
        cy = int(self.height * 0.82) + int(car.pitch_offset)
        tilt = int(car.roll_angle)

        car_w = 220
        car_h = 90

        # Ground shadow
        sw, sh = car_w + 30, 26
        shadow = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 140), (0, 0, sw, sh))
        self.screen.blit(shadow, (cx - sw // 2, cy + car_h - 18))

        # ── Tires ──
        tire_w, tire_h = 46, 52
        ty = cy + car_h - tire_h

        for side in (-1, 1):
            tx = cx + side * (car_w // 2 - tire_w // 2) + tilt
            # Rubber
            pygame.draw.rect(self.screen, (15, 15, 18), (tx - tire_w // 2, ty, tire_w, tire_h), border_radius=6)
            # Sidewall tread
            pygame.draw.rect(self.screen, (30, 30, 35), (tx - tire_w // 2 + 2, ty + 2, tire_w - 4, tire_h - 4), 2, border_radius=5)
            # Alloy rim
            rim_r = tire_w // 2 - 8
            pygame.draw.circle(self.screen, (80, 85, 95), (tx, ty + tire_h // 2), rim_r)
            pygame.draw.circle(self.screen, (140, 145, 155), (tx, ty + tire_h // 2), rim_r - 3)
            # Spokes
            for angle in range(0, 360, 72):
                ex = tx + int(math.cos(math.radians(angle)) * (rim_r - 4))
                ey = ty + tire_h // 2 + int(math.sin(math.radians(angle)) * (rim_r - 4))
                pygame.draw.line(self.screen, (80, 85, 95), (tx, ty + tire_h // 2), (ex, ey), 2)
            # Center nut
            pygame.draw.circle(self.screen, (220, 30, 30), (tx, ty + tire_h // 2), 3)

        # Suspension wishbones
        pygame.draw.line(self.screen, (160, 165, 175),
                         (cx - car_w // 2 + tire_w + tilt, ty + 20),
                         (cx - 35 + tilt, ty + 26), 3)
        pygame.draw.line(self.screen, (160, 165, 175),
                         (cx + car_w // 2 - tire_w + tilt, ty + 20),
                         (cx + 35 + tilt, ty + 26), 3)

        # ── Body (Blue with Yellow stripe) ──
        body_w = car_w - 80
        body_h = car_h - 28
        by = cy + 22

        # Main blue body
        pygame.draw.rect(self.screen, (0, 100, 220), (cx - body_w // 2 + tilt, by, body_w, body_h), border_radius=10)
        # Nose taper
        nose_pts = [
            (cx - body_w // 2 + tilt, by + body_h),
            (cx + body_w // 2 + tilt, by + body_h),
            (cx + body_w // 3 + tilt, by + body_h + 12),
            (cx - body_w // 3 + tilt, by + body_h + 12),
        ]
        pygame.draw.polygon(self.screen, (0, 85, 200), nose_pts)

        # Highlight shine
        pygame.draw.rect(self.screen, (50, 150, 255), (cx - body_w // 2 + 5 + tilt, by + 2, body_w - 10, 10), border_radius=5)

        # Yellow center stripe
        pygame.draw.rect(self.screen, (250, 225, 20), (cx - 15 + tilt, by, 30, body_h))
        # Car Number
        num = self.font_tiny.render("1", True, (20, 20, 20))
        self.screen.blit(num, (cx - num.get_width() // 2 + tilt, by + body_h - 16))

        # Side air intakes
        pygame.draw.rect(self.screen, (10, 50, 100), (cx - body_w // 2 + 5 + tilt, by + 14, 13, 20), border_radius=3)
        pygame.draw.rect(self.screen, (10, 50, 100), (cx + body_w // 2 - 18 + tilt, by + 14, 13, 20), border_radius=3)

        # ── Rear Wing ──
        wing_w = car_w - 20
        wing_h = 20
        wy = cy + 4

        pygame.draw.rect(self.screen, (245, 225, 25), (cx - wing_w // 2 + tilt, wy, wing_w, wing_h), border_radius=3)
        pygame.draw.rect(self.screen, self.RED, (cx - wing_w // 2 + tilt, wy + wing_h - 4, wing_w, 4))

        # Wing Endplates
        ep_w, ep_h = 10, wing_h + 18
        pygame.draw.rect(self.screen, self.RED, (cx - wing_w // 2 + tilt, wy - 5, ep_w, ep_h), border_radius=2)
        pygame.draw.rect(self.screen, self.RED, (cx + wing_w // 2 - ep_w + tilt, wy - 5, ep_w, ep_h), border_radius=2)

        # Support pillars
        pygame.draw.rect(self.screen, (30, 30, 35), (cx - 22 + tilt, wy + wing_h, 5, 18))
        pygame.draw.rect(self.screen, (30, 30, 35), (cx + 17 + tilt, wy + wing_h, 5, 18))

        # ── Cockpit & Helmet ──
        pygame.draw.polygon(self.screen, (0, 75, 170), [
            (cx - 13 + tilt, by), (cx + tilt, by - 14), (cx + 13 + tilt, by)
        ])
        # Helmet
        pygame.draw.circle(self.screen, (255, 225, 30), (cx + tilt, by + 5), 14)
        pygame.draw.circle(self.screen, (230, 190, 15), (cx + tilt, by + 5), 14, 2)
        # Visor
        pygame.draw.rect(self.screen, (15, 20, 35), (cx - 10 + tilt, by + 3, 20, 7), border_radius=3)
        pygame.draw.line(self.screen, (180, 200, 220), (cx - 8 + tilt, by + 4), (cx - 2 + tilt, by + 4), 1)

        # Mirrors
        pygame.draw.rect(self.screen, (0, 110, 220), (cx - body_w // 2 - 5 + tilt, by - 1, 9, 6), border_radius=2)
        pygame.draw.rect(self.screen, (0, 110, 220), (cx + body_w // 2 - 4 + tilt, by - 1, 9, 6), border_radius=2)

        # ── Rear lights & exhausts ──
        if car.is_braking:
            rl_col = (255, 50, 50)
        else:
            rl_col = (200, 20, 20) if (pygame.time.get_ticks() // 250) % 2 else (100, 10, 10)
        pygame.draw.rect(self.screen, rl_col, (cx - 8 + tilt, cy + car_h - 18, 16, 10), border_radius=3)

        # Dual exhausts
        for side_off in (-26, 26):
            pygame.draw.circle(self.screen, (45, 45, 50), (cx + side_off + tilt, cy + car_h - 12), 7)
            pygame.draw.circle(self.screen, (190, 170, 90), (cx + side_off + tilt, cy + car_h - 12), 5)

        # ── Collision Impact Contact Flash & Arcade Badge ──
        if getattr(car, "collision_impact_timer", 0.0) > 0.0:
            c_timer = car.collision_impact_timer
            c_side = getattr(car, "car_collision_side", 1.0)
            ix = cx + int(c_side * (car_w // 2 - 15)) + tilt
            iy = cy + car_h // 2

            # Radial impact contact flash
            r_flash = int(20 * (c_timer / 0.35) + 6)
            flash_surf = pygame.Surface((r_flash * 2, r_flash * 2), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (255, 255, 255, 230), (r_flash, r_flash), r_flash)
            pygame.draw.circle(flash_surf, (255, 230, 40, 180), (r_flash, r_flash), int(r_flash * 0.65))
            pygame.draw.circle(flash_surf, (255, 120, 20, 140), (r_flash, r_flash), int(r_flash * 0.35))
            self.screen.blit(flash_surf, (ix - r_flash, iy - r_flash))

            # Arcade Contact Notification Badge
            if c_timer > 0.08:
                imp_txt = self.font_small.render("!! CONTACT !!", True, self.YELLOW)
                self.screen.blit(imp_txt, (cx - imp_txt.get_width() // 2 + int(c_side * 50), cy - 25))

    # ── Crash / Game Over Overlay ──────────────────────────────────
    def _render_crash_overlay(self) -> None:
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((210, 20, 20, 90))
        self.screen.blit(overlay, (0, 0))

        box_w, box_h = 560, 140
        bx = self.width // 2 - box_w // 2
        by_ = self.height // 2 - box_h // 2
        pygame.draw.rect(self.screen, (20, 20, 25), (bx, by_, box_w, box_h), border_radius=8)
        pygame.draw.rect(self.screen, self.YELLOW, (bx, by_, box_w, box_h), 4, border_radius=8)

        txt = self.font_big.render("CRASH! GAME OVER", True, self.RED)
        self.screen.blit(txt, (self.width // 2 - txt.get_width() // 2, by_ + 22))

        sub = self.font_mid.render("PRESS [SPACE] TO RESTART", True, self.YELLOW)
        self.screen.blit(sub, (self.width // 2 - sub.get_width() // 2, by_ + 76))

    def _render_border_warning(self, side: int) -> None:
        bw, bh = 380, 32
        bx = self.width // 2 - bw // 2
        by_ = int(self.height * 0.68)
        pygame.draw.rect(self.screen, (220, 30, 30), (bx, by_, bw, bh), border_radius=4)
        pygame.draw.rect(self.screen, self.YELLOW, (bx, by_, bw, bh), 2, border_radius=4)
        lbl = "LEFT" if side < 0 else "RIGHT"
        t = self.font_small.render(f"!! BARRIER [{lbl}] !!", True, self.WHITE)
        self.screen.blit(t, (self.width // 2 - t.get_width() // 2, by_ + 6))

    # ── HUD with Real-Time 4-Car Leaderboard ────────────────────────
    def _render_hud(self, car: PlayerCar, control_state: Any, traffic_mgr: Optional[Any] = None) -> None:
        # 1. TOP / SCORE (Top Left)
        self.screen.blit(self.font_mid.render("SCORE", True, self.CYAN), (30, 18))
        score_val = f"{int(car.total_distance * 0.15):05d}"
        self.screen.blit(self.font_mid.render(score_val, True, self.WHITE), (110, 18))

        # 2. POSITION BADGE (Under Score)
        leaderboard = traffic_mgr.get_leaderboard(car) if traffic_mgr else []
        player_pos = 1
        for entry in leaderboard:
            if entry.get("is_player"):
                player_pos = entry.get("position", 1)
                break

        pos_str = ["1st", "2nd", "3rd", "4th"][min(3, player_pos - 1)]
        pos_cols = [(255, 215, 0), (220, 225, 235), (205, 127, 50), (225, 60, 60)]
        badge_col = pos_cols[min(3, player_pos - 1)]

        # Position Card
        pw, ph = 140, 68
        px, py = 30, 52
        pygame.draw.rect(self.screen, (15, 18, 25), (px, py, pw, ph), border_radius=6)
        pygame.draw.rect(self.screen, badge_col, (px, py, pw, ph), 2, border_radius=6)

        pos_lbl = self.font_tiny.render("POSITION", True, self.CYAN)
        self.screen.blit(pos_lbl, (px + 12, py + 6))

        pos_num = self.font_pos.render(f"{pos_str}", True, badge_col)
        self.screen.blit(pos_num, (px + 10, py + 20))

        of_four = self.font_small.render("/4", True, self.WHITE)
        self.screen.blit(of_four, (px + pos_num.get_width() + 14, py + 34))

        # 3. TIME REMAINING (Center Top)
        self.screen.blit(self.font_mid.render("TIME", True, self.CYAN), (self.width // 2 - 25, 14))
        t_left = max(0, 75 - int(getattr(car, "race_time", 0.0)))
        t_surf = self.font_big.render(f"{t_left:02d}", True, self.YELLOW)
        self.screen.blit(t_surf, (self.width // 2 - t_surf.get_width() // 2, 40))

        # 4. SPEED (Right of Center)
        spd_val = f"{int(car.speed)}"
        spd_lbl = self.font_big.render(f"{spd_val} MPH", True, self.WHITE)
        self.screen.blit(spd_lbl, (self.width // 2 + 130, 36))

        # 5. REAL-TIME 4-CAR LEADERBOARD STANDINGS (Top Right)
        if leaderboard:
            lb_w, lb_h = 290, 136
            lb_x = self.width - lb_w - 20
            lb_y = 14

            # Translucent back panel
            bg_surf = pygame.Surface((lb_w, lb_h), pygame.SRCALPHA)
            bg_surf.fill((12, 14, 22, 215))
            self.screen.blit(bg_surf, (lb_x, lb_y))
            pygame.draw.rect(self.screen, (40, 50, 70), (lb_x, lb_y, lb_w, lb_h), 1, border_radius=4)

            # Header
            hdr = self.font_tiny.render("── GRAND PRIX STANDINGS ──", True, self.CYAN)
            self.screen.blit(hdr, (lb_x + lb_w // 2 - hdr.get_width() // 2, lb_y + 6))

            # 4 Car Rows
            suffixes = ["1st", "2nd", "3rd", "4th"]
            for idx, entry in enumerate(leaderboard[:4]):
                ry = lb_y + 26 + idx * 26
                is_p = entry.get("is_player", False)

                if is_p:
                    # Player highlight strip
                    hl_surf = pygame.Surface((lb_w - 10, 24), pygame.SRCALPHA)
                    hl_surf.fill((30, 80, 150, 140))
                    self.screen.blit(hl_surf, (lb_x + 5, ry - 2))
                    pygame.draw.rect(self.screen, self.YELLOW, (lb_x + 5, ry - 2, lb_w - 10, 24), 1, border_radius=2)

                # Rank badge
                p_col = pos_cols[idx]
                r_txt = self.font_tiny.render(suffixes[idx], True, p_col)
                self.screen.blit(r_txt, (lb_x + 12, ry + 2))

                # Color pip
                c_col = entry.get("color", (200, 200, 200))
                pygame.draw.rect(self.screen, c_col, (lb_x + 48, ry + 4, 8, 12), border_radius=2)

                # Car Name
                c_name = entry.get("name", "CAR")
                c_num = entry.get("number", idx + 1)
                tag = " [YOU]" if is_p else ""
                n_surf = self.font_tiny.render(f"#{c_num} {c_name}{tag}", True, (255, 255, 255) if is_p else (190, 195, 205))
                self.screen.blit(n_surf, (lb_x + 62, ry + 2))

                # Speed
                spd = f"{int(entry.get('speed', 0))}mph"
                s_surf = self.font_tiny.render(spd, True, self.YELLOW if is_p else (160, 160, 175))
                self.screen.blit(s_surf, (lb_x + lb_w - s_surf.get_width() - 12, ry + 2))

    # ── Camera / Sensor Inset ──────────────────────────────────────
    def _render_camera_inset(self, cam_surf: Optional[pygame.Surface], control_state: Any) -> None:
        iw, ih = 260, 195
        ix, iy = 20, self.height - ih - 20

        pygame.draw.rect(self.screen, (15, 15, 20), (ix - 3, iy - 3, iw + 6, ih + 6), border_radius=4)
        pygame.draw.rect(self.screen, self.CYAN, (ix - 2, iy - 2, iw + 4, ih + 4), 2, border_radius=4)

        if cam_surf is not None:
            scaled = pygame.transform.smoothscale(cam_surf, (iw, ih))
            self.screen.blit(scaled, (ix, iy))
        else:
            pygame.draw.rect(self.screen, (25, 25, 30), (ix, iy, iw, ih))
            msg = self.font_small.render("CAMERA SENSOR", True, self.YELLOW)
            self.screen.blit(msg, (ix + iw // 2 - msg.get_width() // 2, iy + ih // 2 - 8))


# Backward compatibility alias
CyberpunkRenderer = ArcadeRenderer
