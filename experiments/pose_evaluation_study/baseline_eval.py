"""
Baseline Trajectory Evaluation across all 10 real deliveries in 3d_hits_10_deliveries.
Evaluates:
- Trajectory fit RMSE against ground-truth stereo points
- Launch speed, elevation angle, azimuth
- Initial position (impact position)
- Impact frame ball visibility vs occlusion
"""

import os
import sys
import csv
import json
import numpy as np

# Ensure root directory is on PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cricket_trajectory_engine.config.physics_config import (
    BallConfig,
    EnvironmentConfig,
    AerodynamicsConfig,
    SimulationConfig,
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


def evaluate_baselines():
    folders = list_available_real_deliveries()
    results = []

    print(f"Running baseline evaluation on {len(folders)} real deliveries...")

    for f in folders:
        folder_name = os.path.basename(f)
        deliv_id = folder_name.split("_")[0]
        
        # Load ground truth tracking
        for cam in ["cam1", "cam2"]:
            try:
                deliv_data = load_real_delivery_bat_trajectory(f, camera=cam)
            except Exception as e:
                continue

            obs = deliv_data.observations
            n_pts = len(obs.times_s)
            
            # Initial state estimation (polynomial method)
            init_poly = estimate_initial_state(obs, method="polynomial", polynomial_order=2)
            
            # Trajectory fit with aerodynamics
            fit_res = fit_trajectory_to_observations(
                obs,
                ball_config=BallConfig(),
                env_config=EnvironmentConfig(),
                aero_config=AerodynamicsConfig(constant_cd=0.32),
                fit_drag_coefficient=False,
            )

            # Analyze frame-by-frame ball occlusion around hit
            fbf_csv = os.path.join(f, f"3d_frame_by_frame_{cam}.csv")
            occlusion_stats = {"total_frames": 0, "detected_frames": 0, "occluded_around_hit": False, "hit_frame": None}
            if os.path.exists(fbf_csv):
                with open(fbf_csv, "r", encoding="utf-8-sig") as csv_f:
                    reader = csv.DictReader(csv_f)
                    rows = list(reader)
                    occlusion_stats["total_frames"] = len(rows)
                    detected = [r.get("detected", "").lower() == "true" for r in rows]
                    occlusion_stats["detected_frames"] = sum(detected)
                    
                    # Find hit frame
                    for i, r in enumerate(rows):
                        if r.get("event") == "bat" or r.get("phase") == "bat":
                            occlusion_stats["hit_frame"] = int(r.get("clip_frame", i))
                            # Check window [hit-2, hit+2]
                            start_w = max(0, i - 2)
                            end_w = min(len(rows), i + 3)
                            undetected_in_hit = sum(not detected[k] for k in range(start_w, end_w))
                            occlusion_stats["occluded_around_hit"] = (undetected_in_hit > 0)
                            break

            rec = {
                "delivery_id": deliv_id,
                "folder": folder_name,
                "camera": cam,
                "obs_points": n_pts,
                "path_length_m": deliv_data.path_length_y_m,
                "launch_speed_kmh": round(init_poly.initial_speed_m_s * 3.6, 2),
                "launch_elevation_deg": round(init_poly.elevation_angle_deg, 2),
                "launch_azimuth_deg": round(init_poly.azimuth_angle_deg, 2),
                "initial_pos_m": [round(float(v), 3) for v in init_poly.initial_position_m],
                "initial_vel_m_s": [round(float(v), 3) for v in init_poly.initial_velocity_m_s],
                "fit_rmse_total_m": round(fit_res.total_rmse_m, 4),
                "fit_rmse_x_m": round(fit_res.per_axis_rmse_m.get("x", 0.0), 4),
                "fit_rmse_y_m": round(fit_res.per_axis_rmse_m.get("y", 0.0), 4),
                "fit_rmse_z_m": round(fit_res.per_axis_rmse_m.get("z", 0.0), 4),
                "hit_frame": occlusion_stats["hit_frame"],
                "occluded_around_hit": occlusion_stats["occluded_around_hit"],
                "ball_detection_rate": round(occlusion_stats["detected_frames"] / max(1, occlusion_stats["total_frames"]), 3),
            }
            results.append(rec)
            print(f"[{deliv_id} {cam}] Speed={rec['launch_speed_kmh']} km/h, Elev={rec['launch_elevation_deg']}°, RMSE={rec['fit_rmse_total_m']}m, Occluded={rec['occluded_around_hit']}")
            break # Evaluate primary camera per delivery

    out_json = "experiments/pose_evaluation_study/baseline_results.json"
    out_csv = "experiments/pose_evaluation_study/baseline_results.csv"
    
    with open(out_json, "w") as jf:
        json.dump(results, jf, indent=2)

    keys = list(results[0].keys())
    with open(out_csv, "w", newline="") as cf:
        writer = csv.DictWriter(cf, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nSaved baseline evaluation to {out_json} and {out_csv}")
    return results


if __name__ == "__main__":
    evaluate_baselines()
