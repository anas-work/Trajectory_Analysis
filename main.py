"""
Main demonstration runner for the Cricket Ball 3D Flight Trajectory Prediction Engine.

Executes:
1. Authentic cricket ground demonstrations (Pitch, Wickets, 30-yard ring, Boundary rope).
2. Post-bounce boundary rope clearance modeling (Clearing rope for Four vs Pulling up short).
3. Video demonstration of 3D trajectory arc from bat impact, velocity HUD, and bounce.
4. Aerodynamic comparisons (Vacuum ballistic vs Drag vs Magnus spin).
5. Coordinate loading, velocity estimation, and least-squares trajectory fitting.
6. Monte Carlo ensemble simulation with landing dispersion plots.
"""

import os
import sys
import argparse
import csv
import numpy as np

# Ensure root directory is on PYTHONPATH:
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cricket_trajectory_engine.config.physics_config import (
    BallConfig,
    EnvironmentConfig,
    AerodynamicsConfig,
    GroundCollisionConfig,
    FieldConfig,
    SimulationConfig,
)
from cricket_trajectory_engine.physics.flight_simulator import simulate_flight
from cricket_trajectory_engine.physics.ground_collision import simulate_multi_bounce
from cricket_trajectory_engine.estimation.coordinate_loader import (
    load_observations_from_csv,
    generate_synthetic_observations,
)
from cricket_trajectory_engine.estimation.velocity_estimator import (
    estimate_initial_state,
    compute_launch_angles,
)
from cricket_trajectory_engine.estimation.trajectory_fitting import (
    fit_trajectory_to_observations,
)
from cricket_trajectory_engine.prediction.field_geometry import CricketField
from cricket_trajectory_engine.prediction.outcome_engine import (
    evaluate_outcome,
    FielderPosition,
)
from cricket_trajectory_engine.prediction.uncertainty import (
    MonteCarloConfig,
    run_monte_carlo_simulation,
)
from cricket_trajectory_engine.visualization.trajectory_plots import (
    plot_3d_trajectory,
    plot_trajectory_views,
    plot_comparative_physics,
    plot_monte_carlo_distribution,
)
from cricket_trajectory_engine.visualization.cricket_ground_renderer import (
    render_cricket_stadium_trajectory,
    get_standard_cricket_fielders,
)
from cricket_trajectory_engine.visualization.video_generator import (
    generate_trajectory_video,
    generate_presentation_video_suite,
)


def export_trajectory_csv(times: np.ndarray, positions: np.ndarray, velocities: np.ndarray, filepath: str) -> None:
    """Exports trajectory time-series to CSV."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)) or ".", exist_ok=True)
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time_s", "x_m", "y_m", "z_m", "vx_m_s", "vy_m_s", "vz_m_s"])
        for t, p, v in zip(times, positions, velocities):
            writer.writerow([
                f"{t:.4f}",
                f"{p[0]:.4f}", f"{p[1]:.4f}", f"{p[2]:.4f}",
                f"{v[0]:.4f}", f"{v[1]:.4f}", f"{v[2]:.4f}"
            ])


def run_scenarios(output_dir: str):
    """Runs distinct cricket shot scenarios styled for a real cricket stadium."""
    print("=" * 80)
    print("PHASE 5: RUNNING AUTHENTIC CRICKET STADIUM SHOT DEMONSTRATIONS")
    print("=" * 80)

    ball = BallConfig(mass_kg=0.160, diameter_m=0.0725)
    env = EnvironmentConfig(air_density_kg_m3=1.225, gravity_m_s2=9.80665)
    aero = AerodynamicsConfig(constant_cd=0.32, enable_magnus=False)
    field_cfg = FieldConfig(boundary_radius_m=70.0)
    field_obj = CricketField(field_cfg)
    fielders = get_standard_cricket_fielders()

    scenarios = [
        {
            "id": 1,
            "name": "Scenario 1: Cover Drive (Clearing Rope for FOUR)",
            "pos0": np.array([0.0, 0.0, 0.85]),
            "vel0": np.array([28.0, 10.0, 6.2]),  # Speed ~30.4 m/s (109 km/h), Launch ~11.8 deg, Azimuth ~19.7 deg
            "desc": "Crisply timed cover drive that pitches at 41m, rolls on the turf, and clears the rope for Four.",
        },
        {
            "id": 2,
            "name": "Scenario 2: High-Lofted Shot (Clearing Rope on Full for SIX)",
            "pos0": np.array([0.0, 0.0, 1.10]),
            "vel0": np.array([30.0, 1.5, 20.0]),  # Speed ~36.1 m/s (130 km/h), Launch ~33.7 deg
            "desc": "Lofted shot clearing the outfield and sailing over the 70m rope on the full.",
        },
        {
            "id": 3,
            "name": "Scenario 3: Controlled Push (Pulling Up Short of Rope - 2 Runs)",
            "pos0": np.array([0.0, 0.0, 0.90]),
            "vel0": np.array([22.0, 8.0, 5.0]),   # Speed ~23.9 m/s (86 km/h)
            "desc": "Controlled push through mid-wicket that pitches at 30m, decelerates on grass, and stops 13m short of rope.",
        },
    ]

    for sc in scenarios:
        sid = sc["id"]
        p0 = sc["pos0"]
        v0 = sc["vel0"]
        speed0, elev0, azim0 = compute_launch_angles(v0)

        print(f"\n--- {sc['name']} ---")
        print(f"Description: {sc['desc']}")
        print(f"Initial Velocity: Vx={v0[0]:.2f}m/s, Vy={v0[1]:.2f}m/s, Vz={v0[2]:.2f}m/s")
        print(f"Speed: {speed0:.2f} m/s ({speed0 * 3.6:.1f} km/h) | Launch Angle: {elev0:.2f}° | Azimuth: {azim0:.2f}°")

        res_flight = simulate_flight(p0, v0, ball, env, aero)
        res_multibounce = simulate_multi_bounce(p0, v0, ball, env, aero)
        outcome = evaluate_outcome(res_multibounce, field_config=field_cfg, fielders=fielders)

        print(f"Flight Time to First Contact: {res_flight.flight_time_s:.3f} s")
        print(f"Maximum Height (Apex): {res_flight.max_height_m:.2f} m")
        first_p = res_flight.landing["position_m"] if res_flight.landing else res_flight.positions_m[-1]
        print(f"First Landing Position: X={first_p[0]:.2f}m, Y={first_p[1]:.2f}m, Z={first_p[2]:.2f}m")
        print(f"Horizontal Carry Distance: {res_flight.horizontal_range_m:.2f} m")
        print(f"Total Multi-Bounce Bounces: {len(res_multibounce.bounces)} | Total Ground Distance: {res_multibounce.total_horizontal_distance_m:.2f} m")
        print(f"Match Outcome: [{outcome.primary_call}] - Runs: {outcome.estimated_runs}")
        print(f"Rope Clearance Modeling: {outcome.rope_clearance.summary}")

        # Save CSV:
        csv_path = os.path.join(output_dir, f"scenario_{sid}_trajectory.csv")
        export_trajectory_csv(res_multibounce.time_s, res_multibounce.positions_m, res_multibounce.velocities_m_s, csv_path)

        # 3D Cricket Stadium visualization with pitch and boundary rope:
        stadium_plot_path = os.path.join(output_dir, f"scenario_{sid}_stadium_3d.png")
        render_cricket_stadium_trajectory(
            res_multibounce, outcome, field_obj, fielders,
            title=f"{sc['name']} - Hawkeye 3D",
            filename=stadium_plot_path,
        )

        plot_views_path = os.path.join(output_dir, f"scenario_{sid}_views.png")
        plot_trajectory_views(res_multibounce, field_obj, filename=plot_views_path)
        print(f"Generated Stadium Visual: {stadium_plot_path}")


def run_rope_clearance_demonstration(output_dir: str):
    """Demonstrates post-bounce boundary rope clearance modeling."""
    print("\n" + "=" * 80)
    print("MODELING POST-BOUNCE BOUNDARY ROPE CLEARANCE (FOUR vs PULLED UP SHORT)")
    print("=" * 80)

    ball = BallConfig()
    env = EnvironmentConfig()
    aero = AerodynamicsConfig(constant_cd=0.32)
    field_cfg = FieldConfig(boundary_radius_m=70.0)
    field_obj = CricketField(field_cfg)

    # Shot A: Driven hard, pitches at ~41m, has enough residual momentum to cross 70m rope
    v_four = np.array([29.0, 8.0, 6.0])
    res_four = simulate_multi_bounce(np.array([0, 0, 0.85]), v_four, ball, env, aero)
    outcome_four = evaluate_outcome(res_four, field_cfg)

    # Shot B: Pushed gently, pitches at ~30m, rolls and decelerates, stops 14m short of rope
    v_short = np.array([21.0, 5.0, 5.0])
    res_short = simulate_multi_bounce(np.array([0, 0, 0.85]), v_short, ball, env, aero)
    outcome_short = evaluate_outcome(res_short, field_cfg)

    print("\nCase A: Driven with sufficient pace to clear the rope (FOUR):")
    print(f"  Initial Speed:      {np.linalg.norm(v_four):.1f} m/s ({np.linalg.norm(v_four)*3.6:.0f} km/h)")
    print(f"  Pitch / 1st Bounce: {outcome_four.rope_clearance.first_impact_distance_m:.1f} m (Remaining to rope: {outcome_four.rope_clearance.distance_remaining_to_rope_m:.1f} m)")
    print(f"  Min Speed Required: {outcome_four.rope_clearance.minimum_speed_required_m_s:.1f} m/s")
    print(f"  Post-Bounce Roll:   {outcome_four.rope_clearance.post_bounce_distance_travelled_m:.1f} m")
    print(f"  Residual at Rope:   {outcome_four.rope_clearance.residual_speed_at_rope_m_s:.1f} m/s ({outcome_four.rope_clearance.residual_speed_at_rope_m_s*3.6:.1f} km/h)")
    print(f"  Call:               [{outcome_four.primary_call}] - {outcome_four.rope_clearance.summary}")

    print("\nCase B: Pushed with lower pace, pulling up short of rope (2 Runs):")
    print(f"  Initial Speed:      {np.linalg.norm(v_short):.1f} m/s ({np.linalg.norm(v_short)*3.6:.0f} km/h)")
    print(f"  Pitch / 1st Bounce: {outcome_short.rope_clearance.first_impact_distance_m:.1f} m (Remaining to rope: {outcome_short.rope_clearance.distance_remaining_to_rope_m:.1f} m)")
    print(f"  Min Speed Required: {outcome_short.rope_clearance.minimum_speed_required_m_s:.1f} m/s")
    print(f"  Post-Bounce Roll:   {outcome_short.rope_clearance.post_bounce_distance_travelled_m:.1f} m")
    print(f"  Stopped At:         {outcome_short.physics_facts['total_horizontal_distance_m']:.1f} m ({abs(outcome_short.rope_clearance.margin_m):.1f} m short of rope)")
    print(f"  Call:               [{outcome_short.primary_call}] - {outcome_short.rope_clearance.summary}")


def run_video_generation(output_dir: str):
    """Generates the full presentation video suite across 4 different input scenarios (MP4 & GIF)."""
    print("\n" + "=" * 80)
    print("GENERATING PRESENTATION VIDEO SUITE AT DIFFERENT INPUT VALUES (MP4 & GIF)")
    print("=" * 80)

    video_results = generate_presentation_video_suite(output_dir)

    for vid_id, files in video_results.items():
        print(f"\n[Generated Video: {vid_id}]")
        print(f"  * MP4 Video:    {files['mp4']}")
        if "gif" in files:
            print(f"  * Animated GIF: {files['gif']}")


def run_aero_comparison(output_dir: str):
    """Compares vacuum ballistic, drag, and Magnus lift/dip."""
    print("\n" + "=" * 80)
    print("PHASE 5/7: AERODYNAMIC COMPARISON (VACUUM vs DRAG vs MAGNUS SPIN)")
    print("=" * 80)

    ball = BallConfig()
    env = EnvironmentConfig()

    p0 = np.array([0.0, 0.0, 1.2])
    v0 = np.array([30.0, 0.0, 16.0])

    res_vac = simulate_flight(p0, v0, ball, env, gravity_only=True)
    aero_drag = AerodynamicsConfig(constant_cd=0.32, enable_magnus=False)
    res_drag = simulate_flight(p0, v0, ball, env, aero_drag)
    aero_top = AerodynamicsConfig(constant_cd=0.32, enable_magnus=True, constant_cl=0.15, spin_rad_s=(0.0, 150.0, 0.0))
    res_top = simulate_flight(p0, v0, ball, env, aero_top)
    aero_back = AerodynamicsConfig(constant_cd=0.32, enable_magnus=True, constant_cl=0.15, spin_rad_s=(0.0, -150.0, 0.0))
    res_back = simulate_flight(p0, v0, ball, env, aero_back)

    print(f"Case 1 (Vacuum):        Carry = {res_vac.horizontal_range_m:6.2f} m | Apex = {res_vac.max_height_m:5.2f} m | Flight Time = {res_vac.flight_time_s:5.2f} s")
    print(f"Case 2 (Gravity + Drag):Carry = {res_drag.horizontal_range_m:6.2f} m | Apex = {res_drag.max_height_m:5.2f} m | Flight Time = {res_drag.flight_time_s:5.2f} s")
    print(f"Case 3 (Drag + Topspin):Carry = {res_top.horizontal_range_m:6.2f} m | Apex = {res_top.max_height_m:5.2f} m | Flight Time = {res_top.flight_time_s:5.2f} s (Dip)")
    print(f"Case 4 (Drag + Backspin):Carry = {res_back.horizontal_range_m:6.2f} m | Apex = {res_back.max_height_m:5.2f} m | Flight Time = {res_back.flight_time_s:5.2f} s (Lift)")

    comp_plot_path = os.path.join(output_dir, "comparative_aerodynamics.png")
    plot_comparative_physics(res_vac, res_drag, res_top, res_back, filename=comp_plot_path)
    print(f"Wrote Comparative Plot: {comp_plot_path}")


def run_estimation_and_fitting(output_dir: str):
    """Demonstrates state estimation and least-squares trajectory fitting."""
    print("\n" + "=" * 80)
    print("PHASE 3 & 6: INITIAL STATE ESTIMATION & LEAST-SQUARES TRAJECTORY FITTING")
    print("=" * 80)

    dummy_csv = "cricket_trajectory_engine/data/dummy_observations.csv"
    obs_dummy = load_observations_from_csv(dummy_csv)
    print(f"Loaded {obs_dummy.count} dummy observation coordinates from {dummy_csv}:")

    est_dummy = estimate_initial_state(obs_dummy, method="polynomial", polynomial_order=2)
    print("\nKinematic State Estimation on Dummy Data:")
    print(f"  Estimated Initial Pos:  {np.round(est_dummy.initial_position_m, 3).tolist()} m")
    print(f"  Estimated Initial Vel:  {np.round(est_dummy.initial_velocity_m_s, 2).tolist()} m/s")
    print(f"  Estimated Launch Speed: {est_dummy.initial_speed_m_s:.2f} m/s ({est_dummy.initial_speed_m_s * 3.6:.1f} km/h)")
    print(f"  Elevation Launch Angle: {est_dummy.elevation_angle_deg:.2f}° | Azimuth: {est_dummy.azimuth_angle_deg:.2f}°")
    print(f"  Position Fit RMSE:      Total = {est_dummy.position_fit_rmse_m['total']*1000:.2f} mm")

    fit_res = fit_trajectory_to_observations(obs_dummy, fit_drag_coefficient=False)
    print("\nPhysics-Based Least-Squares Optimization Result:")
    print(f"  Optimized Initial Vel:  {np.round(fit_res.optimized_velocity_m_s, 2).tolist()} m/s")
    print(f"  Optimized Speed:        {fit_res.optimized_speed_m_s:.2f} m/s")
    print(f"  Optimized Elevation:    {fit_res.elevation_angle_deg:.2f}°")
    print(f"  Convergence Success:    {fit_res.convergence_success} ({fit_res.status_message})")
    print(f"  Trajectory Fit RMSE:    Total = {fit_res.total_rmse_m*1000:.2f} mm")


def run_monte_carlo(output_dir: str):
    """Runs Monte Carlo ensemble simulation to quantify uncertainty."""
    print("\n" + "=" * 80)
    print("PHASE 9: MONTE CARLO TRAJECTORY UNCERTAINTY QUANTIFICATION")
    print("=" * 80)

    p0 = np.array([0.0, 0.0, 1.1])
    v0 = np.array([31.0, 1.0, 18.0])

    mc_cfg = MonteCarloConfig(n_simulations=150, random_seed=42)
    mc_summary = run_monte_carlo_simulation(p0, v0, mc_config=mc_cfg)

    print(f"Simulated {mc_summary.n_simulations} perturbed shots (Seed={mc_summary.random_seed})")
    print(f"  Carry Range (m):Mean={mc_summary.horizontal_range_stats_m['mean']:.2f} ± {mc_summary.horizontal_range_stats_m['std']:.2f} | 5th-95th: [{mc_summary.horizontal_range_stats_m['p5']:.2f}, {mc_summary.horizontal_range_stats_m['p95']:.2f}]")
    print(f"  Outcome Probabilities: P(Six)={mc_summary.probability_six*100:.1f}%, P(Four)={mc_summary.probability_four*100:.1f}%, P(In-Field)={mc_summary.probability_in_field*100:.1f}%")

    mc_plot_path = os.path.join(output_dir, "monte_carlo_dispersion.png")
    plot_monte_carlo_distribution(mc_summary, CricketField(), filename=mc_plot_path)


def main():
    parser = argparse.ArgumentParser(description="3D Cricket Ball Trajectory Prediction Engine")
    parser.add_argument("--all", action="store_true", help="Run all demonstrations, video, and validations")
    parser.add_argument("--scenarios", action="store_true", help="Run cricket stadium shot scenarios")
    parser.add_argument("--rope-clearance", action="store_true", help="Demonstrate post-bounce rope clearance")
    parser.add_argument("--video", action="store_true", help="Generate trajectory video demo (MP4 and GIF)")
    parser.add_argument("--compare-aero", action="store_true", help="Run aerodynamic comparison")
    parser.add_argument("--fit", action="store_true", help="Run state estimation and fitting")
    parser.add_argument("--monte-carlo", action="store_true", help="Run Monte Carlo uncertainty")
    parser.add_argument("--output-dir", default="cricket_trajectory_engine/data/generated_trajectories", help="Directory for generated plots & videos")

    args = parser.parse_args()

    run_all = args.all or not (args.scenarios or args.rope_clearance or args.video or args.compare_aero or args.fit or args.monte_carlo)

    os.makedirs(args.output_dir, exist_ok=True)

    if run_all or args.scenarios:
        run_scenarios(args.output_dir)

    if run_all or args.rope_clearance:
        run_rope_clearance_demonstration(args.output_dir)

    if run_all or args.video:
        run_video_generation(args.output_dir)

    if run_all or args.compare_aero:
        run_aero_comparison(args.output_dir)

    if run_all or args.fit:
        run_estimation_and_fitting(args.output_dir)

    if run_all or args.monte_carlo:
        run_monte_carlo(args.output_dir)

    print("\n" + "=" * 80)
    print("ALL DEMONSTRATIONS, VIDEO, AND VISUALS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
