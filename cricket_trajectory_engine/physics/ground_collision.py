"""
Ground collision, bounce mechanics, and multi-bounce rolling simulation.

References:
- J. M. Banerjee & J. J. McPhee (2012), "Simulation of the Three-Dimensional Motion
  of a Cricket Ball Using a Volumetric Contact Model", Procedia Engineering, 34:148-153.
- R. Cross (2002), "Measurements of the horizontal and vertical coefficients of restitution
  for a cricket ball", Sports Engineering.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np

from cricket_trajectory_engine.config.physics_config import (
    BallConfig,
    EnvironmentConfig,
    AerodynamicsConfig,
    GroundCollisionConfig,
    SimulationConfig,
)
from cricket_trajectory_engine.physics.flight_simulator import simulate_flight, TrajectoryResult


@dataclass
class BounceEvent:
    bounce_index: int
    time_s: float
    position_m: np.ndarray
    pre_velocity_m_s: np.ndarray
    post_velocity_m_s: np.ndarray
    pre_speed_m_s: float
    post_speed_m_s: float
    energy_loss_ratio: float


@dataclass
class MultiBounceResult:
    """Contains full trajectory across all airborne bounces and the rolling phase."""
    time_s: np.ndarray
    positions_m: np.ndarray
    velocities_m_s: np.ndarray
    bounces: List[BounceEvent]
    first_bounce: Optional[BounceEvent]
    final_stopping_position_m: np.ndarray
    final_stopping_time_s: float
    total_horizontal_distance_m: float
    stopped: bool


def resolve_ground_impact(
    pre_velocity: np.ndarray,
    pre_spin: np.ndarray,
    ball_config: BallConfig,
    collision_config: GroundCollisionConfig,
) -> tuple[np.ndarray, np.ndarray, float]:
    """
    Applies normal restitution and tangential friction impulse to update velocity and spin.
    
    Physics:
    - Normal component: vz_post = -en * vz_pre  (en in [0, 1])
    - Normal impulse magnitude: Jn = m * (1 + en) * |vz_pre|
    - Maximum friction impulse: Jt_max = mu_t * Jn
    - Tangential velocity reduction:
      delta_vt = -min(|vt_pre|, mu_t * (1 + en) * |vz_pre|) * (vt_pre / |vt_pre|)
    - Angular velocity change from torque about centre:
      delta_L = r_cp x J_friction, with r_cp = [0, 0, -R]
      delta_omega = (m / I) * (-R z_hat x delta_vt)
    
    Returns:
        post_velocity, post_spin, energy_loss_ratio
    """
    vx, vy, vz = pre_velocity
    v_horiz = np.array([vx, vy, 0.0], dtype=float)
    speed_horiz = float(np.hypot(vx, vy))

    en = collision_config.restitution_normal
    mu_t = collision_config.friction_tangential

    # Normal velocity rebound:
    vz_post = -en * vz if vz < 0 else vz

    # Tangential friction impulse:
    if speed_horiz > 1e-9:
        normal_impulse_per_m = (1.0 + en) * abs(vz)
        max_tangential_delta_v = mu_t * normal_impulse_per_m
        delta_v_mag = min(speed_horiz, max_tangential_delta_v)
        v_horiz_unit = v_horiz / speed_horiz
        v_horiz_post = v_horiz - delta_v_mag * v_horiz_unit
        delta_vt = -delta_v_mag * v_horiz_unit
    else:
        v_horiz_post = np.zeros(3, dtype=float)
        delta_vt = np.zeros(3, dtype=float)

    post_velocity = np.array([v_horiz_post[0], v_horiz_post[1], vz_post], dtype=float)

    # Torque on ball from friction force:
    # r_cp = [0, 0, -R]
    # delta_omega = (ball.mass / ball.inertia) * cross(r_cp, delta_vt)
    r_cp = np.array([0.0, 0.0, -ball_config.radius_m], dtype=float)
    delta_spin = (ball_config.mass_kg / ball_config.moment_of_inertia_kg_m2) * np.cross(r_cp, delta_vt)
    post_spin = pre_spin + delta_spin

    e_pre = 0.5 * ball_config.mass_kg * float(np.dot(pre_velocity, pre_velocity))
    e_post = 0.5 * ball_config.mass_kg * float(np.dot(post_velocity, post_velocity))
    loss_ratio = 1.0 - (e_post / max(1e-9, e_pre))

    return post_velocity, post_spin, max(0.0, loss_ratio)


def simulate_multi_bounce(
    initial_position_m: np.ndarray,
    initial_velocity_m_s: np.ndarray,
    ball_config: Optional[BallConfig] = None,
    env_config: Optional[EnvironmentConfig] = None,
    aero_config: Optional[AerodynamicsConfig] = None,
    collision_config: Optional[GroundCollisionConfig] = None,
    sim_config: Optional[SimulationConfig] = None,
    spin_rad_s: Optional[np.ndarray] = None,
) -> MultiBounceResult:
    """
    Simulates consecutive bounces and the final rolling phase until the ball comes to a halt.
    """
    ball = ball_config or BallConfig()
    env = env_config or EnvironmentConfig()
    aero = aero_config or AerodynamicsConfig()
    collision = collision_config or GroundCollisionConfig()
    sim = sim_config or SimulationConfig()

    current_pos = np.asarray(initial_position_m, dtype=float).copy()
    current_vel = np.asarray(initial_velocity_m_s, dtype=float).copy()
    current_spin = np.asarray(spin_rad_s if spin_rad_s is not None else aero.spin_rad_s, dtype=float).copy()
    current_time = 0.0

    all_times: List[float] = []
    all_positions: List[np.ndarray] = []
    all_velocities: List[np.ndarray] = []
    bounces: List[BounceEvent] = []

    bounce_count = 0
    ground_rebound_threshold_vz = 0.25  # m/s; below this normal velocity, ball transitions to roll

    while bounce_count < collision.max_bounces:
        # Simulate current airborne flight phase:
        flight = simulate_flight(
            initial_position_m=current_pos,
            initial_velocity_m_s=current_vel,
            ball_config=ball,
            env_config=env,
            aero_config=aero,
            sim_config=sim,
            spin_rad_s=current_spin,
            stop_at_ground=True,
        )

        n_pts = len(flight.time_s)
        if n_pts > 0:
            phase_times = flight.time_s + current_time
            # Avoid duplicate timestamps at transition boundary
            if all_times and abs(phase_times[0] - all_times[-1]) < 1e-6:
                phase_times = phase_times[1:]
                p_slice = flight.positions_m[1:]
                v_slice = flight.velocities_m_s[1:]
            else:
                p_slice = flight.positions_m
                v_slice = flight.velocities_m_s

            all_times.extend(phase_times.tolist())
            all_positions.append(p_slice)
            all_velocities.append(v_slice)
            current_time = float(all_times[-1])

        if flight.landing is None:
            # Did not hit ground within simulation window
            break

        bounce_count += 1
        landing_pos = np.asarray(flight.landing["position_m"], dtype=float)
        pre_vel = np.asarray(flight.landing["velocity_m_s"], dtype=float)

        post_vel, post_spin, loss = resolve_ground_impact(pre_vel, current_spin, ball, collision)

        bounces.append(BounceEvent(
            bounce_index=bounce_count,
            time_s=current_time,
            position_m=landing_pos,
            pre_velocity_m_s=pre_vel,
            post_velocity_m_s=post_vel,
            pre_speed_m_s=float(np.linalg.norm(pre_vel)),
            post_speed_m_s=float(np.linalg.norm(post_vel)),
            energy_loss_ratio=loss,
        ))

        # Check if normal rebound velocity is insufficient to keep bouncing
        if post_vel[2] < ground_rebound_threshold_vz:
            current_pos = np.array([landing_pos[0], landing_pos[1], ball.radius_m], dtype=float)
            current_vel = np.array([post_vel[0], post_vel[1], 0.0], dtype=float)
            break

        # Setup next airborne phase from contact position:
        current_pos = np.array([landing_pos[0], landing_pos[1], ball.radius_m + 1e-4], dtype=float)
        current_vel = post_vel
        current_spin = post_spin

    # Rolling phase simulation on the outfield:
    horiz_speed = float(np.hypot(current_vel[0], current_vel[1]))
    if horiz_speed > collision.stopping_velocity_tol_m_s:
        roll_dir = current_vel[:2] / horiz_speed
        # Rolling deceleration: a_roll = -mu_roll * g
        a_roll = collision.rolling_resistance_coeff * env.gravity_m_s2
        t_stop = horiz_speed / a_roll
        d_roll = 0.5 * (horiz_speed ** 2) / a_roll

        dt_roll = 0.05
        t_roll_steps = np.arange(dt_roll, t_stop + dt_roll, dt_roll)
        for tr in t_roll_steps:
            if tr > t_stop:
                tr = t_stop
            # v(t) = v0 - a*t
            v_curr = max(0.0, horiz_speed - a_roll * tr)
            # s(t) = v0*t - 0.5*a*t^2
            s_curr = horiz_speed * tr - 0.5 * a_roll * (tr ** 2)
            pos_roll = np.array([
                current_pos[0] + roll_dir[0] * s_curr,
                current_pos[1] + roll_dir[1] * s_curr,
                ball.radius_m
            ], dtype=float)
            vel_roll = np.array([
                roll_dir[0] * v_curr,
                roll_dir[1] * v_curr,
                0.0
            ], dtype=float)

            all_times.append(current_time + tr)
            all_positions.append(pos_roll.reshape(1, 3))
            all_velocities.append(vel_roll.reshape(1, 3))

            if v_curr <= collision.stopping_velocity_tol_m_s:
                break

    pos_concat = np.vstack(all_positions) if all_positions else np.array([initial_position_m])
    vel_concat = np.vstack(all_velocities) if all_velocities else np.array([initial_velocity_m_s])
    final_pos = pos_concat[-1]
    final_time = all_times[-1] if all_times else 0.0
    total_dist = float(np.hypot(final_pos[0] - initial_position_m[0], final_pos[1] - initial_position_m[1]))

    return MultiBounceResult(
        time_s=np.asarray(all_times, dtype=float),
        positions_m=pos_concat,
        velocities_m_s=vel_concat,
        bounces=bounces,
        first_bounce=bounces[0] if bounces else None,
        final_stopping_position_m=final_pos,
        final_stopping_time_s=final_time,
        total_horizontal_distance_m=total_dist,
        stopped=True,
    )

