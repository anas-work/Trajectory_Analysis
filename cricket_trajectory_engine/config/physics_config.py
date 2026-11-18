"""
Configuration data structures for the Cricket Ball Flight Engine.
All parameters are typed, validated, and given scientifically documented defaults.
"""

from dataclasses import dataclass, field
from typing import Tuple, Optional
import numpy as np

from cricket_trajectory_engine.physics.constants import (
    DEFAULT_BALL_MASS_KG,
    DEFAULT_BALL_DIAMETER_M,
    DEFAULT_BALL_RADIUS_M,
    DEFAULT_BALL_AREA_M2,
    DEFAULT_BALL_INERTIA_KG_M2,
    DEFAULT_AIR_DENSITY_KG_M3,
    DEFAULT_AIR_DYNAMIC_VISCOSITY_PA_S,
    STANDARD_GRAVITY_M_S2,
    DEFAULT_DRAG_COEFFICIENT_CD,
    DEFAULT_RESTITUTION_NORMAL,
    DEFAULT_FRICTION_TANGENTIAL,
    DEFAULT_ROLLING_RESISTANCE_COEFF,
    DEFAULT_STOPPING_VELOCITY_TOL_M_S,
)


@dataclass(frozen=True)
class BallConfig:
    """Properties of the cricket ball according to MCC Law 4."""
    mass_kg: float = DEFAULT_BALL_MASS_KG
    diameter_m: float = DEFAULT_BALL_DIAMETER_M

    def __post_init__(self):
        if self.mass_kg <= 0:
            raise ValueError(f"Ball mass must be positive, got {self.mass_kg} kg")
        if self.diameter_m <= 0:
            raise ValueError(f"Ball diameter must be positive, got {self.diameter_m} m")

    @property
    def radius_m(self) -> float:
        return self.diameter_m / 2.0

    @property
    def cross_sectional_area_m2(self) -> float:
        return np.pi * (self.radius_m ** 2)

    @property
    def moment_of_inertia_kg_m2(self) -> float:
        """Solid sphere approximation: I = (2/5) * m * r^2."""
        return 0.4 * self.mass_kg * (self.radius_m ** 2)


@dataclass(frozen=True)
class EnvironmentConfig:
    """Ambient atmospheric and gravitational conditions."""
    air_density_kg_m3: float = DEFAULT_AIR_DENSITY_KG_M3
    dynamic_viscosity_pa_s: float = DEFAULT_AIR_DYNAMIC_VISCOSITY_PA_S
    gravity_m_s2: float = STANDARD_GRAVITY_M_S2
    # Wind vector [Wx, Wy, Wz] in m/s (default calm air)
    wind_vector_m_s: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    def __post_init__(self):
        if self.air_density_kg_m3 <= 0:
            raise ValueError(f"Air density must be positive, got {self.air_density_kg_m3}")
        if self.dynamic_viscosity_pa_s <= 0:
            raise ValueError(f"Dynamic viscosity must be positive, got {self.dynamic_viscosity_pa_s}")
        if self.gravity_m_s2 <= 0:
            raise ValueError(f"Gravity must be positive, got {self.gravity_m_s2}")
        if len(self.wind_vector_m_s) != 3:
            raise ValueError("Wind vector must be a 3-element tuple (Wx, Wy, Wz)")


@dataclass(frozen=True)
class AerodynamicsConfig:
    """
    Aerodynamic configuration.
    
    Includes:
    - Drag model: 'constant' or 'reynolds_dependent'
    - Baseline constant Cd: 0.32 (Baker 2010)
    - Magnus force: enabled flag, lift coefficient model ('constant_cl' or 'spin_parameter'),
      spin vector [wx, wy, wz] in rad/s, and base Cl
    - Seam force: modular interface (disabled in baseline per Grimshaw et al. 2024)
    """
    drag_model: str = "constant"  # "constant" or "reynolds_dependent"
    constant_cd: float = DEFAULT_DRAG_COEFFICIENT_CD
    
    # Magnus / spin parameters (Baker 2013):
    enable_magnus: bool = False
    magnus_model: str = "spin_parameter"  # "constant_cl" or "spin_parameter"
    constant_cl: float = 0.15
    # Angular velocity vector [omega_x, omega_y, omega_z] in rad/s:
    spin_rad_s: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    
    # Seam-related lateral force (Grimshaw et al. 2024):
    enable_seam_effects: bool = False
    seam_angle_deg: float = 0.0
    seam_side_force_cs: float = 0.0

    def __post_init__(self):
        if self.drag_model not in ("constant", "reynolds_dependent"):
            raise ValueError(f"Unknown drag model '{self.drag_model}'")
        if self.constant_cd < 0:
            raise ValueError(f"Drag coefficient Cd cannot be negative, got {self.constant_cd}")
        if len(self.spin_rad_s) != 3:
            raise ValueError("spin_rad_s must be a 3-element tuple (wx, wy, wz)")


@dataclass(frozen=True)
class GroundCollisionConfig:
    """Ground restitution, friction, and multi-bounce stopping parameters."""
    restitution_normal: float = DEFAULT_RESTITUTION_NORMAL
    friction_tangential: float = DEFAULT_FRICTION_TANGENTIAL
    rolling_resistance_coeff: float = DEFAULT_ROLLING_RESISTANCE_COEFF
    stopping_velocity_tol_m_s: float = DEFAULT_STOPPING_VELOCITY_TOL_M_S
    max_bounces: int = 15

    def __post_init__(self):
        if not (0.0 <= self.restitution_normal <= 1.0):
            raise ValueError("Restitution coefficient must be in [0, 1]")
        if self.friction_tangential < 0.0:
            raise ValueError("Tangential friction cannot be negative")


@dataclass(frozen=True)
class FieldConfig:
    """
    Field geometry for boundary and cricket outcome evaluation.
    Default boundary is a 70 m radius circular boundary from pitch centre (0, 0).
    Can also specify elliptical semi-axes (e.g. 75m straight, 65m square).
    """
    boundary_radius_m: float = 70.0
    semi_major_m: Optional[float] = None  # Straight boundary (m)
    semi_minor_m: Optional[float] = None  # Square boundary (m)
    inner_ring_radius_m: float = 27.432   # 30-yard circle (27.432 m)
    pitch_length_m: float = 20.12         # 22 yards (20.12 m)


@dataclass(frozen=True)
class SimulationConfig:
    """Numerical solver settings for scipy.integrate.solve_ivp."""
    integration_method: str = "RK45"
    rtol: float = 1e-8
    atol: float = 1e-10
    max_step_s: float = 0.005
    max_flight_time_s: float = 20.0

