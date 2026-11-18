"""
Unit tests for field geometry, boundary crossing, catch interception, outcome logic, and Monte Carlo.
"""

import pytest
import numpy as np

from cricket_trajectory_engine.config.physics_config import FieldConfig
from cricket_trajectory_engine.physics.ground_collision import simulate_multi_bounce
from cricket_trajectory_engine.prediction.field_geometry import CricketField
from cricket_trajectory_engine.prediction.outcome_engine import (
    evaluate_outcome,
    FielderPosition,
    evaluate_fielders_for_catch,
)
from cricket_trajectory_engine.prediction.uncertainty import (
    MonteCarloConfig,
    run_monte_carlo_simulation,
)


class TestFieldGeometry:
    """Tests boundary calculations and crossing detection."""

    def test_circular_and_elliptical_radii(self):
        circular_field = CricketField(FieldConfig(boundary_radius_m=65.0))
        assert circular_field.boundary_radius_at_azimuth(0.0) == 65.0
        assert circular_field.boundary_radius_at_azimuth(np.pi / 2) == 65.0

        elliptical_field = CricketField(FieldConfig(semi_major_m=75.0, semi_minor_m=60.0))
        assert np.isclose(elliptical_field.boundary_radius_at_azimuth(0.0), 75.0)
        assert np.isclose(elliptical_field.boundary_radius_at_azimuth(np.pi / 2), 60.0)


class TestOutcomeEngine:
    """Tests Six, Four, Catch, and In-Play outcome logic."""

    def test_six_outcome(self):
        # High power lofted shot: 38 m/s at 35 deg (~85 m carry)
        v0 = np.array([34.0, 0.0, 20.0])
        p0 = np.array([0.0, 0.0, 1.2])

        res = simulate_multi_bounce(p0, v0)
        outcome = evaluate_outcome(res, FieldConfig(boundary_radius_m=70.0))

        assert outcome.primary_call == "SIX"
        assert outcome.geometry_facts["crossed_boundary_on_full"] is True
        assert outcome.estimated_runs == 6

    def test_four_outcome(self):
        # Hard ground shot: fast, bounces at 35m, rolls past 70m
        v0 = np.array([32.0, 0.0, 6.0])
        p0 = np.array([0.0, 0.0, 0.8])

        res = simulate_multi_bounce(p0, v0)
        outcome = evaluate_outcome(res, FieldConfig(boundary_radius_m=70.0))

        assert outcome.primary_call == "FOUR"
        assert outcome.geometry_facts["first_impact_inside_boundary"] is True
        assert outcome.geometry_facts["crossed_boundary"] is True
        assert outcome.geometry_facts["crossed_boundary_on_full"] is False
        assert outcome.estimated_runs == 4

    def test_catch_evaluation_with_fielders(self):
        # Lofted shot landing around X = 45m, Y = 0m after ~3.0s flight
        v0 = np.array([24.0, 0.0, 15.0])
        p0 = np.array([0.0, 0.0, 1.0])
        res = simulate_multi_bounce(p0, v0)

        # Fielder 1 (Mid-on): close enough to intercept (at X=42m, Y=2m)
        f_close = FielderPosition(
            fielder_id="f1",
            role_name="Long-On",
            x_m=43.0,
            y_m=1.0,
            max_sprint_speed_m_s=7.0,
        )
        # Fielder 2 (Deep Cover): far away on opposite side
        f_far = FielderPosition(
            fielder_id="f2",
            role_name="Deep Cover",
            x_m=10.0,
            y_m=-45.0,
        )

        outcome = evaluate_outcome(res, FieldConfig(boundary_radius_m=75.0), fielders=[f_close, f_far])
        assert outcome.primary_call == "POTENTIAL_CATCH"

        eval_close = next(e for e in outcome.fielder_evaluations if e.fielder_id == "f1")
        eval_far = next(e for e in outcome.fielder_evaluations if e.fielder_id == "f2")
        assert eval_close.can_intercept_for_catch is True
        assert eval_far.can_intercept_for_catch is False

    def test_missing_fielder_data_flag(self):
        # In-field shot with no fielders provided
        v0 = np.array([15.0, 0.0, 8.0])
        p0 = np.array([0.0, 0.0, 1.0])
        res = simulate_multi_bounce(p0, v0)

        outcome = evaluate_outcome(res, FieldConfig(boundary_radius_m=70.0), fielders=None)
        assert outcome.player_data_missing is True
        assert outcome.primary_call == "IN_PLAY_FIELDER_DATA_REQUIRED"
        assert outcome.estimated_runs is None


class TestMonteCarloSimulation:
    """Tests Monte Carlo reproducibility and statistics."""

    def test_monte_carlo_reproducibility(self):
        p0 = np.array([0.0, 0.0, 1.0])
        v0 = np.array([26.0, 2.0, 14.0])

        mc_cfg = MonteCarloConfig(n_simulations=15, random_seed=42)
        mc1 = run_monte_carlo_simulation(p0, v0, mc_config=mc_cfg)
        mc2 = run_monte_carlo_simulation(p0, v0, mc_config=mc_cfg)

        assert np.isclose(mc1.landing_x_stats_m["mean"], mc2.landing_x_stats_m["mean"])
        assert np.isclose(mc1.probability_six, mc2.probability_six)
        assert 0.0 <= mc1.probability_six <= 1.0
        assert 0.0 <= mc1.probability_four <= 1.0
        assert 0.0 <= mc1.probability_in_field <= 1.0

