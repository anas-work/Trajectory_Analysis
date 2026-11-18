"""
Rigorous Elevation Sweep Benchmark Tests at Fixed 120.0 km/h Launch Speed.

Validates:
1. Aerodynamic ballistic properties at 120 km/h across elevation range [0.5, 89.5] deg.
2. The Six Boundary window (carry >= 70.0 m) between 25.80 deg and 58.65 deg.
3. Square Leg fielder interception regimes across Static, Club, and Elite profiles.
4. Deep Square Leg fielder interception regimes across Static, Club, and Elite profiles.
5. Dual-angle catch windows (low-elevation bullet drives vs high-elevation towering skiers).
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

# Authoritative Constants
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
FIXED_SPEED_KMH = 120.0
FIXED_SPEED_MS = FIXED_SPEED_KMH / 3.6  # 33.3333 m/s

# Target Fielder Coordinates & Azimuths
SQ_LEG_AZIMUTH = math.degrees(math.atan2(-20.0, 3.0))   # -81.4692 deg
DEEP_SQ_LEG_AZIMUTH = math.degrees(math.atan2(-62.0, 10.0))  # -80.8377 deg


def run_elevation_flight(elevation_deg: float, azimuth_deg: float):
    """Executes single flight trajectory at 120 km/h for given elevation and azimuth."""
    rad_elev = math.radians(elevation_deg)
    rad_azim = math.radians(azimuth_deg)

    vx = FIXED_SPEED_MS * math.cos(rad_elev) * math.cos(rad_azim)
    vy = FIXED_SPEED_MS * math.cos(rad_elev) * math.sin(rad_azim)
    vz = FIXED_SPEED_MS * math.sin(rad_elev)

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


def run_elevation_interception_eval(elevation_deg: float, target_name: str, profile_name: str):
    """Runs complete multi-bounce trajectory and evaluates fielder interception."""
    if target_name == "square_leg":
        fx, fy = 3.0, -20.0
        azim = SQ_LEG_AZIMUTH
        role = "Square Leg"
    else:
        fx, fy = 10.0, -62.0
        azim = DEEP_SQ_LEG_AZIMUTH
        role = "Deep Square Leg"

    rad_elev = math.radians(elevation_deg)
    rad_azim = math.radians(azim)

    v0_vec = np.array([
        FIXED_SPEED_MS * math.cos(rad_elev) * math.cos(rad_azim),
        FIXED_SPEED_MS * math.cos(rad_elev) * math.sin(rad_azim),
        FIXED_SPEED_MS * math.sin(rad_elev),
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


class TestBallistics120Kmh:
    """Verifies aerodynamic flight curves and boundary limits at fixed 120 km/h."""

    def test_peak_carry_angle(self):
        """Carry distance should peak near 40 deg elevation at ~80.8m with drag."""
        res_35 = run_elevation_flight(35.0, SQ_LEG_AZIMUTH)
        res_40 = run_elevation_flight(40.0, SQ_LEG_AZIMUTH)
        res_45 = run_elevation_flight(45.0, SQ_LEG_AZIMUTH)

        assert res_40.horizontal_range_m > res_35.horizontal_range_m
        assert res_40.horizontal_range_m > res_45.horizontal_range_m
        assert 80.0 <= res_40.horizontal_range_m <= 81.5

    def test_six_boundary_window(self):
        """Boundary six (carry >= 70m) occurs between 25.80 deg and 58.65 deg."""
        # 25 deg should fall just short of boundary full-pitch (approx 68.5m)
        res_25 = run_elevation_flight(25.0, SQ_LEG_AZIMUTH)
        assert res_25.horizontal_range_m < 70.0

        # 30 deg and 50 deg must clear 70m rope on full
        res_30 = run_elevation_flight(30.0, SQ_LEG_AZIMUTH)
        res_50 = run_elevation_flight(50.0, SQ_LEG_AZIMUTH)
        assert res_30.horizontal_range_m > 70.0
        assert res_50.horizontal_range_m > 70.0

        # 60 deg drops back inside boundary (< 70m)
        res_60 = run_elevation_flight(60.0, SQ_LEG_AZIMUTH)
        assert res_60.horizontal_range_m < 70.0

    def test_steep_skier_kinematics(self):
        """Steep elevation (> 80 deg) has extreme hang time (> 5.5s) and low carry."""
        res_82 = run_elevation_flight(82.0, SQ_LEG_AZIMUTH)
        assert res_82.horizontal_range_m < 25.0
        assert res_82.flight_time_s > 5.5
        assert res_82.max_height_m > 40.0


class TestSquareLegElevationInterceptions:
    """Verifies Square Leg (20.22 m) outcomes across Static, Club, and Elite modes."""

    def test_static_square_leg_regimes(self):
        """Static fielder at Square Leg has two catch windows: low drive and high skied."""
        # 1.5 deg: Falls well short of fielder (carry ~16.5m), fielded cleanly on ground (Dot ball, 0 runs, boundary prevented)
        mb_1_5, out_1_5 = run_elevation_interception_eval(1.5, "square_leg", "static")
        eval_1_5 = out_1_5.fielder_evaluations[0]
        assert not eval_1_5.can_intercept_for_catch
        carry_1_5 = np.hypot(mb_1_5.first_bounce.position_m[0], mb_1_5.first_bounce.position_m[1])
        assert carry_1_5 < 19.0
        assert out_1_5.primary_call == "DOT"
        assert out_1_5.estimated_runs == 0
        assert out_1_5.rope_clearance.clears_rope is False

        # 5.0 deg: Low bullet drive caught direct in hands
        _, out_5_0 = run_elevation_interception_eval(5.0, "square_leg", "static")
        eval_5_0 = out_5_0.fielder_evaluations[0]
        assert eval_5_0.can_intercept_for_catch

        # 15.0 deg: Clears fielder overhead and runs to boundary Four
        _, out_15 = run_elevation_interception_eval(15.0, "square_leg", "static")
        assert not out_15.fielder_evaluations[0].can_intercept_for_catch
        assert out_15.primary_call == "FOUR"

        # 40.0 deg: Clears boundary 70m on full for Six
        _, out_40 = run_elevation_interception_eval(40.0, "square_leg", "static")
        assert out_40.primary_call == "SIX"

        # 70.0 deg: Lands beyond fielder (~50m carry) in outfield
        _, out_70 = run_elevation_interception_eval(70.0, "square_leg", "static")
        assert not out_70.fielder_evaluations[0].can_intercept_for_catch

        # 82.2 deg: High skied ball caught stationary near starting position
        _, out_82_2 = run_elevation_interception_eval(82.2, "square_leg", "static")
        assert out_82_2.fielder_evaluations[0].can_intercept_for_catch

        # 86.0 deg: Skied ball falls short of fielder (< 15m)
        _, out_86 = run_elevation_interception_eval(86.0, "square_leg", "static")
        assert not out_86.fielder_evaluations[0].can_intercept_for_catch

    def test_mobile_square_leg_skier_interception(self):
        """Club and Elite fielders can run 20-30m under high skiers due to 6s hang time."""
        # 85.0 deg lands at carry ~11m (9m in front of fielder).
        # Static cannot reach it, but Club (5m/s) and Elite (7m/s) easily catch it!
        _, out_static = run_elevation_interception_eval(85.0, "square_leg", "static")
        assert not out_static.fielder_evaluations[0].can_intercept_for_catch

        _, out_club = run_elevation_interception_eval(85.0, "square_leg", "club")
        assert out_club.fielder_evaluations[0].can_intercept_for_catch

        _, out_elite = run_elevation_interception_eval(85.0, "square_leg", "elite")
        assert out_elite.fielder_evaluations[0].can_intercept_for_catch


class TestDeepSquareLegElevationInterceptions:
    """Verifies Deep Square Leg (62.80 m) outcomes across Static, Club, and Elite modes."""

    def test_static_deep_square_leg_regimes(self):
        """Static fielder at Deep Square Leg catching envelope."""
        # 10.0 deg: Falls well short (carry ~38m)
        mb_10, out_10 = run_elevation_interception_eval(10.0, "deep_square_leg", "static")
        assert not out_10.fielder_evaluations[0].can_intercept_for_catch
        carry_10 = np.hypot(mb_10.first_bounce.position_m[0], mb_10.first_bounce.position_m[1])
        assert carry_10 < 50.0

        # 21.5 deg: In-hands catch near 63m carry
        _, out_21_5 = run_elevation_interception_eval(21.5, "deep_square_leg", "static")
        assert out_21_5.fielder_evaluations[0].can_intercept_for_catch

        # 30.0 deg: Six over rope
        _, out_30 = run_elevation_interception_eval(30.0, "deep_square_leg", "static")
        assert out_30.primary_call == "SIX"

        # 63.0 deg: Skied catch descending right at deep boundary
        _, out_63 = run_elevation_interception_eval(63.0, "deep_square_leg", "static")
        assert out_63.fielder_evaluations[0].can_intercept_for_catch

        # 75.0 deg: Skied ball falls way short (carry ~40m)
        _, out_75 = run_elevation_interception_eval(75.0, "deep_square_leg", "static")
        assert not out_75.fielder_evaluations[0].can_intercept_for_catch

    def test_mobile_deep_square_leg_interception(self):
        """Elite and Club expand catching range significantly in outfield."""
        # 17.0 deg: Carry ~54.9m. Falls 7.9m short of fielder.
        # Static cannot reach it. Elite diving catch reaches it!
        _, out_static = run_elevation_interception_eval(17.0, "deep_square_leg", "static")
        assert not out_static.fielder_evaluations[0].can_intercept_for_catch

        _, out_elite = run_elevation_interception_eval(17.0, "deep_square_leg", "elite")
        assert out_elite.fielder_evaluations[0].can_intercept_for_catch

        # 70.0 deg: Skied ball landing at carry ~49.8m (13m in front of fielder).
        # Elite charging in can catch it!
        _, out_elite_70 = run_elevation_interception_eval(70.0, "deep_square_leg", "elite")
        assert out_elite_70.fielder_evaluations[0].can_intercept_for_catch