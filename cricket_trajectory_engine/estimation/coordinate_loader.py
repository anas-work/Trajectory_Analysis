"""
Coordinate loader, validation, and synthetic observation generator.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional, Union
import os
import csv
import numpy as np


@dataclass
class ObservationSet:
    """Validated 3D ball coordinate observations with timestamps."""
    times_s: np.ndarray       # Shape (N,)
    positions_m: np.ndarray   # Shape (N, 3) [X, Y, Z]
    frame_indices: Optional[np.ndarray] = None
    source_name: str = "synthetic"

    @property
    def count(self) -> int:
        return len(self.times_s)

    @property
    def duration_s(self) -> float:
        return float(self.times_s[-1] - self.times_s[0]) if self.count > 1 else 0.0

    @property
    def average_dt_s(self) -> float:
        return float(np.mean(np.diff(self.times_s))) if self.count > 1 else 0.0

    @property
    def estimated_fps(self) -> float:
        dt = self.average_dt_s
        return 1.0 / dt if dt > 0 else 0.0

    def slice(self, start: int, stop: int) -> "ObservationSet":
        return ObservationSet(
            times_s=self.times_s[start:stop],
            positions_m=self.positions_m[start:stop],
            frame_indices=self.frame_indices[start:stop] if self.frame_indices is not None else None,
            source_name=self.source_name,
        )

    def to_csv(self, filepath: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["time_s", "x_m", "y_m", "z_m"])
            for t, (x, y, z) in zip(self.times_s, self.positions_m):
                writer.writerow([round(t, 6), round(x, 4), round(y, 4), round(z, 4)])


def validate_observations(
    times: Union[List[float], np.ndarray],
    positions: Union[List[List[float]], np.ndarray],
    min_points: int = 2,
    max_height_bound_m: float = 60.0,
    max_horizontal_bound_m: float = 150.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Validates observation sequences:
    - Checks dimensions, types, and finite values.
    - Ensures minimum number of points.
    - Ensures timestamps are strictly monotonically increasing.
    - Ensures positions are physically feasible within cricket ground bounds.
    """
    t_arr = np.asarray(times, dtype=float)
    p_arr = np.asarray(positions, dtype=float)

    if t_arr.ndim != 1:
        raise ValueError(f"Timestamps must be a 1D array, got shape {t_arr.shape}")
    if p_arr.ndim != 2 or p_arr.shape[1] != 3:
        raise ValueError(f"Positions must have shape (N, 3), got shape {p_arr.shape}")
    if len(t_arr) != len(p_arr):
        raise ValueError(f"Mismatch: {len(t_arr)} timestamps vs {len(p_arr)} positions")
    if len(t_arr) < min_points:
        raise ValueError(f"At least {min_points} points required, got {len(t_arr)}")

    if not np.all(np.isfinite(t_arr)):
        raise ValueError("Non-finite timestamp detected (NaN or Inf)")
    if not np.all(np.isfinite(p_arr)):
        raise ValueError("Non-finite coordinate detected (NaN or Inf)")

    # Monotonic timestamps:
    dt = np.diff(t_arr)
    if np.any(dt <= 0.0):
        bad_idx = int(np.where(dt <= 0.0)[0][0])
        raise ValueError(
            f"Timestamps must be strictly increasing: t[{bad_idx}]={t_arr[bad_idx]:.5f} "
            f">= t[{bad_idx+1}]={t_arr[bad_idx+1]:.5f}"
        )

    # Physical bounds checks:
    z_coords = p_arr[:, 2]
    if np.any(z_coords < 0.0):
        min_z = float(np.min(z_coords))
        raise ValueError(f"Observed ball height Z cannot be negative, got {min_z:.3f} m")
    if np.any(z_coords > max_height_bound_m):
        max_z = float(np.max(z_coords))
        raise ValueError(f"Observed ball height Z exceeds realistic bound ({max_z:.3f} > {max_height_bound_m} m)")

    horiz_dist = np.hypot(p_arr[:, 0], p_arr[:, 1])
    if np.any(horiz_dist > max_horizontal_bound_m):
        max_d = float(np.max(horiz_dist))
        raise ValueError(f"Observed coordinate exceeds field bound ({max_d:.2f} > {max_horizontal_bound_m} m)")

    return t_arr, p_arr


def load_observations_from_csv(filepath: str) -> ObservationSet:
    """
    Loads observed 3D coordinates from a CSV file.
    Expected header: 'time_s', 'x_m', 'y_m', 'z_m' (or case-insensitive variations).
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Observation CSV file not found: {filepath}")

    times: List[float] = []
    positions: List[List[float]] = []

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        # Normalize header keys:
        keys_lower = {k.strip().lower(): k for k in reader.fieldnames or []}

        # Identify time key:
        t_key = None
        for candidate in ["time_s", "time", "t", "timestamp"]:
            if candidate in keys_lower:
                t_key = keys_lower[candidate]
                break
        if not t_key:
            raise KeyError("CSV must contain a 'time_s' or 'time' column")

        # Identify coordinate keys:
        x_key = keys_lower.get("x_m") or keys_lower.get("x")
        y_key = keys_lower.get("y_m") or keys_lower.get("y")
        z_key = keys_lower.get("z_m") or keys_lower.get("z")

        if not (x_key and y_key and z_key):
            raise KeyError("CSV must contain columns for x, y, and z coordinates")

        for row_idx, row in enumerate(reader):
            try:
                t_val = float(row[t_key])
                x_val = float(row[x_key])
                y_val = float(row[y_key])
                z_val = float(row[z_key])
                times.append(t_val)
                positions.append([x_val, y_val, z_val])
            except ValueError as e:
                raise ValueError(f"Failed parsing row {row_idx+1} in {filepath}: {e}")

    t_arr, p_arr = validate_observations(times, positions)
    return ObservationSet(
        times_s=t_arr,
        positions_m=p_arr,
        source_name=os.path.basename(filepath),
    )


def generate_synthetic_observations(
    flight_result,
    start_time_s: float = 0.0,
    end_time_s: float = 0.15,
    fps: float = 30.0,
    noise_std_m: float = 0.0,
    random_seed: Optional[int] = None,
) -> ObservationSet:
    """
    Extracts an observation window (e.g. 5-10 frames after shot) from a simulated trajectory,
    optionally injecting Gaussian tracking noise to test estimator robustness.
    """
    times = flight_result.time_s
    positions = flight_result.positions_m

    dt = 1.0 / fps
    sample_times = np.arange(start_time_s, min(end_time_s + 1e-6, times[-1]), dt)

    # Linear interpolation at sample_times:
    sample_positions = np.zeros((len(sample_times), 3))
    for i in range(3):
        sample_positions[:, i] = np.interp(sample_times, times, positions[:, i])

    if noise_std_m > 0.0:
        rng = np.random.default_rng(random_seed)
        noise = rng.normal(0.0, noise_std_m, size=sample_positions.shape)
        # Ensure height doesn't go below ground
        sample_positions += noise
        sample_positions[:, 2] = np.maximum(0.036, sample_positions[:, 2])

    t_arr, p_arr = validate_observations(sample_times, sample_positions)
    return ObservationSet(
        times_s=t_arr,
        positions_m=p_arr,
        source_name="synthetic_window",
    )

