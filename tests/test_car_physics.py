"""
VelocityCV — Unit Tests for Car Physics
Validates acceleration, braking, nitro, off-road drag, and road border collision.
"""

import pytest
from game.car import PlayerCar
from game.config import DEFAULT_CONFIG


@pytest.fixture
def car() -> PlayerCar:
    return PlayerCar(config=DEFAULT_CONFIG)


def test_initial_state(car: PlayerCar) -> None:
    assert car.speed == 0.0
    assert car.x == 0.0
    assert car.z == 0.0
    assert car.nitro_meter == car.nitro_capacity
    assert not car.is_nitro_active
    assert not car.is_offroad
    assert not car.is_border_collision


def test_acceleration(car: PlayerCar) -> None:
    initial_speed = car.speed
    car.update(
        steering_input=0.0,
        throttle_input=1.0,
        brake_input=0.0,
        nitro_requested=False,
        current_curve=0.0,
        track_total_length=100000.0,
        dt=0.1,
    )
    assert car.speed > initial_speed
    assert car.z > 0.0


def test_braking(car: PlayerCar) -> None:
    car.speed = 150.0
    car.update(
        steering_input=0.0,
        throttle_input=0.0,
        brake_input=1.0,
        nitro_requested=False,
        current_curve=0.0,
        track_total_length=100000.0,
        dt=0.1,
    )
    assert car.speed < 150.0
    assert car.is_braking


def test_nitro_boost(car: PlayerCar) -> None:
    car.speed = 100.0
    initial_nitro = car.nitro_meter
    car.update(
        steering_input=0.0,
        throttle_input=1.0,
        brake_input=0.0,
        nitro_requested=True,
        current_curve=0.0,
        track_total_length=100000.0,
        dt=0.2,
    )
    assert car.is_nitro_active
    assert car.nitro_meter < initial_nitro
    assert car.max_speed > car.base_max_speed


def test_offroad_detection_and_penalty(car: PlayerCar) -> None:
    car.speed = 250.0
    car.x = 1.05  # On rumble strip
    car.update(
        steering_input=0.0,
        throttle_input=0.0,
        brake_input=0.0,
        nitro_requested=False,
        current_curve=0.0,
        track_total_length=100000.0,
        dt=0.5,
    )
    assert car.is_offroad
    assert car.speed < 250.0


def test_road_border_collision(car: PlayerCar) -> None:
    car.speed = 200.0
    car.x = 1.20  # Hits the right border barrier (> 1.12)
    car.update(
        steering_input=0.0,
        throttle_input=1.0,
        brake_input=0.0,
        nitro_requested=False,
        current_curve=0.0,
        track_total_length=100000.0,
        dt=0.05,
    )
    assert car.is_border_collision
    assert car.border_sparks
    assert car.border_collision_side == 1
    # Game over on border collision
    assert car.game_over
    # Clamped at border
    assert abs(car.x) <= car.border_limit + 0.01

