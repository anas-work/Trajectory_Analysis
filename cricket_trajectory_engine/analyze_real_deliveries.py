"""
Analyzes all 10 real deliveries from 3d_hits_10_deliveries:
1. Loads 3D coordinates tracked by the dual-camera stereo system.
2. Estimates initial physical state (velocity vector, launch speed, elevation, azimuth).
3. Fits the physics model to the initial post-bat frames.
4. Predicts the complete unconstrained open-field trajectory (flight, bounces, rolling).
5. Evaluates cricket outcome (Four, Catch, In-Play) and post-bounce rope clearance.
6. Generates 3D Hawkeye stadium visual and video demonstration for real deliveries.
"""

import os
import sys
import numpy as np

# Ensure root directory is on PYTHONPATH:
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cricket_trajectory_engine.config.physics_config import (
    BallConfig,
    EnvironmentConfig,
    AerodynamicsConfig,
    GroundCollisionConfig,
    FieldConfig,
)
from cricket_trajectory_engine.estimation.real_delivery_loader import (
    list_available_real_deliveries,
    load_real_delivery_bat_trajectory,
)
from cricket_trajectory_engine.estimation.velocity_estimator import (
    estimate_initial_state,
    compute_launch_angles,
)
from cricket_trajectory_engine.estimation.trajectory_fitting import (
    fit_trajectory_to_observations,
)
from cricket_trajectory_engine.physics.ground_collision import simulate_multi_bounce
from cricket_trajectory_engine.prediction.field_geometry import CricketField
from cricket_trajectory_engine.prediction.outcome_engine import (
    evaluate_outcome,
    FielderPosition,
)
from cricket_trajectory_engine.visualization.cricket_ground_renderer import (
    render_cricket_stadium_trajectory,
    get_standard_cricket_fielders,
)
from cricket_trajectory_engine.visualization.video_generator import generate_single_video_animation


def analyze_all_real_deliveries(output_dir: str = "cricket_trajectory_engine/data/generated_trajectories"):
    os.makedirs(output_dir, exist_ok=True)
    delivery_folders = list_available_real_deliveries()
    
    print("=" * 80)
    print(f"ANALYSIS OF {len(delivery_folders)} REAL DELIVERIES (DUAL-CAMERA STEREO 3D TRACKING)")
    print("=" * 80)
    
    ball = BallConfig()
    env = EnvironmentConfig()
    aero = AerodynamicsConfig(constant_cd=0.32)
    field_cfg = FieldConfig(boundary_radius_m=70.0)
    field_obj = CricketField(field_cfg)
    fielders = get_standard_cricket_fielders()
    
    summary_results = []
    
    for folder in delivery_folders:
        try:
            deliv = load_real_delivery_bat_trajectory(folder)
            obs = deliv.observations
            
            # Initial state estimation:
            est = estimate_initial_state(obs, method="polynomial", polynomial_order=2)
            
            # Use the first 6-10 frames (initial post-bat launch window before net contact):
            n_fit = min(10, obs.count)
            obs_fit = obs.slice(0, n_fit)
            fit_res = fit_trajectory_to_observations(obs_fit, fit_drag_coefficient=False)
            
            p0 = obs_fit.positions_m[0]
            v0 = fit_res.optimized_velocity_m_s
            speed = np.linalg.norm(v0)
            
            # Unconstrained open-field simulation:
            res_sim = simulate_multi_bounce(p0, v0, ball, env, aero)
            outcome = evaluate_outcome(res_sim, field_cfg, fielders)
            
            first_bounce_d = np.hypot(res_sim.bounces[0].position_m[0], res_sim.bounces[0].position_m[1]) if res_sim.bounces else 0.0
            
            summary_results.append({
                "folder": deliv.folder_name,
                "n_obs": obs.count,
                "speed_kmh": speed * 3.6,
                "launch_deg": est.elevation_angle_deg,
                "azim_deg": est.azimuth_angle_deg,
                "first_pitch_m": first_bounce_d,
                "total_dist_m": res_sim.total_horizontal_distance_m,
                "outcome": outcome.primary_call,
                "rope_summary": outcome.rope_clearance.summary,
                "deliv": deliv,
                "res_sim": res_sim,
                "outcome_obj": outcome,
            })
            
            print(f"\n[{deliv.folder_name}]")
            print(f"  Valid 3D Points:       {obs.count} frames")
            print(f"  Launch Speed:          {speed * 3.6:.1f} km/h ({speed:.2f} m/s)")
            print(f"  Launch Elevation:      {est.elevation_angle_deg:.1f}° | Azimuth: {est.azimuth_angle_deg:.1f}°")
            print(f"  Carry / 1st Bounce:    {first_bounce_d:.1f} m")
            print(f"  Total Open Field Dist: {res_sim.total_horizontal_distance_m:.1f} m")
            print(f"  Predicted Outcome:     [{outcome.primary_call}] - {outcome.rope_clearance.summary}")
            
        except Exception as e:
            print(f"Error analyzing {folder}: {e}")
            
    # Highlight top real shots for visuals and video:
    # 1. Delivery 03: Crisp fast drive down the ground (55.6 km/h)
    # 2. Delivery 09: High lofted shot (46.0 km/h, 37.3 deg launch)
    for target_prefix, desc in [("03_", "Real Shot 03 (Crisp Drive 55.6 km/h)"), ("09_", "Real Shot 09 (Lofted Skyer 46.0 km/h)")]:
        match = [s for s in summary_results if s["folder"].startswith(target_prefix)]
        if match:
            s = match[0]
            stadium_path = os.path.join(output_dir, f"real_delivery_{target_prefix[:2]}_stadium_3d.png")
            render_cricket_stadium_trajectory(
                s["res_sim"], s["outcome_obj"], field_obj, fielders,
                title=f"{desc} - Unconstrained Open Field Prediction",
                filename=stadium_path,
            )
            print(f"\nRendered 3D Stadium Projection for {desc}: {stadium_path}")
            
            # Generate Video for Delivery 03:
            if target_prefix == "03_":
                vid_mp4 = os.path.join(output_dir, "video_real_delivery_03.mp4")
                vid_gif = os.path.join(output_dir, "video_real_delivery_03.gif")
                generate_single_video_animation(
                    s["res_sim"],
                    outcome=s["outcome_obj"],
                    field=field_obj,
                    fielders=fielders,
                    output_mp4_path=vid_mp4,
                    output_gif_path=vid_gif,
                    scenario_title="Real Tracked Delivery 03 - Open Field Hawkeye",
                )
                print(f"Generated Video Demo for Real Delivery 03: {vid_mp4}")


if __name__ == "__main__":
    analyze_all_real_deliveries()
