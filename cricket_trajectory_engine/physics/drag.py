"""
Aerodynamic drag force and Reynolds-number-dependent drag models for cricket balls.

References:
- C. J. Baker (2010), "A Calculation of Cricket Ball Trajectories", Proc. IMechE Part C.
- S. D. Grimshaw, A. Briggs, & N. R. Atkins (2024), "A review and reassessment of the
  aerodynamics of cricket ball swing", Flow, Cambridge University Press.
"""

from typing import Tuple
import numpy as np

from cricket_trajectory_engine.config.physics_config import (
    BallConfig,
    EnvironmentConfig,
    AerodynamicsConfig,
)


def compute_relative_velocity(velocity: np.ndarray, wind_vector: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Computes ball velocity relative to the surrounding air:
        v_rel = v - w
    Returns (v_rel, |v_rel|).
    """
    v_rel = np.asarray(velocity, dtype=float) - np.asarray(wind_vector, dtype=float)
    speed_rel = float(np.linalg.norm(v_rel))
    return v_rel, speed_rel


def compute_reynolds_number(
    speed_rel: float,
    ball_config: BallConfig,
    env_config: EnvironmentConfig,
) -> float:
    """
    Computes Reynolds number:
        Re = (rho * |v_rel| * D) / mu
    
    For a cricket ball of D = 0.0725 m in standard air (rho = 1.225 kg/m^3, mu = 1.81e-5 Pa*s):
        Re ~ 4906 * |v_rel|
    At 30 m/s (108 km/h): Re ~ 1.47e5.
    At 40 m/s (144 km/h): Re ~ 1.96e5.
    """
    if speed_rel <= 1e-12:
        return 0.0
    return (env_config.air_density_kg_m3 * speed_rel * ball_config.diameter_m) / env_config.dynamic_viscosity_pa_s


def evaluate_drag_coefficient(
    speed_rel: float,
    ball_config: BallConfig,
    env_config: EnvironmentConfig,
    aero_config: AerodynamicsConfig,
) -> float:
    """
    Evaluates the drag coefficient Cd.
    
    Modes:
    1. 'constant': returns aero_config.constant_cd (default: 0.32, Baker 2010).
    2. 'reynolds_dependent':
       In the subcritical regime (Re < 1e5), Cd is roughly 0.32 - 0.35.
       In the critical transition (Re ~ 1.2e5 to 2.2e5), boundary layer transition
       on the seam drops Cd to ~0.20 - 0.22.
       
       Note on scientific validity (Grimshaw et al. 2024):
       The precise Re transition point depends critically on seam angle to flow,
       stitch count, and ball wear. This parameterized curve provides a continuous
       logistic model for research testing, but must be calibrated against wind-tunnel
       or tracking data before drawing definitive conclusions about boundary-layer tripping.
    """
    if aero_config.drag_model == "constant":
        return aero_config.constant_cd

    re = compute_reynolds_number(speed_rel, ball_config, env_config)
    if re <= 1e-6:
        return aero_config.constant_cd

    # Parameterized smooth logistic transition curve:
    cd_subcritical = aero_config.constant_cd  # e.g., 0.32
    cd_supercritical = 0.20
    re_crit = 1.6e5
    re_width = 3.0e4

    # Logistic blending:
    factor = 1.0 / (1.0 + np.exp(-(re - re_crit) / re_width))
    cd = cd_subcritical + (cd_supercritical - cd_subcritical) * factor
    return float(cd)


def compute_drag_force(
    velocity: np.ndarray,
    ball_config: BallConfig,
    env_config: EnvironmentConfig,
    aero_config: AerodynamicsConfig,
) -> np.ndarray:
    """
    Computes the quadratic aerodynamic drag force vector:
        F_drag = -0.5 * rho * Cd * A * |v_rel| * v_rel
    Opposing the relative airflow.
    """
    v_rel, speed_rel = compute_relative_velocity(velocity, np.asarray(env_config.wind_vector_m_s))
    if speed_rel < 1e-9:
        return np.zeros(3, dtype=float)

    cd = evaluate_drag_coefficient(speed_rel, ball_config, env_config, aero_config)
    rho = env_config.air_density_kg_m3
    area = ball_config.cross_sectional_area_m2

    force = -0.5 * rho * cd * area * speed_rel * v_rel
    return force

