"""
Tests for ArcadeRenderer and pseudo-3D road rendering.
"""

import os
import pytest
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

from game.car import PlayerCar
from game.renderer import ArcadeRenderer
from game.road import Track
from game.traffic import TrafficManager
from input.control_state import ControlState


@pytest.fixture
def test_setup():
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    cfg = {
        "game": {"resolution": [1280, 720], "target_fps": 60, "max_speed": 280.0},
        "camera_panel": {"enabled": True},
    }
    car = PlayerCar(cfg)
    track = Track()
    renderer = ArcadeRenderer(screen, cfg)
    traffic_mgr = TrafficManager(track, max_traffic=18)
    return screen, car, track, renderer, traffic_mgr


def test_renderer_frame_render(test_setup):
    screen, car, track, renderer, traffic_mgr = test_setup
    ctrl = ControlState.default()

    # Initial frame
    renderer.render(
        car=car,
        track=track,
        control_state=ctrl,
        dt=0.016,
        traffic_mgr=traffic_mgr,
        game_state="RACING",
    )
    assert screen.get_width() == 1280
    assert screen.get_height() == 720


def test_renderer_with_game_over(test_setup):
    screen, car, track, renderer, traffic_mgr = test_setup
    ctrl = ControlState.default()
    car.game_over = True

    renderer.render(
        car=car,
        track=track,
        control_state=ctrl,
        dt=0.016,
        traffic_mgr=traffic_mgr,
        game_state="GAME_OVER",
    )
    assert car.game_over is True


def test_renderer_traffic_visible(test_setup):
    screen, car, track, renderer, traffic_mgr = test_setup
    ctrl = ControlState.default()

    # Car at z=0, 3 automated AI cars on starting grid
    car.z = 0.0
    traffic_mgr.reset_starting_grid()
    assert len(traffic_mgr.cars) == 3

    # Leaderboard has exactly 4 cars (Player + 3 AI)
    lb = traffic_mgr.get_leaderboard(car)
    assert len(lb) == 4
    assert any(c["is_player"] for c in lb)

    # Should render without any exception
    renderer.render(
        car=car,
        track=track,
        control_state=ctrl,
        dt=0.016,
        traffic_mgr=traffic_mgr,
        game_state="RACING",
    )
