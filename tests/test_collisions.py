"""
VelocityCV — Unit Tests for Collision & Near-Miss System
Tests car proximity, direct collision slowdown, invulnerability frames, and near-miss bonuses.
"""

import pytest
from game.car import PlayerCar
from game.collisions import CollisionSystem
from game.config import DEFAULT_CONFIG
from game.road import Track
from game.traffic import TrafficCar, TrafficManager


@pytest.fixture
def collision_env():
    track = Track()
    player = PlayerCar(config=DEFAULT_CONFIG)
    traffic_mgr = TrafficManager(track, max_traffic=0)
    col_system = CollisionSystem(invulnerability_seconds=1.5)
    return player, traffic_mgr, col_system


def test_direct_collision(collision_env):
    player, traffic_mgr, col_system = collision_env
    player.z = 1000.0
    player.x = 0.0
    player.speed = 200.0

    # Place traffic directly in front of player
    traffic_mgr.cars.append(TrafficCar(z=1050.0, lane_x=0.0, speed=100.0, color=(255, 0, 0)))

    hit, near_miss = col_system.update(player, traffic_mgr, dt=0.016)
    assert hit
    assert not near_miss
    assert player.speed < 200.0
    assert col_system.invulnerable_timer > 0.0


def test_near_miss_bonus(collision_env):
    player, traffic_mgr, col_system = collision_env
    player.z = 1000.0
    player.x = 0.0
    player.speed = 220.0
    player.nitro_meter = 20.0

    # Place traffic in adjacent lane within passing zone
    traffic_mgr.cars.append(TrafficCar(z=1040.0, lane_x=0.6, speed=120.0, color=(0, 255, 0)))

    hit, near_miss = col_system.update(player, traffic_mgr, dt=0.016)
    assert not hit
    assert near_miss
    # Nitro bonus awarded
    assert player.nitro_meter > 20.0
