"""
Physics-based trajectory fitting against observed 3D coordinate sequences.

Optimizes initial velocity and/or aerodynamic parameters to minimize position RMSE.
Includes rigorous identifiability diagnostics for short observation windows.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import numpy as np
from scipy.optimize import least_squares

from cricket_trajectory_engine.config.physics_config import (
    BallConfig,
    EnvironmentConfig,
    AerodynamicsConfig,
    SimulationConfig,
)
from cricket_trajectory_engine.physics.flight_simulator import simulate_flight
from cricket_trajectory_engine.estimation.coordinate_loader import ObservationSet
from cricket_trajectory_engine.estimation.velocity_estimator import (
    estimate_initial_state,
    compute_launch_angles,
)


@dataclass
class TrajectoryFitResult:
    """Results from optimizing physics simulation against observed points."""
    optimized_velocity_m_s: np.ndarray
    optimized_speed_m_s: float
    elevation_angle_deg: float
    azimuth_angle_deg: float
    optimized_cd: float
    total_rmse_m: float
    per_axis_rmse_m: Dict[str, float]
    residuals_m: np.ndarray
    convergence_success: bool
    status_message: str
    function_evaluations: int
    parameter_identifiability_warning: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "optimized_velocity_m_s": self.optimized_velocity_m_s.tolist(),
            "optimized_speed_m_s": self.optimized_speed_m_s,
            "elevation_angle_deg": self.elevation_angle_deg,
            "azimuth_angle_deg": self.azimuth_angle_deg,
            "optimized_cd": self.optimized_cd,
            "total_rmse_m": self.total_rmse_m,
            "per_axis_rmse_m": self.per_axis_rmse_m,
            "convergence_success": self.convergence_success,
            "status_message": self.status_message,
            "function_evaluations": self.function_evaluations,
            "parameter_identifiability_warning": self.parameter_identifiability_warning,
        }


def fit_trajectory_to_observations(
    observations: ObservationSet,
    ball_config: Optional[BallConfig] = None,
    env_config: Optional[EnvironmentConfig] = None,
    aero_config: Optional[AerodynamicsConfig] = None,
    sim_config: Optional[SimulationConfig] = None,
    fit_drag_coefficient: bool = False,
) -> TrajectoryFitResult:
    """
    Fits physics model initial conditions to observed 3D coordinates.
    
    Parameters:
        observations: ObservationSet with timestamps and 3D positions.
        fit_drag_coefficient: If False (recommended for short windows), fits only [Vx0, Vy0, Vz0].
                              If True, jointly estimates [Vx0, Vy0, Vz0, Cd].
    """
    ball = ball_config or BallConfig()
    env = env_config or EnvironmentConfig()
    aero = aero_config or AerodynamicsConfig()
    sim = sim_config or SimulationConfig()

    times = observations.times_s
    t_eval = times - times[0]
    target_pos = observations.positions_m
    initial_pos = target_pos[0]

    # Initial guess from polynomial regression:
    poly_est = estimate_initial_state(observations, method="polynomial")
    v_guess = poly_est.initial_velocity_m_s.copy()

    # Identifiability warning check:
    identifiability_warning = None
    if observations.duration_s < 0.35 and fit_drag_coefficient:
        identifiability_warning = (
            f"OBSERVATION WINDOW TOO SHORT ({observations.duration_s:.3f} s < 0.35 s): "
            "Drag coefficient Cd is weakly identifiable over short post-shot windows because "
            "gravitational acceleration dominates the vertical axis while drag deceleration "
            "over a few frames is small compared to tracking noise. Jointly fitting Cd may yield "
            "unphysically high or low values. Velocity-only fitting is recommended."
        )

    if not fit_drag_coefficient:
        # Parameter vector: [Vx, Vy, Vz]
        x0 = v_guess
        # Bounds: plausible cricket velocities [-100, 100] m/s
        bounds = ([-100.0, -100.0, -100.0], [100.0, 100.0, 100.0])

        def residual_fn(params):
            v_curr = params[:3]
            try:
                sim_res = simulate_flight(
                    initial_position_m=initial_pos,
                    initial_velocity_m_s=v_curr,
                    ball_config=ball,
                    env_config=env,
                    aero_config=aero,
                    sim_config=sim,
                    t_eval=t_eval,
                    stop_at_ground=False,
                )
                if len(sim_res.time_s) != len(t_eval):
                    return np.full(len(t_eval) * 3, 1e4)
                diff = sim_res.positions_m - target_pos
                return diff.flatten()
            except Exception:
                return np.full(len(t_eval) * 3, 1e4)

    else:
        # Parameter vector: [Vx, Vy, Vz, Cd]
        x0 = np.concatenate((v_guess, [aero.constant_cd]))
        bounds = ([-100.0, -100.0, -100.0, 0.10], [100.0, 100.0, 100.0, 0.70])

        def residual_fn(params):
            v_curr = params[:3]
            cd_curr = float(params[3])
            aero_temp = AerodynamicsConfig(
                drag_model="constant",
                constant_cd=cd_curr,
                enable_magnus=aero.enable_magnus,
                spin_rad_s=aero.spin_rad_s,
            )
            try:
                sim_res = simulate_flight(
                    initial_position_m=initial_pos,
                    initial_velocity_m_s=v_curr,
                    ball_config=ball,
                    env_config=env,
                    aero_config=aero_temp,
                    sim_config=sim,
                    t_eval=t_eval,
                    stop_at_ground=False,
                )
                if len(sim_res.time_s) != len(t_eval):
                    return np.full(len(t_eval) * 3, 1e4)
                diff = sim_res.positions_m - target_pos
                return diff.flatten()
            except Exception:
                return np.full(len(t_eval) * 3, 1e4)

    opt = least_squares(
        residual_fn,
        x0=x0,
        bounds=bounds,
        method="trf",
        ftol=1e-8,
        xtol=1e-8,
        gtol=1e-8,
        max_nfev=300,
    )

    opt_v = opt.x[:3]
    opt_cd = float(opt.x[3]) if fit_drag_coefficient else aero.constant_cd

    # Compute final residuals with optimized parameters:
    aero_final = AerodynamicsConfig(
        drag_model="constant",
        constant_cd=opt_cd,
        enable_magnus=aero.enable_magnus,
        spin_rad_s=aero.spin_rad_s,
    )
    final_sim = simulate_flight(
        initial_position_m=initial_pos,
        initial_velocity_m_s=opt_v,
        ball_config=ball,
        env_config=env,
        aero_config=aero_final,
        sim_config=sim,
        t_eval=t_eval,
        stop_at_ground=False,
    )
    diff_final = final_sim.positions_m - target_pos
    rmse_x = float(np.sqrt(np.mean(diff_final[:, 0] ** 2)))
    rmse_y = float(np.sqrt(np.mean(diff_final[:, 1] ** 2)))
    rmse_z = float(np.sqrt(np.mean(diff_final[:, 2] ** 2)))
    total_rmse = float(np.sqrt(np.mean(diff_final ** 2)))

    speed, elev, azim = compute_launch_angles(opt_v)

    return TrajectoryFitResult(
        optimized_velocity_m_s=opt_v,
        optimized_speed_m_s=speed,
        elevation_angle_deg=elev,
        azimuth_angle_deg=azim,
        optimized_cd=opt_cd,
        total_rmse_m=total_rmse,
        per_axis_rmse_m={"x": rmse_x, "y": rmse_y, "z": rmse_z},
        residuals_m=diff_final,
        convergence_success=bool(opt.success),
        status_message=str(opt.message),
        function_evaluations=int(opt.nfev),
        parameter_identifiability_warning=identifiability_warning,
    )

