"""
Unit tests for ground collision, restitution, friction, and multi-bounce mechanics.
"""

import pytest
import numpy as np

from cricket_trajectory_engine.config.physics_config import (
    BallConfig,
    GroundCollisionConfig,
)
from cricket_trajectory_engine.physics.ground_collision import (
    resolve_ground_impact,
    simulate_multi_bounce,
)


class TestGroundCollision:
    """Tests normal restitution and tangential friction impulse."""

    def test_normal_velocity_inversion_and_energy_loss(self):
        ball = BallConfig()
        collision = GroundCollisionConfig(restitution_normal=0.60, friction_tangential=0.30)

        pre_v = np.array([20.0, 0.0, -10.0])
        pre_spin = np.array([0.0, 0.0, 0.0])

        post_v, post_spin, loss = resolve_ground_impact(pre_v, pre_spin, ball, collision)

        # Normal velocity inverted with restitution ratio:
        assert np.isclose(post_v[2], 0.60 * 10.0, atol=1e-5)
        # Tangential velocity reduced by friction:
        assert post_v[0] < pre_v[0]
        # Energy strictly dissipated:
        assert loss > 0.0
        e_pre = 0.5 * ball.mass_kg * np.sum(pre_v**2)
        e_post = 0.5 * ball.mass_kg * np.sum(post_v**2)
        assert e_post < e_pre

    def test_friction_induces_topspin_on_bounce(self):
        ball = BallConfig()
        collision = GroundCollisionConfig(restitution_normal=0.55, friction_tangential=0.35)

        # Moving forward with no initial spin:
        pre_v = np.array([22.0, 0.0, -12.0])
        pre_spin = np.array([0.0, 0.0, 0.0])

        post_v, post_spin, _ = resolve_ground_impact(pre_v, pre_spin, ball, collision)

        # Ground friction acts backward in -X at contact point [0, 0, -R].
        # Torque = r x F_friction = [0, 0, -R] x [-Fx, 0, 0] = [0, +R*Fx, 0].
        # Therefore, angular velocity induced around +Y is positive (topspin forward roll):
        assert post_spin[1] > 0.0


class TestMultiBounceSimulation:
    """Tests sequential bouncing and rolling till stop."""

    def test_multi_bounce_decreases_height_and_stops(self):
        p0 = np.array([0.0, 0.0, 1.2])
        v0 = np.array([18.0, 1.0, 8.0])

        res = simulate_multi_bounce(p0, v0)

        assert res.stopped is True
        assert len(res.bounces) >= 2

        # Check successive bounce peak heights decrease:
        b1 = res.bounces[0]
        b2 = res.bounces[1]
        assert b2.pre_speed_m_s < b1.pre_speed_m_s

        # Final position should be on the ground (Z = radius):
        assert np.isclose(res.final_stopping_position_m[2], BallConfig().radius_m, atol=1e-3)
        assert res.total_horizontal_distance_m > 0.0

