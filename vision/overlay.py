"""
VelocityCV — Camera Overlay and Skeleton Visualizer
Draws upright mirrored webcam feed with dual-hand skeletons and retro arcade status HUD.
Converts OpenCV frames right-side-up to Pygame surfaces using frombuffer.
"""

from typing import Any, Dict, List, Optional
import cv2
import numpy as np
import pygame


HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17)
]


class CyberOverlay:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.c_cyan = (255, 240, 0)       # BGR (0, 240, 255)
        self.c_yellow = (0, 240, 255)     # BGR (255, 240, 0)
        self.c_green = (0, 255, 100)      # BGR (100, 255, 0)
        self.c_red = (40, 40, 255)        # BGR (255, 40, 40)
        self.c_white = (255, 255, 255)
        self.c_dark = (20, 20, 20)

    def draw_hands(
        self,
        frame: np.ndarray,
        hands: List[Any],
        control_state: Any,
        left_closed: bool = False,
        right_closed: bool = False,
        left_openness: float = 0.0,
        right_openness: float = 0.0,
    ) -> pygame.Surface:
        """Annotates camera frame with both hands and returns upright Pygame Surface."""
        h, w, _ = frame.shape
        annotated = frame.copy()

        # 1. Draw Skeleton for all detected hands
        if hands:
            for hand in hands:
                coords = [(int(lm.x * w), int(lm.y * h)) for lm in hand.landmarks]

                # Hand color based on side
                is_left_side = hand.center_x < 0.5
                bone_col = self.c_cyan if is_left_side else self.c_yellow

                # Bones
                for start_idx, end_idx in HAND_CONNECTIONS:
                    cv2.line(annotated, coords[start_idx], coords[end_idx], bone_col, 3, cv2.LINE_AA)

                # Joints
                for idx, pt in enumerate(coords):
                    radius = 5 if idx in (0, 4, 8, 12, 16, 20) else 3
                    cv2.circle(annotated, pt, radius, self.c_white, -1, cv2.LINE_AA)

                # Hand side label near wrist
                wrist_pt = coords[0]
                lbl_text = "LEFT HAND" if is_left_side else "RIGHT HAND"
                cv2.putText(
                    annotated,
                    lbl_text,
                    (max(5, wrist_pt[0] - 40), max(20, wrist_pt[1] + 25)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    bone_col,
                    2,
                    cv2.LINE_AA,
                )
        else:
            # Tracking lost banner
            cv2.putText(
                annotated,
                "SHOW BOTH HANDS",
                (w // 2 - 120, h // 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                self.c_yellow,
                2,
                cv2.LINE_AA,
            )

        # 2. Status HUD strip at top of camera frame
        bar_h = 36
        overlay = annotated.copy()
        cv2.rectangle(overlay, (0, 0), (w, bar_h), self.c_dark, -1)
        cv2.addWeighted(overlay, 0.7, annotated, 0.3, 0, annotated)

        # Left hand indicator
        l_status = "CLOSED [LEFT]" if left_closed else f"OPEN {int(left_openness * 100)}%"
        l_col = self.c_red if left_closed else self.c_green
        cv2.putText(annotated, f"L: {l_status}", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.45, l_col, 1, cv2.LINE_AA)

        # Right hand indicator
        r_status = "CLOSED [RIGHT]" if right_closed else f"OPEN {int(right_openness * 100)}%"
        r_col = self.c_red if right_closed else self.c_green
        cv2.putText(annotated, f"R: {r_status}", (w - 180, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.45, r_col, 1, cv2.LINE_AA)

        # 3. Convert BGR NumPy array directly to Pygame Surface (UPRIGHT, NOT INVERTED)
        rgb_frame = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        surf = pygame.image.frombuffer(rgb_frame.tobytes(), (w, h), "RGB")
        return surf

    # Legacy draw wrapper
    def draw(self, frame: np.ndarray, landmarks: Optional[List[Any]], control_state: Any, **kwargs) -> pygame.Surface:
        hands = []
        if landmarks:
            class DummyHand:
                def __init__(self, lms):
                    self.landmarks = lms
                    self.center_x = 0.5
            hands = [DummyHand(landmarks)]
        return self.draw_hands(frame, hands, control_state)
