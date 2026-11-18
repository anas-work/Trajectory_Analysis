"""
Authoritative Trajectory and Fielder Benchmark Recalculation Tests.
Validates the complete recalculation of ball trajectories at elevation 45.0 degrees
against Square Leg (3.0, -20.0 m) and Deep Square Leg (10.0, -62.0 m)
across Static, Club, and Elite fielder configurations.
"""

import math
import pytest
import numpy as np

from cricket_trajectory_engine.config.physics_config import (
    BallConfig,
    EnvironmentConfig,
    AerodynamicsConfig,
    SimulationConfig,
    GroundCollisionConfig,
    FieldConfig,
)
from cricket_trajectory_engine.models.fielder import FIELDER_MOBILITY_PROFILES
from cricket_trajectory_engine.physics.flight_simulator import simulate_flight
from cricket_trajectory_engine.physics.ground_collision import simulate_multi_bounce
from cricket_trajectory_engine.prediction.field_geometry import CricketField
from cricket_trajectory_engine.prediction.outcome_engine import FielderPosition, evaluate_outcome

# Authoritative simulation constants
MASS_KG = 0.160
DIAM_M = 0.0725
RHO = 1.225
GRAVITY = 9.80665
CD = 0.32
E_N = 0.55
MU_T = 0.38
MU_ROLL = 0.20
BOUNDARY_RADIUS = 70.0
RELEASE_POS = [0.0, 0.0, 0.90]
ELEVATION_DEG = 45.0


def run_benchmark_flight(speed_kmh: float, azimuth_deg: float):
    """Executes single flight trajectory matching benchmark conditions."""
    speed_ms = speed_kmh / 3.6
    rad_elev = math.radians(ELEVATION_DEG)
    rad_azim = math.radians(azimuth_deg)

    vx = speed_ms * math.cos(rad_elev) * math.cos(rad_azim)
    vy = speed_ms * math.cos(rad_elev) * math.sin(rad_azim)
    vz = speed_ms * math.sin(rad_elev)

    ball_cfg = BallConfig(mass_kg=MASS_KG, diameter_m=DIAM_M)
    env_cfg = EnvironmentConfig(air_density_kg_m3=RHO, gravity_m_s2=GRAVITY)
    aero_cfg = AerodynamicsConfig(drag_model="constant", constant_cd=CD, enable_magnus=False)
    sim_cfg = SimulationConfig(integration_method="RK45", rtol=1e-8, atol=1e-10, max_step_s=0.005)

    return simulate_flight(
        initial_position_m=RELEASE_POS,
        initial_velocity_m_s=[vx, vy, vz],
        ball_config=ball_cfg,
        env_config=env_cfg,
        aero_config=aero_cfg,
        sim_config=sim_cfg,
        gravity_only=False,
    )


def run_interception_eval(speed_kmh: float, target_name: str, profile_name: str):
    """Runs complete trajectory and evaluates fielder interception."""
    if target_name == "square_leg":
        fx, fy = 3.0, -20.0
        azim = math.degrees(math.atan2(-20.0, 3.0))  # -81.469°
        role = "Square Leg"
    else:
        fx, fy = 10.0, -62.0
        azim = math.degrees(math.atan2(-62.0, 10.0))  # -80.838°
        role = "Deep Square Leg"

    speed_ms = speed_kmh / 3.6
    rad_elev = math.radians(ELEVATION_DEG)
    rad_azim = math.radians(azim)

    v0_vec = np.array([
        speed_ms * math.cos(rad_elev) * math.cos(rad_azim),
        speed_ms * math.cos(rad_elev) * math.sin(rad_azim),
        speed_ms * math.sin(rad_elev),
    ])

    ball_cfg = BallConfig(mass_kg=MASS_KG, diameter_m=DIAM_M)
    env_cfg = EnvironmentConfig(air_density_kg_m3=RHO, gravity_m_s2=GRAVITY)
    aero_cfg = AerodynamicsConfig(drag_model="constant", constant_cd=CD, enable_magnus=False)
    sim_cfg = SimulationConfig(integration_method="RK45", rtol=1e-8, atol=1e-10, max_step_s=0.005)
    collision_cfg = GroundCollisionConfig(
        restitution_normal=E_N,
        friction_tangential=MU_T,
        rolling_resistance_coeff=MU_ROLL,
    )
    field_cfg = FieldConfig(boundary_radius_m=BOUNDARY_RADIUS)

    mb = simulate_multi_bounce(
        initial_position_m=RELEASE_POS,
        initial_velocity_m_s=v0_vec,
        ball_config=ball_cfg,
        env_config=env_cfg,
        aero_config=aero_cfg,
        sim_config=sim_cfg,
        collision_config=collision_cfg,
    )

    prof = FIELDER_MOBILITY_PROFILES[profile_name]
    fielder = FielderPosition(
        fielder_id=f"{target_name}_1",
        role_name=role,
        x_m=fx,
        y_m=fy,
        reach_radius_m=prof["reach_radius_m"],
        max_sprint_speed_m_s=prof["max_sprint_speed_m_s"],
        reaction_time_s=prof["reaction_time_s"],
        min_catch_height_m=prof.get("min_catch_height_m", 0.25),
        max_catch_height_m=prof.get("max_catch_height_m", 2.30),
    )

    outcome = evaluate_outcome(mb, field_config=field_cfg, fielders=[fielder])
    return mb, outcome


class TestAuthoritativeBenchmarkFlightKinematics:
    """Verifies that aerodynamic trajectory flight carry distances match authoritative benchmarks."""

    def test_benchmark_40kmh_carry(self):
        flight = run_benchmark_flight(40.0, -81.47)
        assert abs(flight.horizontal_range_m - 12.77) < 0.10

    def test_benchmark_52kmh_carry(self):
        flight = run_benchmark_flight(52.0, -81.47)
        assert abs(flight.horizontal_range_m - 20.42) < 0.10

    def test_benchmark_60kmh_carry(self):
        flight = run_benchmark_flight(60.0, -81.47)
        assert abs(flight.horizontal_range_m - 26.28) < 0.10

    def test_benchmark_90kmh_carry(self):
        flight = run_benchmark_flight(90.0, -80.84)
        assert abs(flight.horizontal_range_m - 52.06) < 0.15

    def test_benchmark_102kmh_carry(self):
        flight = run_benchmark_flight(102.0, -80.84)
        assert abs(flight.horizontal_range_m - 63.35) < 0.15

    def test_benchmark_114kmh_carry_boundary_six(self):
        flight = run_benchmark_flight(114.0, -80.84)
        assert abs(flight.horizontal_range_m - 74.86) < 0.20
        assert flight.horizontal_range_m >= 70.0  # Clears boundary on full


class TestFielderMobilityProfiles:
    """Verifies profile presets match authoritative specifications."""

    def test_static_profile(self):
        prof = FIELDER_MOBILITY_PROFILES["static"]
        assert prof["max_sprint_speed_m_s"] == 0.0
        assert prof["reach_radius_m"] == 1.80
        assert prof["max_catch_height_m"] == 2.30

    def test_club_profile(self):
        prof = FIELDER_MOBILITY_PROFILES["club"]
        assert prof["max_sprint_speed_m_s"] == 5.0
        assert prof["reach_radius_m"] == 1.50
        assert prof["reaction_time_s"] == 0.45

    def test_elite_profile(self):
        prof = FIELDER_MOBILITY_PROFILES["elite"]
        assert prof["max_sprint_speed_m_s"] == 7.0
        assert prof["reach_radius_m"] == 1.80
        assert prof["reaction_time_s"] == 0.35


class TestSquareLegRegimesAcrossModes:
    """Verifies interception outcomes for Square Leg across Static, Club, and Elite."""

    def test_sl_static_regimes(self):
        # 40 km/h: Falls short
        _, out_40 = run_interception_eval(40.0, "square_leg", "static")
        eval_40 = out_40.fielder_evaluations[0]
        assert not eval_40.can_intercept_for_catch

        # 52 km/h: Direct catch in hands
        _, out_52 = run_interception_eval(52.0, "square_leg", "static")
        eval_52 = out_52.fielder_evaluations[0]
        assert eval_52.can_intercept_for_catch
        assert eval_52.required_sprint_speed_m_s is not None
        assert eval_52.required_sprint_speed_m_s <= 0.10

        # 60 km/h: Overhead clearance (unintercepted)
        _, out_60 = run_interception_eval(60.0, "square_leg", "static")
        eval_60 = out_60.fielder_evaluations[0]
        assert not eval_60.can_intercept_for_catch

    def test_sl_club_regimes(self):
        # 40 km/h: Falls short (beyond 5 m/s sprint)
        _, out_40 = run_interception_eval(40.0, "square_leg", "club")
        assert not out_40.fielder_evaluations[0].can_intercept_for_catch

        # 48 km/h: Intercepted via sprint
        _, out_48 = run_interception_eval(48.0, "square_leg", "club")
        eval_48 = out_48.fielder_evaluations[0]
        assert eval_48.can_intercept_for_catch
        assert eval_48.required_sprint_speed_m_s <= 5.0

        # 52 km/h: Direct catch
        _, out_52 = run_interception_eval(52.0, "square_leg", "club")
        assert out_52.fielder_evaluations[0].can_intercept_for_catch

    def test_sl_elite_regimes(self):
        # 40 km/h: Diving catch (requires ~6.8 m/s, within 7.0 m/s limit)
        _, out_40 = run_interception_eval(40.0, "square_leg", "elite")
        eval_40 = out_40.fielder_evaluations[0]
        assert eval_40.can_intercept_for_catch

        # 52 km/h: Direct catch
        _, out_52 = run_interception_eval(52.0, "square_leg", "elite")
        assert out_52.fielder_evaluations[0].can_intercept_for_catch

        # 60 km/h: Sprint catch (fielder runs back, time allowed = 2.44 s)
        _, out_60 = run_interception_eval(60.0, "square_leg", "elite")
        assert out_60.fielder_evaluations[0].can_intercept_for_catch


class TestDeepSquareLegRegimesAcrossModes:
    """Verifies interception outcomes for Deep Square Leg across Static, Club, and Elite."""

    def test_dsl_static_regimes(self):
        # 90 km/h: Falls short (~52 m carry vs 62.8 m distance)
        _, out_90 = run_interception_eval(90.0, "deep_square_leg", "static")
        eval_90 = out_90.fielder_evaluations[0]
        assert not eval_90.can_intercept_for_catch

        # 102 km/h: Direct catch in hands (carry 63.35 m, lands within 0.55 m of fielder)
        _, out_102 = run_interception_eval(102.0, "deep_square_leg", "static")
        eval_102 = out_102.fielder_evaluations[0]
        assert eval_102.can_intercept_for_catch

        # 114 km/h: Boundary six (carry 74.86 m > 70.0 m)
        mb_114, out_114 = run_interception_eval(114.0, "deep_square_leg", "static")
        assert out_114.primary_call == "SIX"
        assert out_114.geometry_facts["crossed_boundary_on_full"] is True
        carry_dist = np.hypot(mb_114.first_bounce.position_m[0], mb_114.first_bounce.position_m[1])
        assert carry_dist >= 70.0

    def test_dsl_club_regimes(self):
        # 90 km/h: Sprint catch (flight time ~3.47 s gives ample time to cover 12.6 m)
        _, out_90 = run_interception_eval(90.0, "deep_square_leg", "club")
        assert out_90.fielder_evaluations[0].can_intercept_for_catch

        # 102 km/h: Direct catch
        _, out_102 = run_interception_eval(102.0, "deep_square_leg", "club")
        assert out_102.fielder_evaluations[0].can_intercept_for_catch

    def test_dsl_elite_regimes(self):
        # 80 km/h: Diving catch (carry 42.9 m, dist to fielder ~19.9 m, flight time 3.12 s)
        _, out_80 = run_interception_eval(80.0, "deep_square_leg", "elite")
        assert out_80.fielder_evaluations[0].can_intercept_for_catch

        # 90 km/h: Sprint catch
        _, out_90 = run_interception_eval(90.0, "deep_square_leg", "elite")
        assert out_90.fielder_evaluations[0].can_intercept_for_catch

        # 102 km/h: Direct catch
        _, out_102 = run_interception_eval(102.0, "deep_square_leg", "elite")
        assert out_102.fielder_evaluations[0].can_intercept_for_catch
