"""
VelocityCV — Classic 90s Arcade Racing Game
Main Entry Point with Dual-Hand Optical Controls.
"""

import argparse
import sys
from game.config import load_config
from game.engine import GameEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="VelocityCV — Classic 90s Arcade Racing Game")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--mode", type=str, choices=["keyboard", "dual_hand", "single_hand"], default=None, help="Force control mode")
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)
    if args.mode:
        config["controls"]["mode"] = args.mode

    print("=" * 64)
    print(f"  {config['project']['name'].upper()} — CLASSIC 90s ARCADE EDITION")
    print(f"  Theme: {config['project']['theme']}")
    print(f"  Target FPS: {config['game']['target_fps']}")
    print(f"  Resolution: {config['game']['resolution'][0]}x{config['game']['resolution'][1]}")
    print(f"  Control Mode: {config['controls']['mode']}")
    print("=" * 64)
    print("  DUAL-HAND OPTICAL CONTROLS:")
    print("    * CLOSE LEFT HAND   -> Steer Left")
    print("    * CLOSE RIGHT HAND  -> Steer Right")
    print("    * CLOSE BOTH HANDS  -> Brake / Reverse")
    print("    * SHRINK PALMS      -> Modulate Speed (Wide = Fast, Shrunk = Slow)")
    print("  KEYBOARD FALLBACK:")
    print("    [A] / [Left]   : Steer Left")
    print("    [D] / [Right]  : Steer Right")
    print("    [W] / [Up]     : Accelerate")
    print("    [S] / [Down]   : Brake")
    print("    [Space]        : Nitro / Start")
    print("    [C]            : Toggle Camera Sensor Inset")
    print("    [P]            : Pause / Unpause")
    print("    [ESC] / [Q]    : Quit")
    print("=" * 64)

    vision_provider = None
    if config["controls"]["mode"] in ("dual_hand", "single_hand", "two_hand_wheel"):
        try:
            from vision.pipeline import VisionPipeline
            vision_provider = VisionPipeline(config)
            cam_ok = vision_provider.start()
            if cam_ok:
                print("[Vision] Camera and dual-hand optical tracking started.")
            else:
                print("[Vision] Camera unavailable; fallback to keyboard enabled.")
        except Exception as e:
            print(f"[Vision] Failed to initialize vision system: {e}. Falling back to keyboard.")

    try:
        engine = GameEngine(config=config, vision_provider=vision_provider)
        engine.run()
    except KeyboardInterrupt:
        print("\n[VelocityCV] Terminated by user.")
    finally:
        if vision_provider and hasattr(vision_provider, "stop"):
            vision_provider.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
