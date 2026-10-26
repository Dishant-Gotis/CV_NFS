# [PROJECT_NAME] — Hand-Gesture-Controlled Racing Game
### Implementation Specification for an Autonomous Coding Agent

---

## 0. How to Use This Document

This document is a complete specification. The agent implementing it should:

1. Read the entire document before writing any code.
2. Build in the **milestone order** given in Section 12. Do not skip ahead.
3. Treat every item marked **[MUST]** as mandatory, **[SHOULD]** as strongly recommended, and **[MAY]** as optional.
4. Where this document says *"Assumption"*, the choice may be replaced if a better option is found. Any replacement must be recorded in `docs/DECISIONS.md`.
5. Verify the current API of every third-party library before use (library APIs change; do not rely on memory). Pin the versions that were actually tested in `requirements.txt`.
6. After each milestone, run the acceptance checks listed for it and report the results.

Placeholders in square brackets (for example `[PROJECT_NAME]`) are intentionally left for the project owner to fill in.

---

## 1. Project Vision

Build a **Need-for-Speed-style arcade racing game** that is controlled **entirely by the player's hand movements**, captured through a standard webcam and interpreted using computer vision.

When the game starts, a **camera panel** appears on screen showing the live webcam feed with the detected hand skeleton drawn on top. The player steers, accelerates, brakes, and activates nitro boost using hand position, orientation, and gestures. No keyboard or controller is required (a keyboard fallback exists for debugging only).

### 1.1 Goals

- Natural, low-latency, and *fun* hand control — the game must feel responsive, not like a tech demo.
- Runs on an ordinary laptop with an ordinary webcam, with no GPU requirement.
- A visually engaging arcade racing experience: speed, traffic, curves, boost, score.
- A clean, modular codebase in which the vision layer and the game layer are fully decoupled.

### 1.2 Non-Goals (for the first version)

- Online multiplayer.
- Realistic vehicle physics simulation.
- Mobile or console support.
- Photorealistic graphics.

---

## 2. Core User Experience

### 2.1 Player Flow

1. **Launch** → main menu appears (menu is navigable by hand or mouse).
2. **Camera permission and detection** → the camera panel opens; the game verifies a hand is visible.
3. **Calibration (about 5 seconds)** → the player holds a neutral pose; the system records the neutral hand angle and position.
4. **Countdown** → 3 … 2 … 1 … GO.
5. **Race** → the player drives using hand gestures while the camera panel remains visible in a corner.
6. **Finish / Crash-out** → results screen (time, distance, score, top speed) with a restart option via gesture.

### 2.2 The Camera Panel

- **[MUST]** Show the live, **mirrored** webcam feed (mirroring makes the interaction feel natural, like a mirror).
- **[MUST]** Overlay the hand skeleton (21 landmarks and connections).
- **[MUST]** Overlay a small live readout: steering value, throttle/brake state, nitro state, and tracking confidence.
- **[MUST]** Show a clear **"Hand lost"** warning when no hand is detected.
- **[SHOULD]** Default presentation: a **picture-in-picture inset** rendered inside the game window (bottom-left or bottom-right), toggled with a key (`C`).
- **[MAY]** Alternative presentation: a separate resizable window. Make this a config option (`camera_panel.mode = "inset" | "window"`).

---

## 3. Control Scheme

### 3.1 Primary Mode — Single-Hand Control (default)

One hand is held in front of the camera, palm facing the camera, fingers pointing up.

| Game Action | Hand Input | Detection Method |
|---|---|---|
| **Steer left / right** | **Tilt (roll) the hand** left or right, like turning a wheel | Angle of the vector from wrist (landmark 0) to middle-finger base (landmark 9) relative to vertical |
| **Accelerate** | **Open palm** (all fingers extended) | Finger-extension classification |
| **Brake / Reverse** | **Closed fist** | Finger-curl classification |
| **Nitro boost** | **Pinch** (thumb tip touching index tip) — hold while available | Distance between landmark 4 and landmark 8, normalized by hand size |
| **Pause** | Hand leaves frame for longer than `[HAND_LOST_PAUSE_SECONDS]`, or key `P` | Tracking-loss timer |

**Rationale:** tilt-angle steering is independent of where the hand is in the frame, so the player does not have to keep the hand in one exact spot. Open/closed hand maps intuitively to "go / stop".

### 3.2 Alternative Mode — Two-Hand Virtual Steering Wheel (optional)

Both hands are shown to the camera as if holding a steering wheel.

| Game Action | Hand Input |
|---|---|
| **Steer** | Angle of the line connecting the two wrists (landmark 0 of each hand) relative to horizontal |
| **Accelerate** | Automatic while both hands are visible |
| **Brake** | Both hands drop into the lower third of the frame, or both are fists |
| **Nitro** | Both hands move quickly toward the camera (hand-scale increase beyond threshold) or a pinch on either hand |

This mode **[MAY]** be implemented after the single-hand mode is stable. Selectable through `config.control_mode = "single_hand" | "two_hand_wheel"`.

### 3.3 Fallback Mode — Keyboard (debug)

- `A / D` or `← / →` steer; `W / ↑` accelerate; `S / ↓` brake; `Space` nitro.
- **[MUST]** Exists so the game can be developed and tested without a camera.

### 3.4 Control State Contract

The vision layer must output exactly one data structure to the game layer. This is the **only** interface between the two layers.

```python
@dataclass
class ControlState:
    steering: float        # -1.0 (full left) ... +1.0 (full right)
    throttle: float        # 0.0 ... 1.0
    brake: float           # 0.0 ... 1.0
    nitro: bool            # True while boost is requested
    hand_detected: bool    # False when tracking is lost
    confidence: float      # 0.0 ... 1.0 tracking confidence
    timestamp: float       # time.monotonic() of the source frame
```

The game layer must never import OpenCV or the hand-tracking library. It only consumes `ControlState`.

---

## 4. Technical Architecture

### 4.1 Recommended Stack (Assumption)

| Concern | Choice | Reason |
|---|---|---|
| Language | **Python 3.x** (use a version supported by the chosen hand-tracking library; verify) | One language for vision and game, fast iteration |
| Webcam capture | **OpenCV** (`opencv-python`) | Standard, cross-platform |
| Hand tracking | **MediaPipe Hands / Hand Landmarker** | Real-time, CPU-friendly, 21 3D landmarks |
| Game engine | **Pygame** with a pseudo-3D "OutRun-style" road renderer | Simple, fast, and produces a convincing sense of speed without a full 3D engine |
| Math | **NumPy** | Landmark geometry |
| Config | **YAML or JSON** | Tunable thresholds without code changes |

**Upgrade path (optional):** replace the Pygame renderer with a true-3D engine (for example Ursina, Panda3D, Godot, or Unity). Because of the `ControlState` contract in Section 3.4, only the game layer changes. If a non-Python engine is chosen, send `ControlState` from a Python vision process over a local UDP or WebSocket connection as JSON.

### 4.2 Module Layout

```
[PROJECT_NAME]/
├── README.md
├── requirements.txt
├── config.yaml
├── main.py                      # entry point; wires everything together
├── docs/
│   └── DECISIONS.md             # record of deviations from this spec
├── vision/
│   ├── camera.py                # threaded webcam capture
│   ├── hand_tracker.py          # wraps the hand-tracking library, returns landmarks
│   ├── gestures.py              # finger state, pinch, fist/open classification
│   ├── control_mapper.py        # landmarks/gestures -> ControlState
│   ├── filters.py               # smoothing (EMA / One-Euro), deadzone, hysteresis
│   ├── calibration.py           # neutral-pose calibration
│   └── overlay.py               # draws skeleton + HUD readout onto the camera frame
├── game/
│   ├── engine.py                # main loop, state machine (menu/calibrate/race/results)
│   ├── road.py                  # track segments, curves, hills, projection
│   ├── renderer.py              # road, sky, sprites, parallax, HUD
│   ├── car.py                   # player car state and arcade physics
│   ├── traffic.py               # AI cars and obstacles
│   ├── collisions.py
│   ├── nitro.py
│   ├── audio.py                 # engine sound, nitro, crash (optional)
│   └── ui.py                    # menu, HUD, results screen
├── input/
│   ├── control_state.py         # ControlState dataclass
│   └── keyboard_input.py        # fallback provider
├── assets/
│   ├── sprites/
│   ├── sounds/
│   └── fonts/
└── tests/
    ├── test_gestures.py
    ├── test_control_mapper.py
    ├── test_filters.py
    └── test_car_physics.py
```

### 4.3 Threading and Data Flow

```
Webcam ──► [Capture thread] ──► latest frame
                                     │
                                     ▼
                         [Vision thread]
              HandTracker → Gestures → ControlMapper → Filters
                                     │
                     ┌───────────────┴───────────────┐
                     ▼                               ▼
              ControlState (latest)        Annotated camera frame (latest)
                     │                               │
                     ▼                               ▼
              [Main/Game thread]  ◄──── drawn as inset / separate window
              reads latest values each frame; never blocks on vision
```

- **[MUST]** Vision runs in its own thread (or process) so that slow camera frames never lower the game's frame rate.
- **[MUST]** Share data through a "latest value" holder protected by a lock (or a queue of size 1 that discards stale items). Never accumulate a backlog of frames.
- **[MUST]** If vision data is older than `[STALE_INPUT_MS]`, treat it as "hand lost".
- **[SHOULD]** Shut down cleanly: release the camera and join threads on exit, including on exceptions.

### 4.4 Performance Targets

| Metric | Target |
|---|---|
| Game rendering | 60 FPS (minimum 30) |
| Vision processing | 30 FPS or higher |
| Gesture-to-screen latency (hand movement to visible car reaction) | Under 100–150 ms |
| CPU usage | Playable on a mid-range laptop without a dedicated GPU |

---

## 5. Vision Layer — Detailed Specification

### 5.1 Camera Capture

- **[MUST]** Open the default camera; allow selecting a camera index in `config.yaml`.
- **[MUST]** Request a modest resolution (for example 640×480) — higher resolutions add latency without improving gameplay.
- **[MUST]** Flip each frame horizontally **before** tracking so that left/right on screen match the player's real left/right.
- **[MUST]** Handle failure gracefully: camera not found, camera in use, permission denied → show a clear message and offer the keyboard fallback.
- **[SHOULD]** Set the capture buffer size to 1 where supported, to reduce latency.

### 5.2 Hand Tracking

- **[MUST]** Track a single hand in single-hand mode (`max_num_hands = 1`); two hands in wheel mode.
- **[MUST]** Use landmark indices (the standard 21-point hand model):
  - `0` wrist
  - `4` thumb tip, `8` index tip, `12` middle tip, `16` ring tip, `20` pinky tip
  - `5, 9, 13, 17` finger base joints (MCP)
  - `6, 10, 14, 18` middle finger joints (PIP)
- **[MUST]** Configurable detection and tracking confidence thresholds.
- **[MUST]** Note that after mirroring the frame, the library's left/right handedness labels may be swapped. Do not depend on handedness labels for control logic unless verified.
- **[SHOULD]** Prefer the **right hand** by default but accept either hand (`config.preferred_hand = "any" | "left" | "right"`).

### 5.3 Gesture Recognition

All geometry must be **scale-invariant** (normalized by hand size, for example the wrist-to-middle-MCP distance) so the controls work at any distance from the camera.

1. **Steering angle (roll)**
   - Vector `v = landmark[9] − landmark[0]` in image coordinates.
   - `angle_deg = degrees(atan2(v.x, −v.y))` → 0° when the hand points straight up; positive when tilted right.
   - Subtract the calibrated neutral angle.
2. **Finger extended?** A finger is *extended* when its tip is farther from the wrist than its PIP joint (compare distances, not just y-coordinates, so it works when the hand rotates). Thumb needs its own rule (compare tip distance to the index MCP).
3. **Open palm:** at least 4 of 5 fingers extended.
4. **Closed fist:** at most 1 of 5 fingers extended, and all four fingertips are close to the palm.
5. **Pinch:** `distance(landmark[4], landmark[8]) / hand_size < [PINCH_THRESHOLD]`, with hysteresis (see 5.5).
6. **Priority when gestures conflict:** `fist (brake)` > `pinch (nitro)` > `open palm (accelerate)`. Document the final order in code.

### 5.4 Mapping to Control Values

**Steering**

```
if abs(angle) < DEADZONE_DEG:           steering = 0
else:  steering = sign(angle) * (abs(angle) - DEADZONE_DEG) / (MAX_ANGLE_DEG - DEADZONE_DEG)
steering = clamp(steering, -1, 1)
steering = apply_response_curve(steering)   # e.g., sign(s) * |s|^1.3 for finer control near center
```

Suggested starting values (all tunable in config): `DEADZONE_DEG ≈ 8`, `MAX_ANGLE_DEG ≈ 45`.

**Throttle / Brake**

- Open palm → `throttle` ramps toward 1.0; fist → `brake` ramps toward 1.0. Use ramping (not instant jumps) so the car feels smooth.
- No recognized gesture → coast (throttle decays, no brake).

**Nitro**

- `nitro = True` while pinch is held *and* the nitro meter is not empty (the meter itself lives in the game layer).

### 5.5 Filtering and Stability (critical for feel)

- **[MUST]** Smooth the steering signal (exponential moving average or the One-Euro filter). The One-Euro filter is preferred because it removes jitter at rest while staying responsive during fast motion.
- **[MUST]** Apply a **deadzone** around neutral so a resting hand does not cause the car to wander.
- **[MUST]** Apply **hysteresis** to gesture thresholds (for example, enter pinch at 0.30 but leave pinch at 0.40) to prevent flicker.
- **[MUST]** Apply **debouncing**: a gesture must be seen for `[N_FRAMES]` consecutive frames before it changes the state.
- **[MUST]** Hand-lost behavior: for the first `[GRACE_MS]` of tracking loss, hold the last values; then ease steering back to 0 and coast; after `[HAND_LOST_PAUSE_SECONDS]`, pause the game.

### 5.5.1 Calibration

- Display "Hold your hand in a relaxed, neutral position" for about 3–5 seconds.
- Record the median roll angle and hand size over that interval; store as the neutral reference.
- **[SHOULD]** Allow re-calibration at any time with key `R` or a hand gesture.
- **[MAY]** Persist calibration to disk between sessions.

---

## 6. Game Layer — Detailed Specification

### 6.1 Rendering Approach (Assumption: pseudo-3D)

The road is a list of **segments**, each with a world position, curvature, and elevation. Every frame:

1. Starting at the player's position, project the visible segments from near to far using perspective projection.
2. Draw them as horizontal strips from far to near (alternating light/dark colors to convey speed).
3. Offset each strip horizontally by accumulated curvature to produce curves; offset vertically for hills.
4. Draw roadside sprites (trees, signs, buildings) and traffic cars scaled by distance.
5. Draw the sky and a parallax background that shifts with road curvature.
6. Draw the player's car at a fixed screen position, with sprite variants for steering left/right.

### 6.2 Player Car (Arcade Physics)

- State: lateral position on road, speed, steering angle, nitro state.
- `speed` accelerates toward `max_speed` under throttle, decays when coasting, and decreases under brake.
- Lateral movement: `lateral_position += steering * speed_factor * dt`.
- Centrifugal push in curves: on a curve, the car is pushed outward proportionally to curvature and speed; the player must steer against it.
- Going off-road: significant speed penalty and camera shake.
- Nitro: temporary increase of max speed and acceleration, drains a meter, regenerates slowly (or by near-misses with traffic). Add a visual effect (screen-edge speed lines, FOV or camera-distance change, flame sprite).

### 6.3 Track

- **[MUST]** A procedurally or manually defined track composed of straights, left/right curves of varying sharpness, and hills.
- **[MUST]** Defined in data (for example a list of sections in a JSON/YAML file) so that new tracks can be added without code changes.
- **[SHOULD]** Looping or point-to-point track with a finish line and optional checkpoints that add time.

### 6.4 Traffic and Obstacles

- **[MUST]** AI cars that drive in lanes at varying speeds, spawned ahead of the player.
- **[MUST]** Collision detection between the player and traffic (lateral overlap plus depth overlap within a segment).
- **[MUST]** Collision consequence: sharp speed reduction, brief invulnerability, camera shake, sound.
- **[SHOULD]** Near-miss bonus (points and nitro refill).
- **[MAY]** Police or rival cars with simple chase behavior.

### 6.5 Game Modes and Scoring

- **Mode 1 — Time Attack (MVP):** complete the track before the timer expires; checkpoints extend time.
- **Mode 2 — Endless (optional):** infinite road; score is based on distance, speed, and near-misses.
- Score components: distance, average speed bonus, near-miss bonus, nitro-usage bonus, penalty for collisions.

### 6.6 HUD

- Speedometer (digital and/or gauge), nitro meter, timer, score, position/lap if applicable.
- Camera inset with gesture status icons.
- Clear on-screen hints showing the gesture for each action (visible during the countdown and in the pause menu).

### 6.7 State Machine

`MENU → CAMERA_CHECK → CALIBRATION → COUNTDOWN → RACING ⇄ PAUSED → RESULTS → (MENU | COUNTDOWN)`

### 6.8 Audio (optional but recommended)

- Engine sound with pitch tied to speed; nitro whoosh; crash; checkpoint chime; background music with a volume setting.

---

## 7. Configuration (`config.yaml`)

All tunables must live in configuration, never hard-coded. Suggested structure (values are starting points only):

```yaml
camera:
  index: 0
  width: 640
  height: 480
  mirror: true

tracking:
  max_hands: 1
  preferred_hand: any          # any | left | right
  min_detection_confidence: 0.6
  min_tracking_confidence: 0.6

controls:
  mode: single_hand            # single_hand | two_hand_wheel | keyboard
  steering:
    deadzone_deg: 8
    max_angle_deg: 45
    response_exponent: 1.3
    smoothing: one_euro        # one_euro | ema
  gestures:
    pinch_enter: 0.30
    pinch_exit: 0.40
    debounce_frames: 3
  hand_lost:
    grace_ms: 300
    pause_after_seconds: 2.0
    stale_input_ms: 250

camera_panel:
  mode: inset                  # inset | window
  position: bottom_left
  scale: 0.3
  show_skeleton: true
  show_readout: true

game:
  resolution: [1280, 720]
  target_fps: 60
  max_speed: [TBD]
  nitro:
    capacity: [TBD]
    drain_rate: [TBD]
    regen_rate: [TBD]
  track: tracks/default.json
```

---

## 8. Error Handling and Edge Cases

The agent **[MUST]** handle each of the following without crashing:

- Camera missing, busy, or disconnected mid-game → pause, show a message, offer keyboard fallback or retry.
- Hand tracking library fails to initialize → clear error and fallback.
- Poor lighting or low-confidence tracking → on-screen tip ("Improve lighting / move closer").
- Multiple hands in single-hand mode → pick the one with the highest confidence (or the one closest to the camera).
- Very fast hand movement causing a landmark jump → reject physically impossible jumps (for example, a single-frame angle change beyond a threshold) or rely on the filter.
- Window loses focus → pause automatically.
- Slow machine → optionally reduce camera resolution or skip frames dynamically; log the measured FPS.

---

## 9. Testing Strategy

1. **Unit tests** (no camera required):
   - Gesture functions fed with synthetic landmark arrays (open palm, fist, pinch, tilted hand).
   - Control mapper: angle → steering curve, deadzone, clamping.
   - Filters: stability at rest, responsiveness to steps.
   - Car physics: acceleration, braking, off-road penalty, nitro.
2. **Replay tests:** record landmark sequences (not video) to a file and replay them through the pipeline to verify deterministic behavior.
3. **Mock input provider:** a scripted `ControlState` generator (for example, a sine-wave steering signal) to test the game without a camera.
4. **Manual test checklist:** different lighting conditions, different distances from the camera, left and right hand, glasses/sleeves, plain vs. cluttered backgrounds.
5. **Latency check:** log timestamps from frame capture to `ControlState` to rendered frame; report the average and 95th percentile.

---

## 10. Quality, Usability, and Safety Considerations

- **Privacy:** all video is processed locally in memory. **[MUST]** Never save or transmit camera frames. State this in the README.
- **Ergonomics:** the hand-tilt gesture can cause fatigue; **[SHOULD]** keep the required motion small (comfortable range of about ±30–45°) and display a gentle "take a break" reminder after extended play (optional).
- **Accessibility:** configurable sensitivity, deadzone, and an alternative single-gesture-set; keyboard fallback always available.
- **Photosensitivity:** avoid rapid full-screen flashing during nitro and crash effects; provide a "reduce effects" option.
- **Licensing:** use only assets that are original, public-domain, or properly licensed; record asset sources in `assets/CREDITS.md`. Do not use trademarked names or logos (the "Need for Speed" name is a trademark; use `[PROJECT_NAME]` instead).

---

## 11. Documentation Deliverables

The agent **[MUST]** produce:

- `README.md`: overview, install steps, run instructions, control guide with gesture illustrations or descriptions, troubleshooting (camera, lighting), configuration reference.
- `docs/DECISIONS.md`: every deviation from or refinement of this specification, with reasons.
- Inline docstrings on all public functions and classes.
- `requirements.txt` with tested, pinned versions.

---

## 12. Milestones and Acceptance Criteria

Implement in this order. Do not begin a milestone until the previous one's checks pass.

### Milestone 1 — Project Skeleton and Keyboard-Driven Prototype
- Repository structure, config loading, `ControlState`, keyboard input provider.
- Pygame window, main loop at 60 FPS, a flat road that scrolls, a controllable car.
- **Accept:** car steers, accelerates, brakes via keyboard; stable FPS displayed.

### Milestone 2 — Camera Panel and Hand Tracking
- Threaded camera capture; hand landmarks detected and drawn; the camera panel visible as an inset inside the game window; toggle with `C`.
- **Accept:** skeleton overlays correctly on a mirrored feed; no drop in game FPS when the camera is active; camera-failure message works.

### Milestone 3 — Gesture Recognition and Control Mapping
- Steering from tilt, open-palm/fist for throttle/brake, pinch for nitro; filters, deadzone, hysteresis, calibration.
- **Accept:** a stationary hand yields steering ≈ 0 (no drift); gestures do not flicker; the readout on the camera panel matches observed behavior; unit tests pass.

### Milestone 4 — Hand-Controlled Driving
- Connect `ControlState` to the game; handle hand-lost behavior; calibration screen; countdown.
- **Accept:** a player can complete a full lap using only hand gestures; latency measured and logged; hand loss pauses the game safely.

### Milestone 5 — Racing Gameplay
- Curves and hills, centrifugal push, off-road penalty, traffic, collisions, nitro with meter, timer, checkpoints, scoring, HUD, results screen.
- **Accept:** the full game loop (menu → race → results → restart) works end to end.

### Milestone 6 — Polish
- Sprites and parallax, speed lines, camera shake, sounds, music, menu navigation by hand, settings screen (sensitivity, camera panel position, reduce-effects).
- **Accept:** game feels responsive and "fast"; stable for a 15-minute continuous session with no memory growth or crashes.

### Milestone 7 — Optional Extensions
- Two-hand steering-wheel mode, additional tracks, endless mode, ghost car/leaderboard, car selection, packaging into a standalone executable.

---

## 13. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Jittery landmarks cause shaky steering | Poor feel | One-Euro filter, deadzone, response curve |
| Gesture flicker (fist vs. open palm) | Random braking | Hysteresis and debouncing |
| Latency from camera plus processing | Game feels laggy | Threaded pipeline, small resolution, buffer size 1, drop stale frames |
| Different lighting and skin tones, backgrounds | Tracking failures | Confidence thresholds, on-screen tips, calibration; test across conditions |
| Arm fatigue | Short play sessions | Small required motion range, break reminder, adjustable sensitivity |
| Library version incompatibility | Install failures | Pin tested versions; document the supported Python version |
| Scope creep | Unfinished game | Strict milestone order; MVP is Milestones 1–5 |

---

## 14. Definition of Done (MVP)

The project is complete when all of the following are true:

- [ ] The game launches, shows the camera panel with a live hand skeleton, and completes calibration.
- [ ] A player can steer, accelerate, brake, and use nitro using only hand gestures.
- [ ] The racing loop works: track with curves, traffic, collisions, timer, scoring, results, restart.
- [ ] Hand loss, camera failure, and low-confidence situations are handled gracefully.
- [ ] End-to-end latency and FPS targets in Section 4.4 are met on the target machine `[TARGET_HARDWARE]`.
- [ ] Unit tests pass; README and DECISIONS documents are complete.
- [ ] No camera frames are stored or transmitted.

---

## 15. Open Items for the Project Owner

The following details are intentionally left open and should be decided by the project owner (or the agent should propose defaults and record them in `docs/DECISIONS.md`):

- `[PROJECT_NAME]` and visual theme (city night racing, desert, coastal, etc.).
- `[TARGET_HARDWARE]` and operating system(s) to support.
- Final choice of engine (Pygame pseudo-3D vs. a full 3D engine).
- Number of tracks and cars for the first release.
- Deadline and team responsibilities: `[TIMELINE]`, `[TEAM_ROLES]`.
