"""
Unit tests for coordinate loading, state estimation, and trajectory fitting.
"""

import pytest
import numpy as np

from cricket_trajectory_engine.config.physics_config import (
    BallConfig,
    EnvironmentConfig,
    AerodynamicsConfig,
)
from cricket_trajectory_engine.physics.flight_simulator import simulate_flight
from cricket_trajectory_engine.estimation.coordinate_loader import (
    ObservationSet,
    load_observations_from_csv,
    validate_observations,
    generate_synthetic_observations,
)
from cricket_trajectory_engine.estimation.velocity_estimator import (
    estimate_initial_state,
    compute_launch_angles,
)
from cricket_trajectory_engine.estimation.trajectory_fitting import (
    fit_trajectory_to_observations,
)


class TestCoordinateLoader:
    """Tests loading and validation of 3D ball coordinates."""

    def test_validation_rejects_non_monotonic_times(self):
        times = [0.0, 0.033, 0.030, 0.067]
        pos = [[0, 0, 1], [1, 0, 1.2], [2, 0, 1.4], [3, 0, 1.6]]
        with pytest.raises(ValueError, match="strictly increasing"):
            validate_observations(times, pos)

    def test_validation_rejects_negative_height(self):
        times = [0.0, 0.033, 0.067]
        pos = [[0, 0, 1.0], [1, 0, -0.2], [2, 0, 1.4]]
        with pytest.raises(ValueError, match="cannot be negative"):
            validate_observations(times, pos)

    def test_load_dummy_observations_csv(self):
        csv_path = "cricket_trajectory_engine/data/dummy_observations.csv"
        obs = load_observations_from_csv(csv_path)
        assert obs.count == 5
        assert np.isclose(obs.times_s[0], 0.0)
        assert np.isclose(obs.times_s[-1], 0.133)
        assert obs.positions_m.shape == (5, 3)


class TestVelocityEstimator:
    """Tests kinematic estimation from coordinate observations."""

    def test_exact_recovery_on_noiseless_synthetic_flight(self):
        ball = BallConfig()
        env = EnvironmentConfig()
        aero = AerodynamicsConfig(constant_cd=0.32)

        v_true = np.array([28.5, 3.2, 14.8])
        p_true = np.array([0.0, 0.0, 1.2])

        flight = simulate_flight(p_true, v_true, ball, env, aero)
        obs = generate_synthetic_observations(
            flight, start_time_s=0.0, end_time_s=0.15, fps=50.0, noise_std_m=0.0
        )

        est = estimate_initial_state(obs, method="polynomial", polynomial_order=2)

        # Velocity recovered within < 0.2 m/s:
        assert np.allclose(est.initial_velocity_m_s, v_true, atol=0.20)
        assert np.isclose(est.initial_speed_m_s, np.linalg.norm(v_true), atol=0.20)

    def test_noise_smoothing_polynomial_vs_finite_difference(self):
        ball = BallConfig()
        env = EnvironmentConfig()
        aero = AerodynamicsConfig()

        v_true = np.array([25.0, 0.0, 12.0])
        p_true = np.array([0.0, 0.0, 1.0])

        flight = simulate_flight(p_true, v_true, ball, env, aero)
        # 10 frames with 2 cm random noise:
        obs_noisy = generate_synthetic_observations(
            flight, start_time_s=0.0, end_time_s=0.20, fps=50.0, noise_std_m=0.02, random_seed=123
        )

        est_poly = estimate_initial_state(obs_noisy, method="polynomial", polynomial_order=2)
        est_fd = estimate_initial_state(obs_noisy, method="finite_difference")

        # Polynomial fit should have smaller error from true velocity than raw 2-point difference:
        err_poly = np.linalg.norm(est_poly.initial_velocity_m_s - v_true)
        err_fd = np.linalg.norm(est_fd.initial_velocity_m_s - v_true)
        assert err_poly < err_fd


class TestTrajectoryFitting:
    """Tests least-squares optimization against observed points."""

    def test_velocity_only_fitting_recovers_known_trajectory(self):
        ball = BallConfig()
        env = EnvironmentConfig()
        aero = AerodynamicsConfig(constant_cd=0.32)

        v_true = np.array([26.0, 1.5, 13.0])
        p_true = np.array([0.0, 0.0, 1.0])

        flight = simulate_flight(p_true, v_true, ball, env, aero)
        obs = generate_synthetic_observations(flight, start_time_s=0.0, end_time_s=0.15, fps=30.0)

        fit_res = fit_trajectory_to_observations(obs, ball, env, aero, fit_drag_coefficient=False)

        assert fit_res.convergence_success is True
        assert fit_res.total_rmse_m < 0.005  # sub-centimeter fit RMSE
        assert np.allclose(fit_res.optimized_velocity_m_s, v_true, atol=0.10)

    def test_identifiability_warning_on_short_window_with_drag(self):
        ball = BallConfig()
        env = EnvironmentConfig()
        aero = AerodynamicsConfig(constant_cd=0.32)

        v_true = np.array([26.0, 0.0, 13.0])
        p_true = np.array([0.0, 0.0, 1.0])

        flight = simulate_flight(p_true, v_true, ball, env, aero)
        obs = generate_synthetic_observations(flight, start_time_s=0.0, end_time_s=0.10, fps=30.0)

        fit_res = fit_trajectory_to_observations(obs, ball, env, aero, fit_drag_coefficient=True)

        assert fit_res.parameter_identifiability_warning is not None
        assert "OBSERVATION WINDOW TOO SHORT" in fit_res.parameter_identifiability_warning

