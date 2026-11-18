"""
Numerical trajectory flight simulator using scipy.integrate.solve_ivp.

Supports:
- Gravity-only ballistic trajectories.
- Full aerodynamic trajectories (drag, Magnus, wind).
- Continuous ground contact event detection.
- Dense solution interpolation for precise time matching with tracking frames.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, Union, List
import numpy as np
from scipy.integrate import solve_ivp

from cricket_trajectory_engine.config.physics_config import (
    BallConfig,
    EnvironmentConfig,
    AerodynamicsConfig,
    SimulationConfig,
)
from cricket_trajectory_engine.physics.aerodynamics import compute_total_acceleration
from cricket_trajectory_engine.physics.gravity import compute_gravity_acceleration


@dataclass
class TrajectoryResult:
    """Standardized output container for simulated trajectory flight."""
    time_s: np.ndarray
    positions_m: np.ndarray        # Shape (N, 3) [X, Y, Z]
    velocities_m_s: np.ndarray     # Shape (N, 3) [Vx, Vy, Vz]
    landing: Optional[Dict[str, Any]]
    max_height_m: float
    flight_time_s: float
    horizontal_range_m: float
    initial_position_m: np.ndarray
    initial_velocity_m_s: np.ndarray
    initial_speed_m_s: float
    solver_success: bool
    solver_message: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "time_s": self.time_s.tolist(),
            "positions_m": self.positions_m.tolist(),
            "velocities_m_s": self.velocities_m_s.tolist(),
            "landing": self.landing,
            "max_height_m": self.max_height_m,
            "flight_time_s": self.flight_time_s,
            "horizontal_range_m": self.horizontal_range_m,
            "initial_position_m": self.initial_position_m.tolist(),
            "initial_velocity_m_s": self.initial_velocity_m_s.tolist(),
            "initial_speed_m_s": self.initial_speed_m_s,
            "solver_success": self.solver_success,
            "solver_message": self.solver_message,
        }


def _equations_of_motion(
    t: float,
    state: np.ndarray,
    ball_config: BallConfig,
    env_config: EnvironmentConfig,
    aero_config: AerodynamicsConfig,
    spin_rad_s: np.ndarray,
    gravity_only: bool = False,
) -> np.ndarray:
    """State derivative dS/dt = [vx, vy, vz, ax, ay, az]."""
    vel = state[3:6]
    if gravity_only:
        accel = compute_gravity_acceleration(env_config)
    else:
        accel = compute_total_acceleration(vel, spin_rad_s, ball_config, env_config, aero_config)
    return np.concatenate((vel, accel))


def _make_ground_contact_event(ball_radius_m: float):
    """Creates a zero-crossing event when ball bottom touches Z=0 (centre at Z=radius)."""
    def ground_event(t, state, *args):
        return state[2] - ball_radius_m

    ground_event.terminal = True
    ground_event.direction = -1  # Falling downward
    return ground_event


def simulate_flight(
    initial_position_m: Union[List[float], np.ndarray],
    initial_velocity_m_s: Union[List[float], np.ndarray],
    ball_config: Optional[BallConfig] = None,
    env_config: Optional[EnvironmentConfig] = None,
    aero_config: Optional[AerodynamicsConfig] = None,
    sim_config: Optional[SimulationConfig] = None,
    spin_rad_s: Optional[Union[List[float], np.ndarray]] = None,
    gravity_only: bool = False,
    t_eval: Optional[np.ndarray] = None,
    stop_at_ground: bool = True,
) -> TrajectoryResult:
    """
    Simulates a 3D cricket ball flight from initial state to ground impact.
    
    Parameters:
        initial_position_m: [X0, Y0, Z0] in metres.
        initial_velocity_m_s: [Vx0, Vy0, Vz0] in m/s.
        ball_config: Ball physical specs (mass, diameter).
        env_config: Ambient air density, gravity, wind.
        aero_config: Drag and lift coefficients.
        sim_config: Numerical solver tolerances.
        spin_rad_s: Spin vector [wx, wy, wz] (overrides aero_config.spin_rad_s if provided).
        gravity_only: If True, disables drag and lift (pure vacuum ballistic motion).
        t_eval: Explicit evaluation timestamps (optional).
        stop_at_ground: If True, terminates integration when Z reaches ball radius.
    """
    ball = ball_config or BallConfig()
    env = env_config or EnvironmentConfig()
    aero = aero_config or AerodynamicsConfig()
    sim = sim_config or SimulationConfig()

    pos0 = np.asarray(initial_position_m, dtype=float)
    vel0 = np.asarray(initial_velocity_m_s, dtype=float)

    if pos0[2] < ball.radius_m:
        raise ValueError(
            f"Initial ball-centre height ({pos0[2]:.4f} m) cannot be below "
            f"ball radius ({ball.radius_m:.4f} m)."
        )

    y0 = np.concatenate((pos0, vel0))
    current_spin = np.asarray(spin_rad_s if spin_rad_s is not None else aero.spin_rad_s, dtype=float)

    events = [_make_ground_contact_event(ball.radius_m)] if stop_at_ground else None

    sol = solve_ivp(
        fun=_equations_of_motion,
        t_span=(0.0, sim.max_flight_time_s),
        y0=y0,
        method=sim.integration_method,
        t_eval=t_eval,
        events=events,
        max_step=sim.max_step_s,
        rtol=sim.rtol,
        atol=sim.atol,
        args=(ball, env, aero, current_spin, gravity_only),
    )

    times = sol.t
    states = sol.y.T
    positions = states[:, :3]
    velocities = states[:, 3:6]

    landing = None
    if events and len(sol.t_events[0]) > 0:
        t_land = float(sol.t_events[0][0])
        landing_state = sol.y_events[0][0]
        pos_land = landing_state[:3]
        vel_land = landing_state[3:6]
        horiz_range = float(np.hypot(pos_land[0] - pos0[0], pos_land[1] - pos0[1]))
        v_impact_horiz = float(np.hypot(vel_land[0], vel_land[1]))
        impact_angle_deg = float(np.degrees(np.arctan2(abs(vel_land[2]), max(1e-6, v_impact_horiz))))

        landing = {
            "time_s": t_land,
            "position_m": pos_land.tolist(),
            "velocity_m_s": vel_land.tolist(),
            "speed_m_s": float(np.linalg.norm(vel_land)),
            "horizontal_range_m": horiz_range,
            "impact_angle_deg": impact_angle_deg,
        }
        flight_time = t_land
        horizontal_range = horiz_range
    else:
        flight_time = float(times[-1])
        horizontal_range = float(np.hypot(positions[-1, 0] - pos0[0], positions[-1, 1] - pos0[1]))

    return TrajectoryResult(
        time_s=times,
        positions_m=positions,
        velocities_m_s=velocities,
        landing=landing,
        max_height_m=float(np.max(positions[:, 2])),
        flight_time_s=flight_time,
        horizontal_range_m=horizontal_range,
        initial_position_m=pos0,
        initial_velocity_m_s=vel0,
        initial_speed_m_s=float(np.linalg.norm(vel0)),
        solver_success=bool(sol.success),
        solver_message=str(sol.message),
    )

