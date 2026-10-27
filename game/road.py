"""
VelocityCV — Classic 90s Arcade Pseudo-3D Road System
Implements authentic OutRun / Pole Position style road geometry with alternating grass,
red-and-white striped rumble curbs, white center dash, and classic overhead start arch.
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional


class WorldPoint:
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.world_x = x
        self.world_y = y
        self.world_z = z
        self.screen_x = 0
        self.screen_y = 0
        self.screen_w = 0
        self.scale = 0.0

    def project(
        self,
        camera_x: float,
        camera_y: float,
        camera_z: float,
        camera_depth: float,
        width: int,
        height: int,
        road_width: float,
    ) -> None:
        trans_x = self.world_x - camera_x
        trans_y = self.world_y - camera_y
        trans_z = self.world_z - camera_z

        if trans_z <= 0.0:
            self.scale = 0.0
            return

        self.scale = camera_depth / trans_z
        self.screen_x = round((width / 2.0) + (self.scale * trans_x * width / 2.0))
        self.screen_y = round((height / 2.0) - (self.scale * trans_y * height / 2.0))
        self.screen_w = round(self.scale * road_width * width / 2.0)


class SceneryObject:
    def __init__(self, sprite_type: str, offset: float, scale_factor: float = 1.0):
        self.sprite_type = sprite_type
        self.offset = offset
        self.scale_factor = scale_factor


class RoadSegment:
    def __init__(
        self,
        index: int,
        p1: WorldPoint,
        p2: WorldPoint,
        curve: float = 0.0,
        scenery: Optional[List[SceneryObject]] = None,
    ):
        self.index = index
        self.p1 = p1
        self.p2 = p2
        self.curve = curve
        self.scenery: List[SceneryObject] = scenery or []

        # Classic 90s Arcade Colors (Pole Position / OutRun style)
        is_even = (index // 3) % 2 == 0
        if is_even:
            self.color_road = (92, 92, 100)       # Dark gray asphalt
            self.color_grass = (42, 145, 28)      # Dark rich green
            self.color_rumble = (225, 20, 20)     # Vivid red rumble
            self.color_lane = (255, 255, 255)     # Crisp white center dash
        else:
            self.color_road = (105, 105, 115)     # Lighter gray asphalt
            self.color_grass = (58, 175, 38)      # Light bright green
            self.color_rumble = (255, 255, 255)   # White rumble
            self.color_lane = (105, 105, 115)     # Empty dash slot (same as road)


class Track:
    def __init__(
        self,
        track_path: Optional[str] = None,
        segment_length: int = 200,
        rumble_length: int = 3,
        road_width: int = 2400,
        lanes: int = 3,
    ):
        self.segment_length = segment_length
        self.rumble_length = rumble_length
        self.road_width = road_width
        self.lanes = lanes
        self.segments: List[RoadSegment] = []
        self.total_length: float = 0.0

        if track_path and Path(track_path).exists():
            self._load_from_file(track_path)
        else:
            self._build_default_arcade_track()

        self.total_length = len(self.segments) * self.segment_length

    def _load_from_file(self, path: str) -> None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.segment_length = data.get("segment_length", 200)
            self.rumble_length = data.get("rumble_length", 3)
            self.lanes = data.get("lanes", 3)
            self.road_width = data.get("road_width", 2400)

            sections = data.get("sections", [])
            for sec in sections:
                length = sec.get("length", 60)
                curve = sec.get("curve", 0.0)
                elev = sec.get("elevation", 0.0)
                scenery_type = sec.get("scenery", None)
                self._add_road_section(length, curve, elev, scenery_type)
        except Exception as e:
            print(f"[Track] Error loading {path}: {e}. Building default arcade track.")
            self.segments.clear()
            self._build_default_arcade_track()

    def _build_default_arcade_track(self) -> None:
        # Authentic 90s Arcade circuit with billboards, palms and pine trees
        self._add_road_section(60, 0.0, 0.0, "billboard")
        self._add_road_section(50, 0.0, 0.0, "billboard")
        self._add_road_section(70, 1.8, 6.0, "palm_tree")
        self._add_road_section(80, 2.6, 8.0, "pine_tree")
        self._add_road_section(60, 0.0, -6.0, "billboard")
        self._add_road_section(90, -2.4, 4.0, "palm_tree")
        self._add_road_section(70, -1.2, -10.0, "pine_tree")
        self._add_road_section(90, -0.8, -2.0, "billboard")

    def _add_road_section(
        self,
        num_segments: int,
        curve: float,
        elevation: float,
        scenery_type: Optional[str] = None,
    ) -> None:
        start_y = self.segments[-1].p2.world_y if self.segments else 0.0
        end_y = start_y + (elevation * self.segment_length)

        for i in range(num_segments):
            seg_idx = len(self.segments)
            t = (i + 1) / num_segments
            ease_y = start_y + (end_y - start_y) * (math.sin(t * math.pi - (math.pi / 2)) * 0.5 + 0.5)
            prev_y = self.segments[-1].p2.world_y if self.segments else 0.0

            p1 = WorldPoint(0.0, prev_y, seg_idx * self.segment_length)
            p2 = WorldPoint(0.0, ease_y, (seg_idx + 1) * self.segment_length)

            scenery_items = []
            if scenery_type and scenery_type in ("billboard", "palm_tree", "pine_tree"):
                if i % 8 == 0:
                    side = -1.65 if (i % 16 == 0) else 1.65
                    scenery_items.append(SceneryObject(scenery_type, side))

            segment = RoadSegment(seg_idx, p1, p2, curve=curve, scenery=scenery_items)
            self.segments.append(segment)

    def find_segment(self, position_z: float) -> RoadSegment:
        if not self.segments:
            raise ValueError("Track has no segments")
        wrapped_z = position_z % self.total_length
        idx = int(wrapped_z / self.segment_length) % len(self.segments)
        return self.segments[idx]
