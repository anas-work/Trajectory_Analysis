"""
Initial state, velocity, and launch-angle estimation from 3D coordinate observations.

Methods:
1. Two-point consecutive finite differences.
2. Robust multi-point polynomial regression (least-squares).
3. Estimation diagnostics, residual analysis, and launch angles.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple
import numpy as np

from cricket_trajectory_engine.estimation.coordinate_loader import ObservationSet, validate_observations


@dataclass
class InitialStateEstimate:
    """Estimated initial kinematic state from coordinate observations."""
    initial_position_m: np.ndarray       # [X0, Y0, Z0]
    initial_velocity_m_s: np.ndarray     # [Vx0, Vy0, Vz0]
    initial_speed_m_s: float
    elevation_angle_deg: float          # Angle above horizontal (pitch / launch angle)
    azimuth_angle_deg: float            # Angle in horizontal plane (shot direction)
    initial_acceleration_m_s2: Optional[np.ndarray]  # Estimated from 2nd-order fit
    method_used: str
    observation_count: int
    observation_duration_s: float
    position_fit_rmse_m: Dict[str, float]
    velocity_uncertainty_std_m_s: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "initial_position_m": self.initial_position_m.tolist(),
            "initial_velocity_m_s": self.initial_velocity_m_s.tolist(),
            "initial_speed_m_s": self.initial_speed_m_s,
            "elevation_angle_deg": self.elevation_angle_deg,
            "azimuth_angle_deg": self.azimuth_angle_deg,
            "initial_acceleration_m_s2": (
                self.initial_acceleration_m_s2.tolist()
                if self.initial_acceleration_m_s2 is not None
                else None
            ),
            "method_used": self.method_used,
            "observation_count": self.observation_count,
            "observation_duration_s": self.observation_duration_s,
            "position_fit_rmse_m": self.position_fit_rmse_m,
            "velocity_uncertainty_std_m_s": self.velocity_uncertainty_std_m_s,
        }


def compute_launch_angles(velocity: np.ndarray) -> Tuple[float, float, float]:
    """
    Computes (speed, elevation_angle_deg, azimuth_angle_deg).
    
    Elevation angle: angle above horizontal plane (Z=0). Range: [-90, +90] deg.
    Azimuth angle: direction in horizontal plane (X vs Y). 0 deg along +X (straight drive).
    """
    vx, vy, vz = float(velocity[0]), float(velocity[1]), float(velocity[2])
    v_horiz = np.hypot(vx, vy)
    speed = float(np.linalg.norm(velocity))
    elevation_deg = float(np.degrees(np.arctan2(vz, max(1e-9, v_horiz))))
    azimuth_deg = float(np.degrees(np.arctan2(vy, vx)))
    return speed, elevation_deg, azimuth_deg


def estimate_initial_state(
    observations: ObservationSet,
    method: str = "polynomial",
    polynomial_order: int = 2,
) -> InitialStateEstimate:
    """
    Estimates initial state [X0, Y0, Z0, Vx0, Vy0, Vz0] at t = t[0].
    
    Parameters:
        observations: ObservationSet containing timestamps and (X, Y, Z) coordinates.
        method: 'polynomial' (recommended for >=3 points) or 'finite_difference'.
        polynomial_order: 1 (linear/constant velocity) or 2 (quadratic/constant acceleration).
    """
    times = observations.times_s
    positions = observations.positions_m
    n_pts = observations.count

    if n_pts < 2:
        raise ValueError("At least 2 observation points are required to estimate velocity.")

    t0 = times[0]
    t_rel = times - t0  # Shift time so t_rel[0] = 0

    if method == "finite_difference" or n_pts == 2:
        # Two-point or consecutive differences
        dt = times[1] - times[0]
        vel0 = (positions[1] - positions[0]) / dt
        pos0 = positions[0].copy()
        accel0 = None
        method_name = "finite_difference"
        rmse_dict = {"x": 0.0, "y": 0.0, "z": 0.0, "total": 0.0}
        uncert = None

    elif method == "polynomial":
        order = min(polynomial_order, n_pts - 1)
        fitted_pos0 = np.zeros(3)
        vel0 = np.zeros(3)
        accel0 = np.zeros(3) if order >= 2 else None
        resids = []

        for ax in range(3):
            # Fit polynomial: p_ax(t) = c_k * t^k + ... + c_1 * t + c_0
            coeffs, cov = np.polyfit(t_rel, positions[:, ax], deg=order, cov=True)
            # Evaluate at t_rel = 0:
            poly = np.poly1d(coeffs)
            fitted_pos0[ax] = poly(0.0)

            # Derivative at t_rel = 0:
            deriv = np.polyder(poly, m=1)
            vel0[ax] = deriv(0.0)

            if order >= 2 and accel0 is not None:
                deriv2 = np.polyder(poly, m=2)
                accel0[ax] = deriv2(0.0)

            fit_vals = poly(t_rel)
            ax_rmse = float(np.sqrt(np.mean((fit_vals - positions[:, ax]) ** 2)))
            resids.append(ax_rmse)

        # Anchor initial position to observed first point to prevent offset drift:
        pos0 = positions[0].copy()
        total_rmse = float(np.sqrt(np.mean(np.array(resids) ** 2)))
        rmse_dict = {
            "x": resids[0],
            "y": resids[1],
            "z": resids[2],
            "total": total_rmse,
        }
        method_name = f"polynomial_deg_{order}"
        uncert = float(total_rmse / max(1e-6, np.mean(np.diff(t_rel))))

    else:
        raise ValueError(f"Unknown estimation method: {method}")

    speed, elev, azim = compute_launch_angles(vel0)

    return InitialStateEstimate(
        initial_position_m=pos0,
        initial_velocity_m_s=vel0,
        initial_speed_m_s=speed,
        elevation_angle_deg=elev,
        azimuth_angle_deg=azim,
        initial_acceleration_m_s2=accel0,
        method_used=method_name,
        observation_count=n_pts,
        observation_duration_s=observations.duration_s,
        position_fit_rmse_m=rmse_dict,
        velocity_uncertainty_std_m_s=uncert,
    )

