"""
Magnus force implementation for spinning cricket balls.

References:
- C. J. Baker (2013), "A unified framework for the prediction of cricket ball trajectories
  in spin and swing bowling", Proc. IMechE Part P: J. Sports Eng. & Tech., 227(3):197-209.
- Bearman, P. W., & Harvey, J. K. (1976), "Golf ball aerodynamics", Aeronautical Quarterly.
"""

from typing import Tuple
import numpy as np

from cricket_trajectory_engine.config.physics_config import (
    BallConfig,
    EnvironmentConfig,
    AerodynamicsConfig,
)
from cricket_trajectory_engine.physics.drag import compute_relative_velocity


def compute_spin_parameter(
    spin_rad_s: np.ndarray,
    speed_rel: float,
    ball_config: BallConfig,
) -> Tuple[float, float]:
    """
    Computes spin rate (omega) in rad/s and non-dimensional spin parameter:
        S_p = (omega * r) / |v_rel|
    Returns (spin_norm, S_p).
    """
    spin_norm = float(np.linalg.norm(spin_rad_s))
    if speed_rel < 1e-9 or spin_norm < 1e-9:
        return spin_norm, 0.0
    sp = (spin_norm * ball_config.radius_m) / speed_rel
    return spin_norm, float(sp)


def evaluate_lift_coefficient(
    spin_parameter: float,
    aero_config: AerodynamicsConfig,
) -> float:
    """
    Evaluates the Magnus lift coefficient C_L.
    
    Modes:
    1. 'constant_cl': Returns fixed C_L from config (default: 0.15).
    2. 'spin_parameter': Baker (2013) models lift as approximately proportional
       to non-dimensional spin ratio S_p before saturating at high spin:
           C_L = min(0.35, 1.2 * S_p)
    """
    if aero_config.magnus_model == "constant_cl":
        return aero_config.constant_cl
    
    # Linear regime up to saturation:
    cl = min(0.35, 1.2 * spin_parameter)
    return float(cl)


def compute_magnus_force(
    velocity: np.ndarray,
    spin_rad_s: np.ndarray,
    ball_config: BallConfig,
    env_config: EnvironmentConfig,
    aero_config: AerodynamicsConfig,
) -> np.ndarray:
    """
    Computes Magnus force vector:
        F_M = 0.5 * rho * A * C_L * |v_rel|^2 * e_L
    where e_L is the unit vector pointing in the direction of (omega x v_rel).
    
    Right-hand rule sign check:
    - Forward flight along +X: v_rel = [Vx, 0, 0] with Vx > 0.
    - Topspin around +Y axis: omega = [0, Wy, 0] with Wy > 0.
      omega x v_rel = [0, 0, -Wy * Vx] -> points downward in -Z (dip).
    - Backspin around -Y axis: omega = [0, -Wy, 0] with Wy > 0.
      omega x v_rel = [0, 0, +Wy * Vx] -> points upward in +Z (lift).
    - Off-spin / Leg-spin around +Z axis:
      omega x v_rel = [0, +Wz * Vx, 0] -> lateral drift in +Y.
    """
    if not aero_config.enable_magnus:
        return np.zeros(3, dtype=float)

    spin = np.asarray(spin_rad_s, dtype=float)
    spin_norm = np.linalg.norm(spin)
    if spin_norm < 1e-9:
        return np.zeros(3, dtype=float)

    v_rel, speed_rel = compute_relative_velocity(velocity, np.asarray(env_config.wind_vector_m_s))
    if speed_rel < 1e-9:
        return np.zeros(3, dtype=float)

    lift_vector = np.cross(spin, v_rel)
    lift_norm = np.linalg.norm(lift_vector)
    if lift_norm < 1e-9:
        return np.zeros(3, dtype=float)

    e_lift = lift_vector / lift_norm

    _, sp = compute_spin_parameter(spin, speed_rel, ball_config)
    cl = evaluate_lift_coefficient(sp, aero_config)

    rho = env_config.air_density_kg_m3
    area = ball_config.cross_sectional_area_m2
    force_magnitude = 0.5 * rho * area * cl * (speed_rel ** 2)

    return force_magnitude * e_lift

