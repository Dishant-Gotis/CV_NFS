# VELOCITY // CV
### Hand-Gesture-Controlled Cyberpunk Arcade Racing Game

![Theme: Cyberpunk Neon Night + Synthwave](https://img.shields.io/badge/Theme-Cyberpunk%20Synthwave-ff007f?style=for-the-badge)
![Python 3.10](https://img.shields.io/badge/Python-3.10.11-00f0ff?style=for-the-badge)
![MediaPipe](https://img.shields.io/badge/Vision-MediaPipe%20Hands-ffd700?style=for-the-badge)
![Pygame-CE](https://img.shields.io/badge/Engine-Pygame--CE%2060FPS-39ff14?style=for-the-badge)

---

## 1. Overview

**VelocityCV** is a high-octane, OutRun-style pseudo-3D arcade racer set in a neon-drenched synthwave city. The game is controlled **entirely through real-time hand gestures** captured from any standard webcam via computer vision — no physical steering wheel or keyboard required.

A real-time optical HUD inset displays your live mirrored video feed with an overlaid 21-point neon hand skeleton and live telemetry readings.

---

## 2. Gesture Controls (Primary Single-Hand Mode)

Hold your hand in front of the camera (~0.4 to 0.8 meters away, palm facing camera):

| Action | Hand Gesture | Mechanics & Detection |
|---|---|---|
| **Steer Left / Right** | **Tilt / Roll Hand** ($\pm 30^{\circ}$) | Angle of wrist-to-middle-knuckle vector. Adaptive One-Euro low-pass filter eliminates jitter. |
| **Accelerate** | **Open Palm** | 4 or more fingers extended outward. Throttle smoothly ramps to full power. |
| **Brake / Reverse** | **Closed Fist** | Fingers curled tightly into palm. Active high-intensity taillight flare. |
| **Nitro Boost** | **Pinch** (Thumb + Index) | Touch thumb tip to index fingertip. Activates plasma thrusters, speed lines, and blue-violet exhaust. |
| **Recalibrate** | Key `R` | Re-zeros the neutral tilt angle and hand scale. |
| **Toggle Camera Inset** | Key `C` | Shows / hides the optical sensor inset frame. |
| **Pause** | Key `P` or Hand Left Frame | Automatically pauses if tracking is lost for $>2$ seconds. |

### Keyboard Fallback Mode (Debug & Testing)
* `A` / `←` : Steer Left
* `D` / `→` : Steer Right
* `W` / `↑` : Accelerate
* `S` / `↓` : Brake
* `Space` : Nitro Boost
* `ESC` / `Q` : Exit

---

## 3. Visuals & Synthwave Aesthetics

* **Dynamic Road Geometry:** Perspective-projected segment strips with alternating dark obsidian asphalt, glowing neon cyan and pink rumble curbs, and pulsing lane dashes.
* **Cyberpunk Parallax Skyline:** Multi-layered neon skyscraper silhouettes, animated spires, twinkling stars, and a classic Synthwave grid sun.
* **Procedural Cyber Supercar:** Detailed wedge-body racer featuring glowing neon cyan underglow, continuous rear LED taillight bar with brake bloom, and dynamic steering lean.
* **Visual FX:** Warp speed lines at $>180\text{ km/h}$, particle emitters for exhaust flames and nitro plasma trails, and impact screen shake.
* **AI Traffic & Collisions:** AI traffic cars in lane configurations; near-miss passes award nitro plasma and +500 point bonuses.

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

```bash
# Launch with Hand Gesture Vision tracking (Default):
python main.py

# Launch directly in Keyboard Fallback Mode:
python main.py --mode keyboard
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
