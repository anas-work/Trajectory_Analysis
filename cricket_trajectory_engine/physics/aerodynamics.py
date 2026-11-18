"""
Unified aerodynamics module combining drag, Magnus effect, and seam force interfaces.

References:
- C. J. Baker (2010), "A Calculation of Cricket Ball Trajectories".
- C. J. Baker (2013), "A unified framework for the prediction of cricket ball trajectories in spin and swing bowling".
- S. D. Grimshaw, A. Briggs, & N. R. Atkins (2024), "A review and reassessment of the aerodynamics of cricket ball swing".
"""

from typing import Dict, Any
import numpy as np

from cricket_trajectory_engine.config.physics_config import (
    BallConfig,
    EnvironmentConfig,
    AerodynamicsConfig,
)
from cricket_trajectory_engine.physics.drag import compute_drag_force, compute_relative_velocity
from cricket_trajectory_engine.physics.magnus import compute_magnus_force
from cricket_trajectory_engine.physics.gravity import compute_gravity_acceleration


def compute_seam_force(
    velocity: np.ndarray,
    ball_config: BallConfig,
    env_config: EnvironmentConfig,
    aero_config: AerodynamicsConfig,
) -> np.ndarray:
    """
    Modular interface for seam-induced aerodynamic side forces.
    
    Status: DISABLED in the baseline engine.
    
    Scientific justification (Grimshaw et al. 2024):
    Conventional and reverse swing require precise knowledge of seam orientation
    vector, angle of attack to airflow (typically 10-20 degrees for conventional swing),
    laminar separation bubble dynamics on the seam side, and bilateral surface roughness.
    In the absence of high-speed seam-tracking video or wind-tunnel calibration for this
    specific ball, applying an arbitrary lateral force would be scientifically unjustified.
    """
    if not aero_config.enable_seam_effects or aero_config.seam_side_force_cs == 0.0:
        return np.zeros(3, dtype=float)

    v_rel, speed_rel = compute_relative_velocity(velocity, np.asarray(env_config.wind_vector_m_s))
    if speed_rel < 1e-9:
        return np.zeros(3, dtype=float)

    # Unit vector perpendicular to velocity in horizontal plane:
    # v_rel_horiz = [vx, vy, 0] -> lateral normal is [-vy, vx, 0]
    horiz_speed = np.hypot(v_rel[0], v_rel[1])
    if horiz_speed < 1e-9:
        return np.zeros(3, dtype=float)

    lateral_dir = np.array([-v_rel[1], v_rel[0], 0.0], dtype=float) / horiz_speed

    rho = env_config.air_density_kg_m3
    area = ball_config.cross_sectional_area_m2
    side_force_mag = 0.5 * rho * area * aero_config.seam_side_force_cs * (speed_rel ** 2)

    return side_force_mag * lateral_dir


def compute_total_acceleration(
    velocity: np.ndarray,
    spin_rad_s: np.ndarray,
    ball_config: BallConfig,
    env_config: EnvironmentConfig,
    aero_config: AerodynamicsConfig,
) -> np.ndarray:
    """
    Computes total acceleration vector:
        a = g + (F_drag + F_magnus + F_seam) / m
    """
    g = compute_gravity_acceleration(env_config)
    f_drag = compute_drag_force(velocity, ball_config, env_config, aero_config)
    f_magnus = compute_magnus_force(velocity, spin_rad_s, ball_config, env_config, aero_config)
    f_seam = compute_seam_force(velocity, ball_config, env_config, aero_config)

    total_aero_force = f_drag + f_magnus + f_seam
    return g + (total_aero_force / ball_config.mass_kg)


def compute_aerodynamic_breakdown(
    velocity: np.ndarray,
    spin_rad_s: np.ndarray,
    ball_config: BallConfig,
    env_config: EnvironmentConfig,
    aero_config: AerodynamicsConfig,
) -> Dict[str, Any]:
    """Provides a diagnostic breakdown of all forces and accelerations."""
    v_rel, speed_rel = compute_relative_velocity(velocity, np.asarray(env_config.wind_vector_m_s))
    f_drag = compute_drag_force(velocity, ball_config, env_config, aero_config)
    f_magnus = compute_magnus_force(velocity, spin_rad_s, ball_config, env_config, aero_config)
    f_seam = compute_seam_force(velocity, ball_config, env_config, aero_config)
    g = compute_gravity_acceleration(env_config)
    
    return {
        "speed_rel_m_s": speed_rel,
        "drag_force_N": f_drag.tolist(),
        "drag_magnitude_N": float(np.linalg.norm(f_drag)),
        "magnus_force_N": f_magnus.tolist(),
        "magnus_magnitude_N": float(np.linalg.norm(f_magnus)),
        "seam_force_N": f_seam.tolist(),
        "gravity_accel_m_s2": g.tolist(),
    }

