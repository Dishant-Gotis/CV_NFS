"""
VelocityCV — Vision Pipeline Thread
Coordinates dual-hand webcam tracking, control mapping, and annotated preview surface.
"""

import threading
import time
from typing import Any, Dict, Optional
import pygame

from input.control_state import ControlState
from .camera import ThreadedCamera
from .control_mapper import ControlMapper
from .hand_tracker import HandTracker
from .overlay import CyberOverlay


class VisionPipeline:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

        self.camera = ThreadedCamera(config)
        self.tracker = HandTracker(config)
        self.mapper = ControlMapper(config)
        self.overlay = CyberOverlay(config)

        self._lock = threading.Lock()
        self._latest_state: ControlState = ControlState.default()
        self._latest_surface: Optional[pygame.Surface] = None
        self._is_running = False
        self._worker_thread: Optional[threading.Thread] = None

    def start(self) -> bool:
        cam_started = self.camera.start()
        if not cam_started:
            print(f"[VisionPipeline] Camera initialization warning: {self.camera.error_message}")

        self._is_running = True
        self._worker_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._worker_thread.start()
        return cam_started

    def _run_loop(self) -> None:
        target_delay = 1.0 / 30.0

        while self._is_running:
            loop_start = time.monotonic()
            frame, frame_time = self.camera.get_latest_frame()

            if frame is None:
                state = self.mapper.process_hands([], timestamp=loop_start)
                with self._lock:
                    self._latest_state = state
                time.sleep(0.02)
                continue

            # Detect both hands
            detected_hands = self.tracker.process_frame(frame)

            # Map dual-hand state
            state = self.mapper.process_hands(detected_hands, timestamp=frame_time)

            # Draw preview surface
            annotated_surf = self.overlay.draw_hands(
                frame=frame,
                hands=detected_hands,
                control_state=state,
                left_closed=self.mapper.left_hand_closed,
                right_closed=self.mapper.right_hand_closed,
                left_openness=self.mapper.left_openness,
                right_openness=self.mapper.right_openness,
            )

            with self._lock:
                self._latest_state = state
                self._latest_surface = annotated_surf

            elapsed = time.monotonic() - loop_start
            sleep_time = max(0.001, target_delay - elapsed)
            time.sleep(sleep_time)

    def get_control_state(self) -> ControlState:
        with self._lock:
            return self._latest_state

    def get_annotated_frame(self) -> Optional[pygame.Surface]:
        with self._lock:
            return self._latest_surface

    def trigger_calibration(self) -> None:
        self.mapper.calibrator.start()

    def stop(self) -> None:
        self._is_running = False
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)
        self.camera.stop()
        self.tracker.close()
