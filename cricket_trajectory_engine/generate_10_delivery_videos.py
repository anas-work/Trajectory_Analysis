"""
Batch processor and video generator for all 10 deliveries in 3d_hits_10_deliveries:
Generates 2 output videos for each delivery (1 for cam1, 1 for cam2) -> Total 20 videos!

Displays on every video:
- Input values used from each camera's tracking data (camera name, frame count, measured velocities)
- Extra physical values added by the simulation pipeline (mass, drag, restitution, turf friction)
- Predicted results (pitch carry, apex, rollout, rope clearance, cricket outcome)
"""

import os
import sys
import csv
import shutil
import numpy as np
from typing import Dict, Any, List

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
    get_standard_cricket_fielders,
    render_cricket_stadium_trajectory,
)
from cricket_trajectory_engine.visualization.video_generator import generate_single_video_animation


def load_summary_dict(summary_csv_path: str = "3d_hits_10_deliveries/summary.csv") -> Dict[str, Dict[str, Any]]:
    """Loads summary.csv keyed by folder name."""
    summary_map = {}
    if not os.path.exists(summary_csv_path):
        return summary_map
    with open(summary_csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            d_name = row.get("delivery", "").strip()
            summary_map[d_name] = row
    return summary_map


def process_all_deliveries_multi_cam(
    output_dir: str = "cricket_trajectory_engine/data/real_deliveries_videos",
    artifact_dir: str = "/Users/anasazizkhan/.gemini/antigravity/brain/c7d45dd8-82af-4bc7-89b2-0c45307e09ab",
):
    os.makedirs(output_dir, exist_ok=True)
    summary_map = load_summary_dict()
    delivery_folders = list_available_real_deliveries()

    print("=" * 90)
    print(f"PROCESSING 10 DELIVERIES ACROSS BOTH CAMERAS (CAM1 & CAM2) -> 20 OUTPUT VIDEOS")
    print("=" * 90)

    # Standard physical parameters:
    ball = BallConfig(mass_kg=0.160, diameter_m=0.0725)
    env = EnvironmentConfig(air_density_kg_m3=1.225, gravity_m_s2=9.80665)
    aero = AerodynamicsConfig(constant_cd=0.32, enable_magnus=False)
    collision = GroundCollisionConfig(restitution_normal=0.55, friction_tangential=0.38, rolling_resistance_coeff=0.20)
    field_cfg = FieldConfig(boundary_radius_m=70.0)
    field_obj = CricketField(field_cfg)
    fielders = get_standard_cricket_fielders()

    all_results = []
    total_runs = len(delivery_folders) * 2
    current_run = 0

    for f_idx, folder in enumerate(delivery_folders, 1):
        deliv_id = os.path.basename(folder).split("_")[0]
        folder_base = os.path.basename(folder)
        meta_row = summary_map.get(folder_base, {})

        for cam in ["cam1", "cam2"]:
            current_run += 1
            print(f"\n[{current_run}/{total_runs}] Processing Delivery {deliv_id} - Camera {cam.upper()}: {folder_base}")

            try:
                # 1. Load tracked observations for this camera:
                deliv_data = load_real_delivery_bat_trajectory(folder, camera=cam)
                obs = deliv_data.observations

                # 2. Fit initial launch state from the post-bat launch frames:
                n_fit = min(10, obs.count)
                obs_fit = obs.slice(0, n_fit)
                est = estimate_initial_state(obs_fit, method="polynomial", polynomial_order=2)
                fit_res = fit_trajectory_to_observations(obs_fit, fit_drag_coefficient=False)

                p0 = obs_fit.positions_m[0]
                v0 = fit_res.optimized_velocity_m_s
                speed0 = float(np.linalg.norm(v0))
                elev0 = est.elevation_angle_deg
                azim0 = est.azimuth_angle_deg

                # 3. Simulate unconstrained open-field trajectory:
                res_sim = simulate_multi_bounce(p0, v0, ball, env, aero, collision)
                outcome = evaluate_outcome(res_sim, field_cfg, fielders)

                d1 = float(np.hypot(res_sim.bounces[0].position_m[0], res_sim.bounces[0].position_m[1])) if res_sim.bounces else 0.0
                t_pitch = float(res_sim.bounces[0].time_s) if res_sim.bounces else float(res_sim.time_s[-1])
                apex_h = float(np.max(res_sim.positions_m[:, 2]))
                total_dist = float(res_sim.total_horizontal_distance_m)
                d_roll = float(outcome.rope_clearance.post_bounce_distance_travelled_m)

                # Rope clearance string:
                if outcome.rope_clearance.clears_rope:
                    v_rope = outcome.rope_clearance.residual_speed_at_rope_m_s or 0.0
                    rope_str = f"Cleared (+{v_rope*3.6:.0f} km/h)"
                else:
                    margin = abs(outcome.rope_clearance.margin_m)
                    rope_str = f"{margin:.1f}m short of rope"

                # Bowler & bat-hit speeds from summary.csv:
                bowler_v = meta_row.get("pipeline_pre_bounce_final_speed_kmh", "N/A")
                bat_v = meta_row.get("bat_hit_fit_y_speed_kmh", "N/A")
                if bat_v != "N/A":
                    try:
                        bat_v = f"{abs(float(bat_v)):.1f}"
                    except ValueError:
                        pass
                if bowler_v != "N/A":
                    try:
                        bowler_v = f"{float(bowler_v):.1f}"
                    except ValueError:
                        pass

                # Camera-specific window info:
                cam_window = meta_row.get(f"{cam}_window", "N/A")
                cam_hit_frame = meta_row.get(f"{cam}_hit_session_frame", "N/A")

                # 4. Visible video metadata:
                video_metadata = {
                    "input_data": {
                        "delivery_id": f"Del #{deliv_id} [{cam.upper()}] (Rank {meta_row.get('rank', f_idx)})",
                        "bowler_speed_kmh": bowler_v,
                        "bat_hit_speed_kmh": bat_v,
                        "n_points": obs.count,
                        "v0_str": f"[{v0[0]:.2f}, {v0[1]:.2f}, {v0[2]:.2f}]",
                        "launch_speed_kmh": f"{speed0*3.6:.1f}",
                        "elevation_deg": f"{elev0:+.1f}",
                        "azimuth_deg": f"{azim0:+.1f}",
                    },
                    "pipeline_params": {
                        "mass_dia": f"{ball.mass_kg*1000:.0f}g / {ball.diameter_m*1000:.1f}mm",
                        "air_gravity": f"{env.air_density_kg_m3:.3f} kg/m³ | {env.gravity_m_s2:.2f} m/s²",
                        "cd": f"{aero.constant_cd:.2f}",
                        "spin_model": "Disabled (baseline)",
                        "en": f"{collision.restitution_normal:.2f}",
                        "mu_t": f"{collision.friction_tangential:.2f}",
                        "mu_roll": f"{collision.rolling_resistance_coeff:.2f}",
                        "boundary_r": f"{field_cfg.boundary_radius_m:.1f} m",
                    },
                    "results_data": {
                        "t_pitch": f"{t_pitch:.2f}",
                        "d_pitch": f"{d1:.1f}",
                        "apex": f"{apex_h:.2f}",
                        "d_roll": f"{d_roll:.1f}",
                        "d_total": f"{total_dist:.1f}",
                        "rope_clearance": rope_str,
                        "outcome_call": outcome.primary_call,
                    },
                }

                # 5. Output file paths:
                mp4_filename = f"delivery_{deliv_id}_{cam}_prediction.mp4"
                gif_filename = f"delivery_{deliv_id}_{cam}_prediction.gif"
                png_filename = f"delivery_{deliv_id}_{cam}_stadium_3d.png"

                mp4_path = os.path.join(output_dir, mp4_filename)
                gif_path = os.path.join(output_dir, gif_filename)
                png_path = os.path.join(output_dir, png_filename)

                # 6. Render 3D Stadium plot:
                render_cricket_stadium_trajectory(
                    res_sim, outcome, field_obj, fielders,
                    title=f"Delivery {deliv_id} ({cam.upper()}): Open-Field Trajectory",
                    filename=png_path,
                )

                # 7. Render Broadcast Video (MP4 and GIF):
                anim_duration = min(res_sim.time_s[-1], 4.5)
                generate_single_video_animation(
                    res_sim,
                    outcome=outcome,
                    field=field_obj,
                    fielders=fielders,
                    output_mp4_path=mp4_path,
                    output_gif_path=gif_path,
                    scenario_title=f"DELIVERY {deliv_id} ({cam.upper()}): OPEN-FIELD TRAJECTORY PREDICTION",
                    pipeline_metadata=video_metadata,
                    fps=20,
                    max_duration_s=anim_duration,
                    dpi=105,
                )

                # 8. Copy to brain artifact directory:
                if os.path.exists(artifact_dir):
                    shutil.copy2(mp4_path, os.path.join(artifact_dir, mp4_filename))
                    shutil.copy2(gif_path, os.path.join(artifact_dir, gif_filename))
                    shutil.copy2(png_path, os.path.join(artifact_dir, png_filename))

                all_results.append({
                    "delivery_id": deliv_id,
                    "camera": cam,
                    "folder": folder_base,
                    "bowler_speed_kmh": bowler_v,
                    "bat_hit_speed_kmh": bat_v,
                    "tracked_frames": obs.count,
                    "v0": v0,
                    "launch_speed_kmh": speed0 * 3.6,
                    "elevation_deg": elev0,
                    "azimuth_deg": azim0,
                    "first_pitch_m": d1,
                    "apex_m": apex_h,
                    "rollout_m": d_roll,
                    "total_dist_m": total_dist,
                    "rope_status": rope_str,
                    "outcome": outcome.primary_call,
                    "mp4_file": mp4_filename,
                    "gif_file": gif_filename,
                    "png_file": png_filename,
                })

                print(f"  -> Video Generated: {mp4_path}")
                print(f"  -> Outcome: [{outcome.primary_call}] | Total Dist: {total_dist:.1f}m ({rope_str})")

            except Exception as e:
                print(f"Error processing Delivery {deliv_id} {cam}: {e}")

    # Export comparison CSV:
    summary_out_csv = os.path.join(output_dir, "real_10_deliveries_cam1_cam2_summary.csv")
    with open(summary_out_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "delivery_id", "camera", "folder", "bowler_speed_kmh", "bat_hit_speed_kmh", "tracked_frames",
            "v0_x_m_s", "v0_y_m_s", "v0_z_m_s", "launch_speed_kmh", "launch_elevation_deg", "launch_azimuth_deg",
            "first_pitch_m", "apex_m", "rollout_m", "total_dist_m", "rope_status", "outcome_call",
            "mp4_video", "gif_video"
        ])
        for r in all_results:
            writer.writerow([
                r["delivery_id"], r["camera"], r["folder"], r["bowler_speed_kmh"], r["bat_hit_speed_kmh"], r["tracked_frames"],
                f"{r['v0'][0]:.2f}", f"{r['v0'][1]:.2f}", f"{r['v0'][2]:.2f}",
                f"{r['launch_speed_kmh']:.1f}", f"{r['elevation_deg']:.1f}", f"{r['azimuth_deg']:.1f}",
                f"{r['first_pitch_m']:.1f}", f"{r['apex_m']:.2f}", f"{r['rollout_m']:.1f}",
                f"{r['total_dist_m']:.1f}", r["rope_status"], r["outcome"],
                r["mp4_file"], r["gif_file"]
            ])

    if os.path.exists(artifact_dir):
        shutil.copy2(summary_out_csv, os.path.join(artifact_dir, "real_10_deliveries_cam1_cam2_summary.csv"))

    print("\n" + "=" * 90)
    print(f"COMPLETED GENERATING ALL {len(all_results)} CAMERA OUTPUT VIDEOS!")
    print(f"Summary table saved to: {summary_out_csv}")
    print("=" * 90)


if __name__ == "__main__":
    process_all_deliveries_multi_cam()
