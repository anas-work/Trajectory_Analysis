"""
Physics unit and integration tests.
Validates analytical gravity, drag range reduction, wind, Magnus lift, and numerical stability.
"""

import pytest
import numpy as np

from cricket_trajectory_engine.config.physics_config import (
    BallConfig,
    EnvironmentConfig,
    AerodynamicsConfig,
    SimulationConfig,
)
from cricket_trajectory_engine.physics.flight_simulator import simulate_flight
from cricket_trajectory_engine.physics.drag import compute_reynolds_number, evaluate_drag_coefficient
from cricket_trajectory_engine.physics.magnus import compute_magnus_force


class TestBallisticAnalyticalGravity:
    """Verifies that numerical solve_ivp exactly matches analytical equations in vacuum."""

    def test_analytical_projectile_match(self):
        ball = BallConfig(mass_kg=0.160, diameter_m=0.0725)
        g = 9.80665
        env = EnvironmentConfig(gravity_m_s2=g, wind_vector_m_s=(0.0, 0.0, 0.0))

        x0, y0, z0 = 0.0, 0.0, 1.20
        vx0, vy0, vz0 = 25.0, 5.0, 15.0

        res = simulate_flight(
            initial_position_m=[x0, y0, z0],
            initial_velocity_m_s=[vx0, vy0, vz0],
            ball_config=ball,
            env_config=env,
            gravity_only=True,
        )

        assert res.solver_success is True
        assert res.landing is not None

        # Analytical flight time to Z = radius:
        # z(t) = z0 + vz0*t - 0.5*g*t^2 = R
        # 0.5*g*t^2 - vz0*t + (R - z0) = 0
        h_drop = z0 - ball.radius_m
        t_analytical = (vz0 + np.sqrt(vz0**2 + 2 * g * h_drop)) / g
        x_analytical = x0 + vx0 * t_analytical
        y_analytical = y0 + vy0 * t_analytical
        range_analytical = np.hypot(x_analytical - x0, y_analytical - y0)
        apex_analytical = z0 + (vz0**2) / (2 * g)

        t_num = res.landing["time_s"]
        pos_num = res.landing["position_m"]
        range_num = res.landing["horizontal_range_m"]
        apex_num = res.max_height_m

        # Tolerances (< 0.05% relative difference):
        assert np.isclose(t_num, t_analytical, rtol=1e-3)
        assert np.isclose(range_num, range_analytical, rtol=1e-3)
        assert np.isclose(apex_num, apex_analytical, rtol=1e-3)
        assert np.isclose(pos_num[0], x_analytical, rtol=1e-3)
        assert np.isclose(pos_num[1], y_analytical, rtol=1e-3)
        assert np.isclose(pos_num[2], ball.radius_m, atol=1e-5)


class TestAerodynamics:
    """Tests drag force, Reynolds number, and range reduction."""

    def test_drag_reduces_range_and_height(self):
        ball = BallConfig()
        env = EnvironmentConfig()
        aero = AerodynamicsConfig(constant_cd=0.32)

        p0 = [0.0, 0.0, 1.0]
        v0 = [30.0, 0.0, 15.0]

        res_vacuum = simulate_flight(p0, v0, ball, env, aero, gravity_only=True)
        res_drag = simulate_flight(p0, v0, ball, env, aero, gravity_only=False)

        assert res_drag.horizontal_range_m < res_vacuum.horizontal_range_m
        assert res_drag.max_height_m < res_vacuum.max_height_m
        # Typically aerodynamic drag reduces cricket ball flight range by 15-30%:
        reduction_ratio = res_drag.horizontal_range_m / res_vacuum.horizontal_range_m
        assert 0.60 < reduction_ratio < 0.90

    def test_reynolds_number_calculation(self):
        ball = BallConfig(diameter_m=0.0725)
        env = EnvironmentConfig(air_density_kg_m3=1.225, dynamic_viscosity_pa_s=1.81e-5)

        re_zero = compute_reynolds_number(0.0, ball, env)
        assert re_zero == 0.0

        # At 30 m/s: Re = 1.225 * 30 * 0.0725 / 1.81e-5 = ~147196
        re_30 = compute_reynolds_number(30.0, ball, env)
        assert np.isclose(re_30, 147196.0, rtol=1e-2)

    def test_wind_relative_velocity_effects(self):
        ball = BallConfig()
        aero = AerodynamicsConfig(constant_cd=0.32)
        p0 = [0.0, 0.0, 1.0]
        v0 = [30.0, 0.0, 15.0]

        env_calm = EnvironmentConfig(wind_vector_m_s=(0.0, 0.0, 0.0))
        # 5 m/s headwind in -X
        env_headwind = EnvironmentConfig(wind_vector_m_s=(-5.0, 0.0, 0.0))
        # 5 m/s tailwind in +X
        env_tailwind = EnvironmentConfig(wind_vector_m_s=(5.0, 0.0, 0.0))
        # 5 m/s crosswind in +Y
        env_crosswind = EnvironmentConfig(wind_vector_m_s=(0.0, 5.0, 0.0))

        res_calm = simulate_flight(p0, v0, ball, env_calm, aero)
        res_head = simulate_flight(p0, v0, ball, env_headwind, aero)
        res_tail = simulate_flight(p0, v0, ball, env_tailwind, aero)
        res_cross = simulate_flight(p0, v0, ball, env_crosswind, aero)

        # Headwind reduces forward landing distance:
        assert res_head.landing["position_m"][0] < res_calm.landing["position_m"][0]
        # Tailwind increases forward landing distance:
        assert res_tail.landing["position_m"][0] > res_calm.landing["position_m"][0]
        # Crosswind in +Y creates relative wind in -Y, causing drag force in +Y (deflection towards +Y):
        assert res_cross.landing["position_m"][1] > res_calm.landing["position_m"][1] + 1.0


class TestMagnusForce:
    """Tests spin parameter, lift coefficient, and force directions."""

    def test_topspin_causes_dip_and_shorter_range(self):
        ball = BallConfig()
        env = EnvironmentConfig()
        p0 = [0.0, 0.0, 1.0]
        v0 = [28.0, 0.0, 14.0]

        # No spin
        aero_nospin = AerodynamicsConfig(constant_cd=0.32, enable_magnus=False)
        # Topspin around +Y axis (omega_y > 0): omega x V = [0, w, 0] x [Vx, 0, 0] = [0, 0, -w*Vx] (downward force)
        aero_topspin = AerodynamicsConfig(
            constant_cd=0.32,
            enable_magnus=True,
            magnus_model="constant_cl",
            constant_cl=0.15,
            spin_rad_s=(0.0, 150.0, 0.0),
        )
        # Backspin around -Y axis (omega_y < 0): produces upward lift
        aero_backspin = AerodynamicsConfig(
            constant_cd=0.32,
            enable_magnus=True,
            magnus_model="constant_cl",
            constant_cl=0.15,
            spin_rad_s=(0.0, -150.0, 0.0),
        )

        res_nospin = simulate_flight(p0, v0, ball, env, aero_nospin)
        res_top = simulate_flight(p0, v0, ball, env, aero_topspin)
        res_back = simulate_flight(p0, v0, ball, env, aero_backspin)

        # Topspin dips earlier -> lower apex and shorter flight time:
        assert res_top.max_height_m < res_nospin.max_height_m
        assert res_top.flight_time_s < res_nospin.flight_time_s

        # Backspin lifts higher -> higher apex and longer flight time:
        assert res_back.max_height_m > res_nospin.max_height_m
        assert res_back.flight_time_s > res_nospin.flight_time_s

    def test_sidespin_causes_lateral_drift(self):
        ball = BallConfig()
        env = EnvironmentConfig()
        p0 = [0.0, 0.0, 1.0]
        v0 = [28.0, 0.0, 14.0]

        # Spin around +Z axis: [0, 0, wz] x [vx, 0, 0] = [0, wz*vx, 0] (lateral drift towards +Y)
        aero_sidespin = AerodynamicsConfig(
            constant_cd=0.32,
            enable_magnus=True,
            magnus_model="constant_cl",
            constant_cl=0.15,
            spin_rad_s=(0.0, 0.0, 120.0),
        )

        res_side = simulate_flight(p0, v0, ball, env, aero_sidespin)
        assert res_side.landing["position_m"][1] > 1.5


class TestNumericalSolverStability:
    """Verifies that simulation results are stable across solver tolerances and step sizes."""

    def test_solver_step_size_invariance(self):
        ball = BallConfig()
        env = EnvironmentConfig()
        aero = AerodynamicsConfig(constant_cd=0.32)
        p0 = [0.0, 0.0, 1.0]
        v0 = [28.0, 2.0, 14.0]

        sim_coarse = SimulationConfig(max_step_s=0.01, rtol=1e-6, atol=1e-8)
        sim_fine = SimulationConfig(max_step_s=0.002, rtol=1e-9, atol=1e-11)

        res_coarse = simulate_flight(p0, v0, ball, env, aero, sim_config=sim_coarse)
        res_fine = simulate_flight(p0, v0, ball, env, aero, sim_config=sim_fine)

        assert np.isclose(res_coarse.landing["time_s"], res_fine.landing["time_s"], rtol=1e-4)
        assert np.isclose(res_coarse.horizontal_range_m, res_fine.horizontal_range_m, rtol=1e-4)
        assert np.isclose(res_coarse.max_height_m, res_fine.max_height_m, rtol=1e-4)

