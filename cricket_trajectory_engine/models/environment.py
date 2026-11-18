"""
Environment, Aerodynamic, and Turf Contact Models.
"""

from dataclasses import dataclass, field, asdict
from typing import Tuple, Dict, Any, List


SURFACE_PRESETS = {
    "natural_grass": {
        "name": "Natural Grass (Standard International)",
        "restitution_normal": 0.55,
        "friction_tangential": 0.38,
        "rolling_resistance_coeff": 0.20,
        "description": "Standard well-maintained international natural grass turf and outfield."
    },
    "dry_outfield": {
        "name": "Dry & Fast Outfield",
        "restitution_normal": 0.60,
        "friction_tangential": 0.34,
        "rolling_resistance_coeff": 0.16,
        "description": "Hard-baked dry grass surface allowing balls to travel faster and bounce higher."
    },
    "wet_outfield": {
        "name": "Wet / Damp Outfield",
        "restitution_normal": 0.48,
        "friction_tangential": 0.45,
        "rolling_resistance_coeff": 0.28,
        "description": "Moist grass with higher traction, deadening normal bounce and pulling shots up short."
    },
    "hard_practice_surface": {
        "name": "Hard Synthetic / Practice Turf",
        "restitution_normal": 0.68,
        "friction_tangential": 0.30,
        "rolling_resistance_coeff": 0.12,
        "description": "Synthetic astroturf or concrete-backed training net pitch with high rebound."
    }
}


@dataclass
class EnvironmentModel:
    air_density_kg_m3: float = 1.225
    dynamic_viscosity_pa_s: float = 1.81e-5
    gravity_m_s2: float = 9.80665
    wind_vector_m_s: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    # Aerodynamic model settings:
    drag_model: str = "constant"         # "constant" or "reynolds_dependent"
    constant_cd: float = 0.32            # Baker (2010), Grimshaw et al. (2024)
    enable_magnus: bool = False
    magnus_model: str = "spin_parameter" # "constant_cl" or "spin_parameter"
    constant_cl: float = 0.15
    spin_rad_s: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    # Turf contact settings:
    surface_preset: str = "natural_grass"
    restitution_normal: float = 0.55
    friction_tangential: float = 0.38
    rolling_resistance_coeff: float = 0.20

    def apply_surface_preset(self, preset_key: str) -> None:
        if preset_key in SURFACE_PRESETS:
            p = SURFACE_PRESETS[preset_key]
            self.surface_preset = preset_key
            self.restitution_normal = p["restitution_normal"]
            self.friction_tangential = p["friction_tangential"]
            self.rolling_resistance_coeff = p["rolling_resistance_coeff"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "air_density_kg_m3": self.air_density_kg_m3,
            "dynamic_viscosity_pa_s": self.dynamic_viscosity_pa_s,
            "gravity_m_s2": self.gravity_m_s2,
            "wind_vector_m_s": list(self.wind_vector_m_s),
            "drag_model": self.drag_model,
            "constant_cd": self.constant_cd,
            "enable_magnus": self.enable_magnus,
            "magnus_model": self.magnus_model,
            "constant_cl": self.constant_cl,
            "spin_rad_s": list(self.spin_rad_s),
            "surface_preset": self.surface_preset,
            "restitution_normal": self.restitution_normal,
            "friction_tangential": self.friction_tangential,
            "rolling_resistance_coeff": self.rolling_resistance_coeff,
            "available_presets": SURFACE_PRESETS,
        }

