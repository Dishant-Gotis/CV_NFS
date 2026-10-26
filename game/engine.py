"""
VelocityCV — Main Game Engine
Orchestrates the 60 FPS game loop, state machine, arcade physics, traffic AI,
collision detection, telemetry HUD, and decoupled vision / keyboard input.
"""

import sys
import time
from typing import Any, Dict, Optional
import pygame

from .car import PlayerCar
from .collisions import CollisionSystem
from .renderer import CyberpunkRenderer
from .road import Track
from .traffic import TrafficManager
from .ui import GameState, UIManager
from input.control_state import ControlState
from input.keyboard_input import KeyboardInputProvider


class GameEngine:
    def __init__(self, config: Dict[str, Any], vision_provider: Optional[Any] = None):
        self.config = config
        self.vision_provider = vision_provider

        # Display Setup
        res = config.get("game", {}).get("resolution", [1280, 720])
        self.screen_width = int(res[0])
        self.screen_height = int(res[1])
        self.target_fps = int(config.get("game", {}).get("target_fps", 60))

        pygame.init()
        pygame.display.set_caption(f"{config.get('project', {}).get('name', 'VelocityCV')} — Cyberpunk Arcade")
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.clock = pygame.time.Clock()

        # Core Subsystems
        track_file = config.get("game", {}).get("track", "tracks/synthwave_city.json")
        self.track = Track(track_path=track_file)
        self.car = PlayerCar(config=config)
        self.renderer = CyberpunkRenderer(self.screen, config=config)
        self.traffic_mgr = TrafficManager(self.track, max_traffic=14)
        self.collision_system = CollisionSystem()
        self.ui = UIManager(self.screen)
        self.keyboard_input = KeyboardInputProvider()

        # State Machine
        self.state = GameState.MENU
        self.running = False
        self.current_state = ControlState.default()

        # Timers and Telemetry
        self.countdown_timer = 3.5
        self.race_time = 0.0
        self.score = 0
        self.top_speed = 0.0
        self.near_misses = 0
        self.collisions = 0
        self.hand_lost_duration = 0.0

    def run(self) -> None:
        """Executes the 60 FPS game loop."""
        self.running = True
        last_time = time.monotonic()

        while self.running:
            current_time = time.monotonic()
            raw_dt = current_time - last_time
            last_time = current_time
            dt = max(0.001, min(0.05, raw_dt))

            # 1. Event Handling
            self._handle_events()

            # 2. Input Polling
            self._update_input()

            # 3. State Machine & Physics Updates
            self._update_state(dt)

            # 4. Rendering Pass
            self._render_current_state(dt)

            # 5. Flip & Frame Rate Lock
            pygame.display.flip()
            self.clock.tick(self.target_fps)

            # Update Window Title
            fps = self.clock.get_fps()
            mode_lbl = "Hand CV" if (self.current_state.hand_detected and self.vision_provider) else "Keyboard"
            pygame.display.set_caption(
                f"VelocityCV — FPS: {fps:.1f} | Speed: {int(self.car.speed)} km/h | Mode: {mode_lbl} | Score: {self.score}"
            )

        pygame.quit()

    def _update_state(self, dt: float) -> None:
        """State machine tick."""
        if self.state == GameState.MENU:
            # Check for start trigger
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE] or keys[pygame.K_RETURN] or (self.current_state.throttle > 0.6 and self.current_state.hand_detected):
                if self.vision_provider and hasattr(self.vision_provider, "trigger_calibration"):
                    self.vision_provider.trigger_calibration()
                    self.state = GameState.CALIBRATION
                else:
                    self.countdown_timer = 3.5
                    self.state = GameState.COUNTDOWN

        elif self.state == GameState.CALIBRATION:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE] or keys[pygame.K_RETURN]:
                self.countdown_timer = 3.5
                self.state = GameState.COUNTDOWN
                return

            calibrator = getattr(self.vision_provider.mapper, "calibrator", None) if self.vision_provider else None
            if calibrator:
                if not calibrator.is_calibrating and calibrator.calibrated:
                    self.countdown_timer = 3.5
                    self.state = GameState.COUNTDOWN
            else:
                self.countdown_timer = 3.5
                self.state = GameState.COUNTDOWN

        elif self.state == GameState.COUNTDOWN:
            self.countdown_timer -= dt
            if self.countdown_timer <= 0:
                self.state = GameState.RACING

        elif self.state == GameState.RACING:
            self.race_time += dt

            # Hand lost safety pause (Section 5.5 / Section 8)
            if self.vision_provider and not self.current_state.hand_detected:
                self.hand_lost_duration += dt
                if self.hand_lost_duration >= 2.0:
                    self.state = GameState.PAUSED
            else:
                self.hand_lost_duration = 0.0

            # Physics Step
            current_segment = self.track.find_segment(self.car.z)
            self.car.update(
                steering_input=self.current_state.steering,
                throttle_input=self.current_state.throttle,
                brake_input=self.current_state.brake,
                nitro_requested=self.current_state.nitro,
                current_curve=current_segment.curve,
                track_total_length=self.track.total_length,
                dt=dt,
            )

            # Traffic Step
            self.traffic_mgr.update(self.car.z, dt)

            # Collision & Near-Miss Detection
            hit, near_miss = self.collision_system.update(self.car, self.traffic_mgr, dt)
            if hit:
                self.collisions += 1
                self.score = max(0, self.score - 250)
            if near_miss:
                self.near_misses += 1
                self.score += 500

            # Score & Speed Telemetry
            if self.car.speed > self.top_speed:
                self.top_speed = self.car.speed

            # Distance points (proportional to speed)
            self.score += int(self.car.speed * 0.15 * dt)

            # Finish lap check (e.g. after 90 seconds or completed distance)
            if self.race_time >= 90.0:
                self.state = GameState.RESULTS

        elif self.state == GameState.PAUSED:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                self.state = GameState.RACING

        elif self.state == GameState.RESULTS:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE] or keys[pygame.K_RETURN] or (self.current_state.throttle > 0.6 and self.current_state.hand_detected):
                self._reset_race()
                self.countdown_timer = 3.5
                self.state = GameState.COUNTDOWN

    def _reset_race(self) -> None:
        """Resets car and telemetry for a new race."""
        self.car = PlayerCar(config=self.config)
        self.traffic_mgr = TrafficManager(self.track, max_traffic=14)
        self.score = 0
        self.race_time = 0.0
        self.top_speed = 0.0
        self.near_misses = 0
        self.collisions = 0
        self.hand_lost_duration = 0.0

    def _render_current_state(self, dt: float) -> None:
        """Passes current state to renderer and UI overlays."""
        camera_surf = None
        if self.vision_provider and hasattr(self.vision_provider, "get_annotated_frame"):
            camera_surf = self.vision_provider.get_annotated_frame()

        # Render 3D World (Road, Parallax, Car, Traffic, HUD)
        self.renderer.render(
            car=self.car,
            track=self.track,
            control_state=self.current_state,
            dt=dt,
            camera_frame_surf=camera_surf,
            traffic_mgr=self.traffic_mgr,
        )

        # Render State UI Overlays
        if self.state == GameState.MENU:
            self.ui.render_menu()
        elif self.state == GameState.CALIBRATION:
            prog = 0.5
            if self.vision_provider and hasattr(self.vision_provider.mapper, "calibrator"):
                prog = self.vision_provider.mapper.calibrator.progress
            self.ui.render_calibration(prog)
        elif self.state == GameState.COUNTDOWN:
            self.ui.render_countdown(self.countdown_timer)
        elif self.state == GameState.PAUSED:
            self.ui.render_paused()
        elif self.state == GameState.RESULTS:
            self.ui.render_results({
                "score": self.score,
                "top_speed": self.top_speed,
                "distance": int(self.car.z),
                "near_misses": self.near_misses,
                "time_elapsed": self.race_time,
            })

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    self.running = False
                elif event.key == pygame.K_c:
                    self.renderer.show_camera_panel = not self.renderer.show_camera_panel
                elif event.key == pygame.K_p:
                    if self.state == GameState.RACING:
                        self.state = GameState.PAUSED
                    elif self.state == GameState.PAUSED:
                        self.state = GameState.RACING
                elif event.key == pygame.K_r:
                    # Quick recalibration trigger
                    if self.vision_provider and hasattr(self.vision_provider, "trigger_calibration"):
                        self.vision_provider.trigger_calibration()

    def _update_input(self) -> None:
        """Updates control state from vision if tracking, or keyboard fallback."""
        if self.vision_provider and hasattr(self.vision_provider, "get_control_state"):
            vision_state = self.vision_provider.get_control_state()
            if vision_state and vision_state.hand_detected:
                self.current_state = vision_state
                return

        self.current_state = self.keyboard_input.update()
