# VELOCITY // CV
### Dual-Hand Gesture-Controlled 90s Arcade Racing Game

![Theme: Classic 90s Arcade](https://img.shields.io/badge/Theme-Classic%2090s%20Arcade-00f0ff?style=for-the-badge)
![Python 3.10](https://img.shields.io/badge/Python-3.10.11-00f0ff?style=for-the-badge)
![MediaPipe](https://img.shields.io/badge/Vision-MediaPipe%20Hands-ffd700?style=for-the-badge)
![Pygame-CE](https://img.shields.io/badge/Engine-Pygame--CE%2060FPS-39ff14?style=for-the-badge)

---

## 1. Overview

**VelocityCV** is a high-octane, OutRun / Pole Position-style pseudo-3D arcade racer inspired by classic 90s arcade cabinets (Sega OutRun, Super Monaco GP). The game is controlled **entirely through real-time dual-hand gestures** captured from any standard webcam via computer vision — no physical steering wheel or keyboard required.

A real-time optical HUD inset displays your live mirrored video feed (right-side up) with an overlaid 21-point dual-hand skeletal tracker and wrist labels.

---

## 2. Gesture Controls (Dual-Hand Arcade Scheme)

Present both hands in front of the camera (~0.4 to 0.8 meters away, palms facing camera):

| Action | Hand Gesture | Mechanics & Detection |
|---|---|---|
| **Steer Left** | **Left Fist Closed** (Right hand open) | Smooth analog steering to the left. |
| **Steer Right** | **Right Fist Closed** (Left hand open) | Smooth analog steering to the right. |
| **Brake / Decelerate** | **Both Fists Closed** | Closes both fists simultaneously for strong braking and brake light activation. |
| **Speed / Throttle Control** | **Palm Openness** (Shrink / Expand) | Continuous speed modulation: Open flat palms = maximum throttle; shrink/curl palms inward = throttle feathering. |
| **Skip Calibration** | Key `Space` | Press Space at the countdown screen to immediately skip straight to GO! |
| **Recalibrate** | Key `R` | Re-zeros the neutral hand tracking baselines. |
| **Toggle Camera Inset** | Key `C` | Shows / hides the optical sensor inset frame. |
| **Pause** | Key `P` or Hands Left Frame | Automatically pauses if tracking is lost. |

### Keyboard Fallback Mode (Debug & Testing)
* `A` / `←` : Steer Left
* `D` / `→` : Steer Right
* `W` / `↑` : Accelerate
* `S` / `↓` : Brake
* `Space` : Nitro Boost / Skip Countdown
* `ESC` / `Q` : Exit

---

## 3. Visuals & 90s Arcade Quality

* **Starting Grid & Pack AI:** 6 rival competitors on the starting grid directly in front of the player (staggered pole position) plus 12 field competitors racing dynamically with lane-changing and drafting.
* **Road Border & Guardrail Collisions:** Impacting the red-and-white rumble curbs or guardrails triggers lateral rebound physics, speed penalty, screen shake, and sparking particle effects.
* **Detailed Formula / Arcade Racer Model:** Procedural high-fidelity Formula car featuring wide textured slicks with metallic 5-spoke alloy rims, dual-tone aerodynamic sidepods with specular light highlights, cockpit roll hoop, helmet visor reflections, rear wing endplates, and pulsing F1 rain light.
* **Overhead START Gantry:** 3D lattice gantry spanning the highway with working 3-2-1 red-to-green traffic signals.
* **Classic 90s Horizon:** Clean multi-tier mountain ridges, cumulus clouds, and azure sky true to classic Sega arcade cabinets.
* **Clean 90s HUD:** Authentic top-row `TOP`, `SCORE`, `TIME`, `LAP`, and digital gear/tachometer readout.

---

## 4. Installation & Setup

VelocityCV uses Python 3.10 for stable MediaPipe compatibility:

```bash
# 1. Clone repository
git clone https://github.com/Dishant-Gotis/CV_NFS.git
cd CV_NFS

# 2. Activate Python 3.10 virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Install pinned dependencies (if not already installed)
pip install -r requirements.txt
```

---

## 5. Running the Game

You can run the game with 1 click using the launcher scripts, or directly with the virtual environment's Python:

```powershell
# Option 1: 1-Click Launcher (Batch or PowerShell)
.\run_game.bat
# or
.\run_game.ps1

# Option 2: Direct Virtual Environment Python (Default Dual-Hand Vision Tracking)
.\.venv\Scripts\python.exe main.py

# Option 3: Keyboard Fallback Mode
.\.venv\Scripts\python.exe main.py --mode keyboard
```

---

## 6. Testing

The codebase includes an automated unit test suite with 18 unit tests validating car physics, gesture classification, One-Euro filters, and collision mathematics:

```bash
python -m pytest
```

---

## 7. Privacy & Security

**Privacy Guarantee:** All video frames captured from your webcam are processed locally in real-time RAM. **No images or video recordings are ever saved to disk, transmitted over the internet, or logged.**
