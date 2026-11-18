"""
Cricket field geometry, boundaries, and inner circle representation.
"""

from dataclasses import dataclass
from typing import Optional, Tuple, List
import numpy as np

from cricket_trajectory_engine.config.physics_config import FieldConfig


@dataclass
class BoundaryIntersection:
    """Information about where and when the ball intersects the field boundary."""
    intersects: bool
    intersection_point_m: Optional[np.ndarray] = None
    intersection_time_s: Optional[float] = None
    height_at_crossing_m: Optional[float] = None
    distance_from_origin_m: Optional[float] = None
    crossed_on_full: bool = False  # True if crossed while airborne on first flight


class CricketField:
    """
    Cricket ground boundary geometry.
    Origin (0, 0, 0) is the centre of the pitch / batsman's stance at the batting crease.
    """
    def __init__(self, config: Optional[FieldConfig] = None):
        self.config = config or FieldConfig()
        self.radius_m = self.config.boundary_radius_m
        self.semi_major_m = self.config.semi_major_m
        self.semi_minor_m = self.config.semi_minor_m
        self.inner_ring_radius_m = self.config.inner_ring_radius_m

    def boundary_radius_at_azimuth(self, azimuth_rad: float) -> float:
        """
        Computes distance from origin to boundary at a given azimuth angle.
        Supports circular or elliptical grounds (major axis straight down X, minor across Y).
        """
        if self.semi_major_m is not None and self.semi_minor_m is not None:
            a = self.semi_major_m
            b = self.semi_minor_m
            # Polar equation of ellipse: r(theta) = (a * b) / sqrt((b * cos(theta))^2 + (a * sin(theta))^2)
            denom = np.sqrt((b * np.cos(azimuth_rad)) ** 2 + (a * np.sin(azimuth_rad)) ** 2)
            return float((a * b) / max(1e-6, denom))
        return float(self.radius_m)

    def is_inside_boundary(self, x: float, y: float) -> bool:
        """Checks if 2D ground coordinates (x, y) lie inside boundary."""
        azimuth = np.arctan2(y, x)
        r_bnd = self.boundary_radius_at_azimuth(azimuth)
        return float(np.hypot(x, y)) <= r_bnd

    def is_inside_inner_ring(self, x: float, y: float) -> bool:
        """Checks if point is inside the 30-yard inner circle."""
        return float(np.hypot(x, y)) <= self.inner_ring_radius_m

    def find_boundary_crossing(
        self,
        times_s: np.ndarray,
        positions_m: np.ndarray,
        first_bounce_time_s: Optional[float] = None,
    ) -> BoundaryIntersection:
        """
        Finds the exact moment and position where trajectory crosses the boundary.
        """
        n = len(times_s)
        if n < 2:
            return BoundaryIntersection(intersects=False)

        for i in range(n - 1):
            p1 = positions_m[i]
            p2 = positions_m[i + 1]
            t1 = times_s[i]
            t2 = times_s[i + 1]

            d1 = np.hypot(p1[0], p1[1])
            d2 = np.hypot(p2[0], p2[1])

            az1 = np.arctan2(p1[1], p1[0])
            az2 = np.arctan2(p2[1], p2[0])
            r_bnd1 = self.boundary_radius_at_azimuth(az1)
            r_bnd2 = self.boundary_radius_at_azimuth(az2)

            if d1 <= r_bnd1 and d2 > r_bnd2:
                # Interpolate crossing point
                fraction = (r_bnd1 - d1) / max(1e-6, (d2 - d1))
                fraction = np.clip(fraction, 0.0, 1.0)

                cross_p = p1 + fraction * (p2 - p1)
                cross_t = float(t1 + fraction * (t2 - t1))
                cross_z = float(cross_p[2])
                cross_dist = float(np.hypot(cross_p[0], cross_p[1]))

                on_full = (
                    first_bounce_time_s is None or cross_t <= (first_bounce_time_s + 1e-4)
                ) and cross_z > 0.036

                return BoundaryIntersection(
                    intersects=True,
                    intersection_point_m=cross_p,
                    intersection_time_s=cross_t,
                    height_at_crossing_m=cross_z,
                    distance_from_origin_m=cross_dist,
                    crossed_on_full=on_full,
                )

        return BoundaryIntersection(intersects=False)

