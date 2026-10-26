"""
VelocityCV — Game Configuration Loader
Reads config.yaml and provides structured settings with safe fallbacks.
"""

from pathlib import Path
from typing import Any, Dict
import yaml


DEFAULT_CONFIG: Dict[str, Any] = {
    "project": {"name": "VelocityCV", "theme": "cyberpunk_synthwave"},
    "camera": {"index": 0, "width": 640, "height": 480, "mirror": True, "fps": 30},
    "tracking": {
        "max_hands": 1,
        "preferred_hand": "any",
        "min_detection_confidence": 0.6,
        "min_tracking_confidence": 0.6,
    },
    "controls": {
        "mode": "keyboard",
        "steering": {
            "deadzone_deg": 8.0,
            "max_angle_deg": 45.0,
            "response_exponent": 1.3,
            "smoothing": "one_euro",
            "one_euro_min_cutoff": 1.0,
            "one_euro_beta": 0.05,
            "one_euro_d_cutoff": 1.0,
        },
        "gestures": {
            "pinch_enter": 0.30,
            "pinch_exit": 0.40,
            "debounce_frames": 3,
            "finger_curl_threshold": 0.95,
        },
        "hand_lost": {
            "grace_ms": 300,
            "pause_after_seconds": 2.0,
            "stale_input_ms": 250,
        },
    },
    "camera_panel": {
        "mode": "inset",
        "position": "bottom_left",
        "scale": 0.28,
        "show_skeleton": True,
        "show_readout": True,
        "enabled": True,
    },
    "game": {
        "resolution": [1280, 720],
        "target_fps": 60,
        "max_speed": 320.0,
        "acceleration": 140.0,
        "braking": 260.0,
        "deceleration": 45.0,
        "offroad_deceleration": 180.0,
        "centrifugal_force": 0.35,
        "nitro": {
            "capacity": 100.0,
            "drain_rate": 35.0,
            "regen_rate": 8.0,
            "near_miss_bonus": 25.0,
            "speed_boost_factor": 1.35,
            "acceleration_boost_factor": 1.8,
        },
        "track": "tracks/synthwave_city.json",
        "visuals": {
            "bloom": True,
            "speed_lines": True,
            "screen_shake": True,
            "neon_glow": True,
            "crt_scanlines": False,
        },
    },
}


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Loads configuration from YAML file, merging with default fallbacks."""
    path = Path(config_path)
    if not path.exists():
        return DEFAULT_CONFIG

    try:
        with open(path, "r", encoding="utf-8") as f:
            user_cfg = yaml.safe_load(f) or {}
        # Deep merge with defaults
        merged = _deep_merge(DEFAULT_CONFIG, user_cfg)
        return merged
    except Exception as e:
        print(f"[Config] Error loading {config_path}: {e}. Using defaults.")
        return DEFAULT_CONFIG


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result
