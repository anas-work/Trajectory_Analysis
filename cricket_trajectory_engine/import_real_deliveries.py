"""
Importer script to load all 10 real deliveries (both Cam 1 and Cam 2) into the
persistent experiments repository (experiments/) as formal experiments.

This ensures all 20 real-world camera observations appear by default in
the Experiment History table, complete with full calculation traces,
trajectories, outcomes, and rendered multi-view videos.
"""

import os
import sys
import shutil
import numpy as np

# Ensure root directory is on PYTHONPATH
sys.path.insert(0, os.path.abspath("."))

from cricket_trajectory_engine.models.experiment import (
    ExperimentConfig,
    ExperimentRecord,
    compute_simulation_fingerprint,
)
from cricket_trajectory_engine.estimation.real_delivery_loader import (
    list_available_real_deliveries,
    load_real_delivery_bat_trajectory,
)
from cricket_trajectory_engine.estimation.velocity_estimator import estimate_initial_state
from cricket_trajectory_engine.services.simulation_service import SimulationService
from cricket_trajectory_engine.services.experiment_service import ExperimentService


def import_delivery_set(
    dataset_dir: str,
    id_prefix: str = "DELIVERY_",
    name_suffix: str = "",
    tag_name: str = "10_deliveries",
):
    sim_service = SimulationService()
    exp_service = ExperimentService(base_dir="experiments")
    delivery_folders = list_available_real_deliveries(dataset_dir)

    print(f"\nFound {len(delivery_folders)} deliveries in {dataset_dir} to import.")
    imported_count = 0
    video_source_dir = "cricket_trajectory_engine/data/real_deliveries_videos"

    for folder_path in delivery_folders:
        folder_name = os.path.basename(folder_path)
        d_idx = folder_name.split("_")[0]  # "01", "02", etc.

        for cam in ["cam1", "cam2"]:
            exp_id = f"{id_prefix}{d_idx}_{cam.upper()}"
            name = f"Delivery {d_idx}{name_suffix} ({cam.upper()} Tracking)"
            desc = f"Real-world match delivery from {folder_name} ({dataset_dir}) using {cam.upper()} stereo tracking"

            try:
                real_data = load_real_delivery_bat_trajectory(folder_path, camera=cam)
                init_state = estimate_initial_state(
                    real_data.observations, method="polynomial", polynomial_order=2
                )
                p0_fit = init_state.initial_position_m
                v_fit = init_state.initial_velocity_m_s
            except Exception as e:
                print(f"  Skipping {exp_id}: error loading coordinates ({e})")
                continue

            # Standard cricket configuration for match conditions
            config = ExperimentConfig(
                name=name,
                input_mode="camera_tracking",
                pos0=[float(p0_fit[0]), float(p0_fit[1]), float(p0_fit[2])],
                vel0=[float(v_fit[0]), float(v_fit[1]), float(v_fit[2])],
                ball={"mass_kg": 0.156, "diameter_m": 0.072},
                environment={
                    "air_density_kg_m3": 1.205,
                    "constant_cd": 0.32,
                    "restitution_normal": 0.50,
                    "friction_tangential": 0.35,
                    "rolling_resistance_coeff": 0.10,
                    "enable_magnus": False,
                },
                stadium={"boundary_radius_m": 70.0},
            )
            config.sync_velocity_and_angles()

            # Run physical simulation and generate calculation trace
            res_obj, trace, res_multibounce, outcome = sim_service.run_simulation(config)

            record = ExperimentRecord(
                experiment_id=exp_id,
                name=name,
                description=desc,
                created_at="2026-11-19T10:00:00",
                tags=["real_delivery", tag_name, f"delivery_{d_idx}", cam.lower(), outcome.primary_call.lower()],
                config=config,
                results=res_obj,
                fingerprint=res_obj.fingerprint,
            )

            # Persist experiment
            saved_id = exp_service.save_experiment(record, res_multibounce, trace)
            exp_dir = os.path.join("experiments", saved_id)

            # Link existing generated video, gif, and renders if present
            v_dir = os.path.join(exp_dir, "videos")
            vis_dir = os.path.join(exp_dir, "visualizations")
            os.makedirs(v_dir, exist_ok=True)
            os.makedirs(vis_dir, exist_ok=True)

            src_mp4 = os.path.join(video_source_dir, f"delivery_{d_idx}_{cam}_prediction.mp4")
            src_gif = os.path.join(video_source_dir, f"delivery_{d_idx}_{cam}_prediction.gif")
            src_png = os.path.join(video_source_dir, f"delivery_{d_idx}_{cam}_stadium_3d.png")
            src_gt_clip = os.path.join(folder_path, f"clip_{cam}.mp4")

            if os.path.exists(src_mp4) and dataset_dir == "3d_hits_10_deliveries":
                shutil.copy2(src_mp4, os.path.join(v_dir, "simulation_presentation.mp4"))
                shutil.copy2(src_mp4, os.path.join(v_dir, f"delivery_{d_idx}_{cam}_prediction.mp4"))
            if os.path.exists(src_gif) and dataset_dir == "3d_hits_10_deliveries":
                shutil.copy2(src_gif, os.path.join(v_dir, "simulation_presentation.gif"))
            if os.path.exists(src_png) and dataset_dir == "3d_hits_10_deliveries":
                shutil.copy2(src_png, os.path.join(vis_dir, "stadium_3d.png"))
            if os.path.exists(src_gt_clip):
                shutil.copy2(src_gt_clip, os.path.join(v_dir, "ground_truth_clip.mp4"))

            spd_kmh = float(np.linalg.norm(config.vel0) * 3.6)
            imported_count += 1
            print(f"  [✓] Imported {saved_id}: {res_obj.outcome_call} | Launch: {spd_kmh:.1f} km/h, {init_state.elevation_angle_deg:+.1f}°, {init_state.azimuth_angle_deg:+.1f}° | Carry: {res_obj.carry_distance_m:.1f}m | Total: {res_obj.total_distance_m:.1f}m")

    print(f"Successfully imported {imported_count} real deliveries from {dataset_dir}.")
    return imported_count


def import_all_real_deliveries():
    c1 = import_delivery_set(
        dataset_dir="3d_hits_10_deliveries",
        id_prefix="DELIVERY_",
        name_suffix="",
        tag_name="10_deliveries",
    )
    c2 = import_delivery_set(
        dataset_dir="3d_hits_39_more_deliveries",
        id_prefix="DELIVERY_39_",
        name_suffix=" (39-Set)",
        tag_name="39_more_deliveries",
    )
    print(f"\n=======================================================")
    print(f"TOTAL REAL DELIVERIES IMPORTED: {c1 + c2} ({c1} + {c2})")
    print(f"=======================================================")


if __name__ == "__main__":
    import_all_real_deliveries()
