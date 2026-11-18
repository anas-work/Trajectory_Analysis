"""
Physical constants and official MCC cricket ball specifications.
"""

from typing import Final

# MCC Law 4 - The Ball (Standard Men's Match Cricket Ball):
# Mass: 155.9 g to 163.0 g (5.5 to 5.75 oz) -> nominal 160.0 g
DEFAULT_BALL_MASS_KG: Final[float] = 0.160

# Circumference: 22.4 cm to 22.9 cm -> Diameter: 0.0713 m to 0.0729 m -> nominal 0.0725 m
DEFAULT_BALL_DIAMETER_M: Final[float] = 0.0725
DEFAULT_BALL_RADIUS_M: Final[float] = DEFAULT_BALL_DIAMETER_M / 2.0
DEFAULT_BALL_AREA_M2: Final[float] = 3.141592653589793 * (DEFAULT_BALL_RADIUS_M ** 2)

# Moment of inertia for a solid sphere: I = (2/5) * m * r^2
# (Cricket ball cork/twine core with 4-piece leather casing is closely approximated by solid sphere)
DEFAULT_BALL_INERTIA_KG_M2: Final[float] = 0.4 * DEFAULT_BALL_MASS_KG * (DEFAULT_BALL_RADIUS_M ** 2)

# Standard Atmospheric Conditions (ISA at sea level, 15 °C, 1013.25 hPa):
DEFAULT_AIR_DENSITY_KG_M3: Final[float] = 1.225
DEFAULT_AIR_DYNAMIC_VISCOSITY_PA_S: Final[float] = 1.81e-5  # Pa*s at 15 °C

# Standard Gravitational Acceleration (WGS-84 / ISO 80000-3):
STANDARD_GRAVITY_M_S2: Final[float] = 9.80665

# Aerodynamic Baseline Parameters (Baker 2010; Grimshaw et al. 2024):
# Subcritical cricket ball drag coefficient typically sits between 0.30 and 0.35:
DEFAULT_DRAG_COEFFICIENT_CD: Final[float] = 0.32

# Ground contact & bounce baseline parameters (Banerjee & McPhee 2012; Carré et al.):
DEFAULT_RESTITUTION_NORMAL: Final[float] = 0.55     # Hard turf cricket pitch (0.45 - 0.65)
DEFAULT_FRICTION_TANGENTIAL: Final[float] = 0.38    # Turf grass/clay pitch friction (0.25 - 0.45)
DEFAULT_ROLLING_RESISTANCE_COEFF: Final[float] = 0.20  # Turf grass outfield rolling resistance (0.15 - 0.30)
DEFAULT_STOPPING_VELOCITY_TOL_M_S: Final[float] = 0.05  # Below this horizontal speed, ball is stopped

# Coordinate reference system standard:
# X: Longitudinal / Forward towards bowler/long-off or shot direction (metres)
# Y: Lateral / Across pitch (positive to off-side or leg-side depending on orientation) (metres)
# Z: Vertical altitude above ground plane (metres). Ground is at Z = 0.
