# Architectural and Design Decisions — VelocityCV

## DECISION 001: Project Name & Theme (Initial)
- **Date:** 2026-10-27
- **Initial Theme:** Cyberpunk Neon Night + Synthwave.

---

## DECISION 002: Python Environment Selection
- **Date:** 2026-10-27
- **Decision:** Use Python 3.10.11 via dedicated `.venv`.
- **Rationale:** `mediapipe` has verified prebuilt wheels for Python 3.10, whereas Python 3.14 lacks wheel support.

---

## DECISION 003: Game Engine Selection
- **Date:** 2026-10-27
- **Decision:** Use `pygame-ce` (Pygame Community Edition) with OutRun-style pseudo-3D road projection.

---

## DECISION 004: Control Interface Contract
- **Date:** 2026-10-27
- **Decision:** Strict decoupling maintained via `input/control_state.py` (`ControlState` dataclass).

---

## DECISION 005: Visual Theme Shift to Classic 90s Arcade
- **Date:** 2026-10-27
- **Decision:** Replaced dark synthwave with **Classic 90s Arcade** (Pole Position / OutRun style matching user reference):
  - Vivid blue sky with pixelated drifting clouds.
  - Green mountain horizon ridge.
  - Alternating lush green grass terrain.
  - High-contrast, clean gray asphalt highway running straight down the center.
  - Striking red-and-white striped curb rumble strips.
  - Authentic overhead START/FINISH truss gantry arch with yellow checkered banner and traffic lights.
  - Classic 90s arcade HUD: `TOP`, `SCORE`, `TIME`, `LAP`, `SPEED` in authentic arcade cyan and yellow font with zero clutter.

---

## DECISION 006: Dual-Hand Control Scheme
- **Date:** 2026-10-27
- **Decision:** Adopted dual-hand optical control requested by user:
  - Both hands tracked simultaneously (`max_hands = 2`).
  - **Left Hand Closed (fist):** Steer Left.
  - **Right Hand Closed (fist):** Steer Right.
  - **Both Hands Closed (fists):** Full Brake.
  - **Palm Openness / Shrink:** Speed modulation. Wide open palm = 100% throttle; shrinking palm inward decreases throttle smoothly.
  - While one hand is closed to steer, the open hand modulates speed.

---

## DECISION 007: Camera Orientation and Road Painter's Algorithm Fixes
- **Date:** 2026-10-27
- **Camera Inversion Fix:** Replaced `np.rot90(np.fliplr())` with `pygame.image.frombuffer(rgb.tobytes(), (w, h), 'RGB')`. Camera preview is now upright, non-inverted, and horizontally mirrored (natural mirror feel).
- **Road Occlusion Fix:** Fixed painter's algorithm rendering order from far to near so the complete highway renders from screen bottom up to the horizon vanishing point.
