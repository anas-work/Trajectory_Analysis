"""
Gravitational force and acceleration module.
"""

import numpy as np
from cricket_trajectory_engine.config.physics_config import EnvironmentConfig


def compute_gravity_acceleration(env_config: EnvironmentConfig) -> np.ndarray:
    """
    Returns gravitational acceleration vector [0, 0, -g] in m/s^2.
    
    Coordinate convention:
    Z is vertical, positive pointing upwards away from ground plane.
    """
    return np.array([0.0, 0.0, -env_config.gravity_m_s2], dtype=float)

