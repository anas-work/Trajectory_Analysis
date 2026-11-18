"""
Monte Carlo uncertainty simulation for cricket ball trajectories.

Quantifies prediction confidence intervals and outcome probabilities
subject to input observation error, aerodynamic parameter uncertainty, and wind variance.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import numpy as np

from cricket_trajectory_engine.config.physics_config import (
    BallConfig,
    EnvironmentConfig,
    AerodynamicsConfig,
    FieldConfig,
    GroundCollisionConfig,
    SimulationConfig,
)
from cricket_trajectory_engine.physics.ground_collision import simulate_multi_bounce
from cricket_trajectory_engine.prediction.outcome_engine import evaluate_outcome, FielderPosition


@dataclass
class MonteCarloConfig:
    """Uncertainty perturbation settings."""
    n_simulations: int = 100
    random_seed: Optional[int] = 42
    
    # Standard deviations of Gaussian perturbations:
    std_initial_position_m: float = 0.03       # Video coordinate tracking noise (~3 cm)
    std_initial_velocity_m_s: float = 0.60     # Velocity estimation uncertainty (~0.6 m/s)
    std_drag_coefficient_cd: float = 0.025     # Aerodynamic drag uncertainty
    std_wind_speed_m_s: float = 0.50           # Ambient wind gust fluctuation (m/s)
    std_spin_rad_s: float = 5.0                # Spin rate estimation variance (rad/s)


@dataclass
class MonteCarloSummary:
    """Statistical summary of Monte Carlo trajectory ensemble."""
    n_simulations: int
    random_seed: Optional[int]
    perturbation_parameters: Dict[str, float]
    
    # Statistics: mean, std, p5, p50, p95
    landing_x_stats_m: Dict[str, float]
    landing_y_stats_m: Dict[str, float]
    horizontal_range_stats_m: Dict[str, float]
    flight_time_stats_s: Dict[str, float]
    max_height_stats_m: Dict[str, float]
    
    # Outcome probabilities:
    probability_six: float
    probability_four: float
    probability_in_field: float
    probability_catch_potential: float
    
    all_landing_positions_m: np.ndarray  # Shape (N, 2) [X, Y]
    all_ranges_m: np.ndarray             # Shape (N,)
    all_flight_times_s: np.ndarray       # Shape (N,)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n_simulations": self.n_simulations,
            "random_seed": self.random_seed,
            "perturbation_parameters": self.perturbation_parameters,
            "landing_x_stats_m": self.landing_x_stats_m,
            "landing_y_stats_m": self.landing_y_stats_m,
            "horizontal_range_stats_m": self.horizontal_range_stats_m,
            "flight_time_stats_s": self.flight_time_stats_s,
            "max_height_stats_m": self.max_height_stats_m,
            "probability_six": self.probability_six,
            "probability_four": self.probability_four,
            "probability_in_field": self.probability_in_field,
            "probability_catch_potential": self.probability_catch_potential,
        }


def _compute_stats(arr: np.ndarray) -> Dict[str, float]:
    """Helper to compute mean, std, 5th, 50th, 95th percentiles."""
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "p5": float(np.percentile(arr, 5)),
        "p50_median": float(np.median(arr)),
        "p95": float(np.percentile(arr, 95)),
    }


def run_monte_carlo_simulation(
    nominal_position_m: np.ndarray,
    nominal_velocity_m_s: np.ndarray,
    ball_config: Optional[BallConfig] = None,
    env_config: Optional[EnvironmentConfig] = None,
    aero_config: Optional[AerodynamicsConfig] = None,
    field_config: Optional[FieldConfig] = None,
    collision_config: Optional[GroundCollisionConfig] = None,
    sim_config: Optional[SimulationConfig] = None,
    mc_config: Optional[MonteCarloConfig] = None,
    fielders: Optional[List[FielderPosition]] = None,
) -> MonteCarloSummary:
    """
    Runs Monte Carlo ensemble simulation to assess sensitivity and prediction confidence.
    """
    ball = ball_config or BallConfig()
    env = env_config or EnvironmentConfig()
    aero = aero_config or AerodynamicsConfig()
    field_cfg = field_config or FieldConfig()
    collision = collision_config or GroundCollisionConfig()
    sim = sim_config or SimulationConfig()
    mc = mc_config or MonteCarloConfig()

    rng = np.random.default_rng(mc.random_seed)

    pos_nom = np.asarray(nominal_position_m, dtype=float)
    vel_nom = np.asarray(nominal_velocity_m_s, dtype=float)
    wind_nom = np.asarray(env.wind_vector_m_s, dtype=float)
    spin_nom = np.asarray(aero.spin_rad_s, dtype=float)

    landing_xs: List[float] = []
    landing_ys: List[float] = []
    ranges: List[float] = []
    flight_times: List[float] = []
    max_heights: List[float] = []

    count_six = 0
    count_four = 0
    count_in_field = 0
    count_catch = 0

    for _ in range(mc.n_simulations):
        # 1. Perturb initial position:
        pos_pert = pos_nom + rng.normal(0.0, mc.std_initial_position_m, size=3)
        pos_pert[2] = max(ball.radius_m + 0.05, pos_pert[2])

        # 2. Perturb initial velocity:
        vel_pert = vel_nom + rng.normal(0.0, mc.std_initial_velocity_m_s, size=3)

        # 3. Perturb drag coefficient:
        cd_pert = max(0.15, min(0.60, float(rng.normal(aero.constant_cd, mc.std_drag_coefficient_cd))))
        aero_pert = AerodynamicsConfig(
            drag_model=aero.drag_model,
            constant_cd=cd_pert,
            enable_magnus=aero.enable_magnus,
            magnus_model=aero.magnus_model,
            constant_cl=aero.constant_cl,
            spin_rad_s=aero.spin_rad_s,
        )

        # 4. Perturb wind:
        wind_pert = wind_nom + rng.normal(0.0, mc.std_wind_speed_m_s, size=3)
        env_pert = EnvironmentConfig(
            air_density_kg_m3=env.air_density_kg_m3,
            dynamic_viscosity_pa_s=env.dynamic_viscosity_pa_s,
            gravity_m_s2=env.gravity_m_s2,
            wind_vector_m_s=(float(wind_pert[0]), float(wind_pert[1]), float(wind_pert[2])),
        )

        # 5. Perturb spin if Magnus enabled:
        spin_pert = spin_nom
        if aero.enable_magnus:
            spin_pert = spin_nom + rng.normal(0.0, mc.std_spin_rad_s, size=3)

        # Run multi-bounce simulation:
        res = simulate_multi_bounce(
            initial_position_m=pos_pert,
            initial_velocity_m_s=vel_pert,
            ball_config=ball,
            env_config=env_pert,
            aero_config=aero_pert,
            collision_config=collision,
            sim_config=sim,
            spin_rad_s=spin_pert,
        )

        outcome = evaluate_outcome(res, field_config=field_cfg, fielders=fielders)

        first_b = res.first_bounce
        p_land = first_b.position_m if first_b else res.positions_m[-1]
        t_land = first_b.time_s if first_b else res.final_stopping_time_s
        r_horiz = float(np.hypot(p_land[0] - pos_pert[0], p_land[1] - pos_pert[1]))

        landing_xs.append(float(p_land[0]))
        landing_ys.append(float(p_land[1]))
        ranges.append(r_horiz)
        flight_times.append(float(t_land))
        max_heights.append(float(np.max(res.positions_m[:, 2])))

        if outcome.primary_call == "SIX":
            count_six += 1
        elif outcome.primary_call == "FOUR":
            count_four += 1
        elif outcome.primary_call == "POTENTIAL_CATCH":
            count_catch += 1
            count_in_field += 1
        else:
            count_in_field += 1

    n = mc.n_simulations
    xs_arr = np.array(landing_xs)
    ys_arr = np.array(landing_ys)
    r_arr = np.array(ranges)
    ft_arr = np.array(flight_times)
    mh_arr = np.array(max_heights)

    return MonteCarloSummary(
        n_simulations=n,
        random_seed=mc.random_seed,
        perturbation_parameters={
            "std_initial_position_m": mc.std_initial_position_m,
            "std_initial_velocity_m_s": mc.std_initial_velocity_m_s,
            "std_drag_coefficient_cd": mc.std_drag_coefficient_cd,
            "std_wind_speed_m_s": mc.std_wind_speed_m_s,
            "std_spin_rad_s": mc.std_spin_rad_s,
        },
        landing_x_stats_m=_compute_stats(xs_arr),
        landing_y_stats_m=_compute_stats(ys_arr),
        horizontal_range_stats_m=_compute_stats(r_arr),
        flight_time_stats_s=_compute_stats(ft_arr),
        max_height_stats_m=_compute_stats(mh_arr),
        probability_six=float(count_six / n),
        probability_four=float(count_four / n),
        probability_in_field=float(count_in_field / n),
        probability_catch_potential=float(count_catch / n),
        all_landing_positions_m=np.column_stack((xs_arr, ys_arr)),
        all_ranges_m=r_arr,
        all_flight_times_s=ft_arr,
    )

