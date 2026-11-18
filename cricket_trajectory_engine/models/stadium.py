"""
Stadium & Cricket Ground Domain Model.
Supports standard circular, elliptical, and arbitrary polygonal ground boundaries.
"""

import math
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional
import numpy as np


@dataclass
class StadiumModel:
    boundary_shape: str = "circular"  # "circular", "elliptical", "polygon"
    boundary_radius_m: float = 70.0
    straight_boundary_m: float = 75.0
    square_boundary_m: float = 65.0
    polygon_points: List[Tuple[float, float]] = field(default_factory=list)

    # Standard pitch dimensions (MCC Law 6):
    pitch_length_m: float = 20.12     # 22 yards
    pitch_width_m: float = 3.05       # 10 feet
    popping_crease_dist_m: float = 1.22 # 4 feet from stumps
    stump_height_m: float = 0.711     # 28 inches
    stump_width_m: float = 0.2286     # 9 inches
    inner_circle_radius_m: float = 27.43 # 30 yards

    def get_boundary_radius_at_azimuth(self, azimuth_rad: float) -> float:
        """Computes distance from striker's crease (0, 0) to boundary at given azimuth angle."""
        if self.boundary_shape == "circular":
            return self.boundary_radius_m
        elif self.boundary_shape == "elliptical":
            a = self.straight_boundary_m
            b = self.square_boundary_m
            cos_phi = math.cos(azimuth_rad)
            sin_phi = math.sin(azimuth_rad)
            denom = math.sqrt((b * cos_phi) ** 2 + (a * sin_phi) ** 2)
            return (a * b) / denom if denom > 1e-6 else self.boundary_radius_m
        elif self.boundary_shape == "polygon" and len(self.polygon_points) >= 3:
            # Ray-polygon intersection from origin along direction (cos_phi, sin_phi):
            dx = math.cos(azimuth_rad)
            dy = math.sin(azimuth_rad)
            min_dist = float("inf")
            n = len(self.polygon_points)
            for i in range(n):
                p1 = self.polygon_points[i]
                p2 = self.polygon_points[(i + 1) % n]
                # Ray: t * (dx, dy), Segment: p1 + u * (p2 - p1)
                x1, y1 = p1
                x2, y2 = p2
                denom = dx * (y2 - y1) - dy * (x2 - x1)
                if abs(denom) > 1e-9:
                    t = ((x1) * (y2 - y1) - (y1) * (x2 - x1)) / denom
                    u = ((x1) * dy - (y1) * dx) / denom
                    if t > 0.0 and 0.0 <= u <= 1.0:
                        if t < min_dist:
                            min_dist = t
            return min_dist if min_dist != float("inf") else self.boundary_radius_m
        return self.boundary_radius_m

    def is_inside_boundary(self, x: float, y: float) -> bool:
        r = math.hypot(x, y)
        phi = math.atan2(y, x)
        r_bnd = self.get_boundary_radius_at_azimuth(phi)
        return r <= r_bnd

    def is_inside_30_yard_circle(self, x: float, y: float) -> bool:
        """Distance from pitch center (pitch_length / 2, 0) to point."""
        center_x = self.pitch_length_m / 2.0
        return math.hypot(x - center_x, y) <= self.inner_circle_radius_m

    def to_dict(self) -> Dict[str, Any]:
        return {
            "boundary_shape": self.boundary_shape,
            "boundary_radius_m": self.boundary_radius_m,
            "straight_boundary_m": self.straight_boundary_m,
            "square_boundary_m": self.square_boundary_m,
            "polygon_points": self.polygon_points,
            "pitch_length_m": self.pitch_length_m,
            "pitch_width_m": self.pitch_width_m,
            "popping_crease_dist_m": self.popping_crease_dist_m,
            "stump_height_m": self.stump_height_m,
            "stump_width_m": self.stump_width_m,
            "inner_circle_radius_m": self.inner_circle_radius_m,
        }

