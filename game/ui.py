"""
VelocityCV — Classic 90s Arcade UI
Clean, retro arcade menus, countdown, and results screen matching the 90s arcade aesthetic.
"""

from enum import Enum
import math
from typing import Any, Dict
import pygame


class GameState(Enum):
    MENU = "MENU"
    CALIBRATION = "CALIBRATION"
    COUNTDOWN = "COUNTDOWN"
    RACING = "RACING"
    PAUSED = "PAUSED"
    GAME_OVER = "GAME_OVER"
    RESULTS = "RESULTS"


class UIManager:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()

        pygame.font.init()
        self.font_title = pygame.font.SysFont("impact", 54)
        self.font_big = pygame.font.SysFont("impact", 40)
        self.font_mid = pygame.font.SysFont("impact", 26)
        self.font_arcade = pygame.font.SysFont("consolas", 18, bold=True)

        self.c_yellow = (255, 240, 0)
        self.c_cyan = (0, 240, 255)
        self.c_white = (255, 255, 255)
        self.c_red = (230, 20, 20)

    def render_menu(self) -> None:
        """Draws clean 90s arcade menu."""
        # Top banner title
        title_surf = self.font_title.render("VELOCITY // ARCADE", True, self.c_yellow)
        self.screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 130))

        # Instructions
        card_w = 620
        card_h = 240
        card_x = self.width // 2 - card_w // 2
        card_y = 230

        pygame.draw.rect(self.screen, (10, 10, 15), (card_x, card_y, card_w, card_h))
        pygame.draw.rect(self.screen, self.c_yellow, (card_x, card_y, card_w, card_h), 3)

        lines = [
            ("DUAL-HAND OPTICAL CONTROLS", self.c_cyan),
            ("CLOSE LEFT HAND   ->  STEER LEFT", self.c_white),
            ("CLOSE RIGHT HAND  ->  STEER RIGHT", self.c_white),
            ("CLOSE BOTH HANDS  ->  BRAKE / STOP", (255, 80, 80)),
            ("SHRINK PALMS      ->  CONTROL SPEED", (80, 255, 120)),
            ("KEYBOARD FALLBACK :  WASD / ARROWS + SPACE", (180, 180, 200)),
        ]

        cy = card_y + 16
        for text, col in lines:
            t = self.font_arcade.render(text, True, col)
            self.screen.blit(t, (card_x + card_w // 2 - t.get_width() // 2, cy))
            cy += 35

        # Blinking start prompt
        if (pygame.time.get_ticks() // 400) % 2 == 0:
            start_txt = self.font_mid.render("SHOW BOTH HANDS OR PRESS [SPACE] TO START", True, self.c_white)
            self.screen.blit(start_txt, (self.width // 2 - start_txt.get_width() // 2, 530))

    def render_calibration(self, progress: float) -> None:
        title = self.font_big.render("CALIBRATING SENSORS", True, self.c_yellow)
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 220))

        sub = self.font_mid.render(f"HOLD BOTH HANDS VISIBLE: {int(progress * 100)}%", True, self.c_white)
        self.screen.blit(sub, (self.width // 2 - sub.get_width() // 2, 280))

    def render_countdown(self, seconds_left: float) -> None:
        count = math.ceil(seconds_left)
        label = "GO!" if count <= 0 else str(count)
        col = (40, 230, 40) if count <= 0 else self.c_yellow

        surf = self.font_title.render(label, True, col)
        sx = self.width // 2 - surf.get_width() // 2
        sy = self.height // 2 - surf.get_height() // 2
        self.screen.blit(surf, (sx, sy))

    def render_paused(self) -> None:
        title = self.font_title.render("PAUSED", True, self.c_yellow)
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 260))

        sub = self.font_mid.render("PRESS [P] OR [SPACE] TO RESUME", True, self.c_white)
        self.screen.blit(sub, (self.width // 2 - sub.get_width() // 2, 340))

    def render_results(self, stats: Dict[str, Any]) -> None:
        title = self.font_title.render("GRAND PRIX FINISH", True, self.c_yellow)
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 110))

        # ── Left Card: Telemetry & Stats ──
        card_w, card_h = 360, 240
        card_x = self.width // 2 - card_w - 20
        card_y = 200

        pygame.draw.rect(self.screen, (12, 12, 18), (card_x, card_y, card_w, card_h), border_radius=6)
        pygame.draw.rect(self.screen, self.c_yellow, (card_x, card_y, card_w, card_h), 2, border_radius=6)

        hdr = self.font_arcade.render("── RACE TELEMETRY ──", True, self.c_cyan)
        self.screen.blit(hdr, (card_x + card_w // 2 - hdr.get_width() // 2, card_y + 16))

        lines = [
            f"SCORE      : {int(stats.get('score', 0)):05d}",
            f"TOP SPEED  : {int(stats.get('top_speed', 0))} MPH",
            f"DISTANCE   : {int(stats.get('distance', 0))} M",
            f"TIME       : {stats.get('time_elapsed', 0.0):.1f} SEC",
            f"NEAR MISS  : {int(stats.get('near_misses', 0))}",
        ]
        cy = card_y + 50
        for line in lines:
            t = self.font_arcade.render(line, True, self.c_white)
            self.screen.blit(t, (card_x + 35, cy))
            cy += 34

        # ── Right Card: 4-Car Leaderboard ──
        lb_w, lb_h = 420, 240
        lb_x = self.width // 2 + 20
        lb_y = 200

        pygame.draw.rect(self.screen, (12, 12, 18), (lb_x, lb_y, lb_w, lb_h), border_radius=6)
        pygame.draw.rect(self.screen, self.c_yellow, (lb_x, lb_y, lb_w, lb_h), 2, border_radius=6)

        lb_hdr = self.font_arcade.render("── FINAL STANDINGS ──", True, self.c_cyan)
        self.screen.blit(lb_hdr, (lb_x + lb_w // 2 - lb_hdr.get_width() // 2, lb_y + 16))

        leaderboard = stats.get("leaderboard", [])
        pos_suffixes = ["1st", "2nd", "3rd", "4th"]
        pos_colors = [(255, 215, 0), (220, 225, 235), (205, 127, 50), (220, 80, 80)]

        row_y = lb_y + 50
        for idx, entry in enumerate(leaderboard[:4]):
            p_lbl = pos_suffixes[idx] if idx < 4 else f"{idx+1}th"
            p_col = pos_colors[idx] if idx < 4 else self.c_white

            # Row background highlight for player
            is_player = entry.get("is_player", False)
            if is_player:
                pygame.draw.rect(self.screen, (30, 45, 80), (lb_x + 10, row_y - 3, lb_w - 20, 32), border_radius=4)
                pygame.draw.rect(self.screen, self.c_yellow, (lb_x + 10, row_y - 3, lb_w - 20, 32), 1, border_radius=4)

            # Pos badge
            pos_t = self.font_arcade.render(p_lbl, True, p_col)
            self.screen.blit(pos_t, (lb_x + 22, row_y + 3))

            # Team color pip
            c_col = entry.get("color", (200, 200, 200))
            pygame.draw.rect(self.screen, c_col, (lb_x + 75, row_y + 6, 12, 14), border_radius=2)

            # Name & Number
            c_name = entry.get("name", "CAR")
            c_num = entry.get("number", idx + 1)
            player_tag = " [YOU]" if is_player else ""
            txt = f"#{c_num} {c_name}{player_tag}"
            t_surf = self.font_arcade.render(txt, True, (255, 255, 255) if is_player else (200, 200, 210))
            self.screen.blit(t_surf, (lb_x + 98, row_y + 3))

            # Gap / Speed
            gap = entry.get("gap_str", "")
            g_surf = self.font_arcade.render(gap, True, self.c_yellow if is_player else (160, 160, 180))
            self.screen.blit(g_surf, (lb_x + lb_w - g_surf.get_width() - 25, row_y + 3))

            row_y += 38

        restart_txt = self.font_mid.render("PRESS [SPACE] TO RACE AGAIN", True, self.c_cyan)
        self.screen.blit(restart_txt, (self.width // 2 - restart_txt.get_width() // 2, 490))
