"""
VelocityCV — Threaded Camera Capture
Captures webcam frames in a dedicated thread with minimal latency (buffer size 1).
"""

import threading
import time
from typing import Any, Dict, Optional, Tuple
import cv2
import numpy as np


class ThreadedCamera:
    """Non-blocking webcam reader running on its own thread."""

    def __init__(self, config: Dict[str, Any]):
        cam_cfg = config.get("camera", {})
        self.camera_index = int(cam_cfg.get("index", 0))
        self.width = int(cam_cfg.get("width", 640))
        self.height = int(cam_cfg.get("height", 480))
        self.mirror = bool(cam_cfg.get("mirror", True))

        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.is_available = False
        self.error_message = ""

        self._lock = threading.Lock()
        self._latest_frame: Optional[np.ndarray] = None
        self._latest_timestamp: float = 0.0
        self._thread: Optional[threading.Thread] = None

    def start(self) -> bool:
        """Opens the camera and launches the background capture loop."""
        try:
            # cv2.CAP_DSHOW provides fast initialization on Windows
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.cap or not self.cap.isOpened():
                # Fallback to default backend if CAP_DSHOW fails
                self.cap = cv2.VideoCapture(self.camera_index)

            if not self.cap or not self.cap.isOpened():
                self.error_message = f"Could not open camera at index {self.camera_index}."
                self.is_available = False
                return False

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

            # Warm-up camera auto-exposure
            for _ in range(5):
                self.cap.read()
                time.sleep(0.02)

            self.is_running = True
            self.is_available = True
            self._thread = threading.Thread(target=self._capture_loop, daemon=True)
            self._thread.start()
            return True
        except Exception as e:
            self.error_message = str(e)
            self.is_available = False
            return False

    def _capture_loop(self) -> None:
        """Continuously reads frames, keeping only the latest one to eliminate latency."""
        while self.is_running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            now = time.monotonic()
            if self.mirror:
                frame = cv2.flip(frame, 1)

            with self._lock:
                self._latest_frame = frame
                self._latest_timestamp = now

            # Pacing sleep to prevent DirectShow bus flood
            time.sleep(0.008)

    def get_latest_frame(self) -> Tuple[Optional[np.ndarray], float]:
        """Returns the most recent captured frame (BGR) and its capture timestamp."""
        with self._lock:
            if self._latest_frame is None:
                return None, 0.0
            return self._latest_frame.copy(), self._latest_timestamp

    def stop(self) -> None:
        """Stops the thread and releases the webcam device."""
        self.is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        if self.cap:
            self.cap.release()
            self.cap = None
        self.is_available = False
