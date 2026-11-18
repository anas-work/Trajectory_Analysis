"""
Loader and adapter for real-world 3D delivery tracking datasets (from 3d_hits_10_deliveries).

Maps dual-camera stereo coordinate systems into the simulator ground frame:
- Stereo frame: Y along pitch (decreasing after hit), Z vertical height, X lateral.
- Simulator frame: X downfield along pitch from striker crease, Y lateral, Z height.
"""

import os
import csv
import glob
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from cricket_trajectory_engine.estimation.coordinate_loader import ObservationSet, validate_observations


@dataclass
class RealDeliveryData:
    delivery_id: str
    folder_name: str
    camera: str
    observations: ObservationSet
    first_session_frame: int
    last_session_frame: int
    raw_fit_y_speed_kmh: Optional[float]
    path_length_y_m: float
    hit_timestamp_s: float


def load_real_delivery_bat_trajectory(
    delivery_folder_path: str,
    camera: str = "cam1",
) -> RealDeliveryData:
    """
    Loads post-bat 3D trajectory from a real delivery folder in 3d_hits_10_deliveries.
    Filters for frames with valid 3D triangulation (`has_3d == True`).
    """
    csv_filename = f"3d_bat_{camera}.csv"
    csv_path = os.path.join(delivery_folder_path, csv_filename)
    if not os.path.exists(csv_path):
        # Fallback to cam2 if cam1 not present
        alt_cam = "cam2" if camera == "cam1" else "cam1"
        csv_path = os.path.join(delivery_folder_path, f"3d_bat_{alt_cam}.csv")
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Could not find 3D bat CSV in {delivery_folder_path}")
        camera = alt_cam

    times = []
    positions_stereo = []
    session_frames = []

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            has_3d_str = str(row.get("has_3d", "")).strip().lower()
            if has_3d_str != "true":
                continue

            try:
                t_val = float(row["time_s"])
                x_val = float(row["X_m"])
                y_val = float(row["Y_m"])
                z_val = float(row["Z_m"])
                s_frame = int(row["session_frame"])

                times.append(t_val)
                positions_stereo.append([x_val, y_val, z_val])
                session_frames.append(s_frame)
            except (ValueError, KeyError):
                continue

    if len(times) < 2:
        raise ValueError(f"Insufficient valid 3D points in {csv_path}: got {len(times)}")

    t_arr = np.array(times)
    p_stereo = np.array(positions_stereo)

    # Convert coordinates to simulator frame:
    # At bat hit (index 0): origin is at bat impact.
    # In stereo frame, Y decreases as ball moves back towards bowler.
    # Therefore, downfield travel X_sim = Y_hit - Y_stereo.
    # Lateral travel Y_sim = x_hit - X_stereo (+Y = Off-side, -Y = On-side / Leg-side).
    # Vertical Z_sim = Z_stereo.
    y_hit = p_stereo[0, 1]
    x_hit = p_stereo[0, 0]
    t_hit = t_arr[0]

    t_rel = t_arr - t_hit
    x_sim = y_hit - p_stereo[:, 1]
    y_sim = x_hit - p_stereo[:, 0]
    z_sim = np.maximum(0.04, p_stereo[:, 2])  # Clamped above pitch ground

    pos_sim = np.column_stack((x_sim, y_sim, z_sim))

    obs = ObservationSet(
        times_s=t_rel,
        positions_m=pos_sim,
        frame_indices=np.array(session_frames),
        source_name=os.path.basename(delivery_folder_path),
    )

    # Path length along pitch:
    path_len_y = float(abs(p_stereo[-1, 1] - p_stereo[0, 1]))

    return RealDeliveryData(
        delivery_id=os.path.basename(delivery_folder_path).split("_")[0],
        folder_name=os.path.basename(delivery_folder_path),
        camera=camera,
        observations=obs,
        first_session_frame=session_frames[0],
        last_session_frame=session_frames[-1],
        raw_fit_y_speed_kmh=None,
        path_length_y_m=path_len_y,
        hit_timestamp_s=t_hit,
    )


def list_available_real_deliveries(base_dir: str = "3d_hits_10_deliveries") -> List[str]:
    """Finds all delivery subdirectories in 3d_hits_10_deliveries."""
    if not os.path.exists(base_dir):
        return []
    folders = sorted([
        os.path.join(base_dir, d)
        for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d)) and not d.startswith(".") and d != "bat_hit_graphs"
    ])
    return folders

