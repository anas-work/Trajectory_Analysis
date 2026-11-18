"""
Ball Domain Model with auto-calculated physical geometric properties.
"""

import math
from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class BallModel:
    mass_kg: float = 0.160              # MCC Law 4: 0.1559 - 0.1630 kg
    diameter_m: float = 0.0725          # MCC Law 4: 0.0713 - 0.0729 m
    seam_type: str = "standard_4_piece"  # "standard_4_piece", "red_dukes", "white_kookaburra"

    @property
    def radius_m(self) -> float:
        return self.diameter_m / 2.0

    @property
    def area_m2(self) -> float:
        """Frontal projected cross-sectional area: A = pi * D^2 / 4"""
        return math.pi * (self.diameter_m ** 2) / 4.0

    @property
    def moment_of_inertia_kg_m2(self) -> float:
        """
        Moment of inertia for cricket ball: I = (2/3) * m * R^2.
        Approximates leather shell with cork/twine composite core.
        """
        return (2.0 / 3.0) * self.mass_kg * (self.radius_m ** 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mass_kg": self.mass_kg,
            "diameter_m": self.diameter_m,
            "radius_m": round(self.radius_m, 5),
            "area_m2": round(self.area_m2, 7),
            "moment_of_inertia_kg_m2": round(self.moment_of_inertia_kg_m2, 7),
            "seam_type": self.seam_type,
            "explanations": {
                "area_formula": "A = π * D² / 4",
                "radius_formula": "R = D / 2",
                "inertia_formula": "I = (2/3) * m * R²",
            }
        }

