"""
Experiment Data Models and Deterministic Simulation Fingerprinting.
"""

import hashlib
import json
import math
import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import numpy as np

from cricket_trajectory_engine.models.ball import BallModel
from cricket_trajectory_engine.models.environment import EnvironmentModel
from cricket_trajectory_engine.models.stadium import StadiumModel
from cricket_trajectory_engine.models.fielder import FieldingSetupModel


def compute_simulation_fingerprint(
    pos0: List[float],
    vel0: List[float],
    ball_dict: Dict[str, Any],
    env_dict: Dict[str, Any],
    stadium_dict: Dict[str, Any],
    solver_dict: Dict[str, Any],
    fielding_dict: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Computes a deterministic SHA-256 fingerprint from the physical simulation inputs.
    Any identical physics simulation produces the exact same hash.
    Visual styling or video settings do not affect this fingerprint.
    """
    canonical_dict = {
        "pos0": [round(float(x), 4) for x in pos0],
        "vel0": [round(float(v), 4) for v in vel0],
        "ball": {
            "mass_kg": round(float(ball_dict.get("mass_kg", 0.160)), 4),
            "diameter_m": round(float(ball_dict.get("diameter_m", 0.0725)), 5),
        },
        "env": {
            "air_density": round(float(env_dict.get("air_density_kg_m3", 1.225)), 4),
            "gravity": round(float(env_dict.get("gravity_m_s2", 9.80665)), 4),
            "drag_model": str(env_dict.get("drag_model", "constant")),
            "cd": round(float(env_dict.get("constant_cd", 0.32)), 4),
            "enable_magnus": bool(env_dict.get("enable_magnus", False)),
            "restitution": round(float(env_dict.get("restitution_normal", 0.55)), 4),
            "friction": round(float(env_dict.get("friction_tangential", 0.38)), 4),
            "rolling": round(float(env_dict.get("rolling_resistance_coeff", 0.20)), 4),
        },
        "stadium": {
            "shape": str(stadium_dict.get("boundary_shape", "circular")),
            "radius": round(float(stadium_dict.get("boundary_radius_m", 70.0)), 2),
        },
        "solver": {
            "method": str(solver_dict.get("method", "RK45")),
            "rtol": float(solver_dict.get("rtol", 1e-7)),
            "atol": float(solver_dict.get("atol", 1e-9)),
        }
    }
    if fielding_dict:
        fielders = fielding_dict.get("fielders", [])
        canonical_dict["fielding"] = [
            {
                "id": str(f.get("id", "")),
                "x": round(float(f.get("x_m", f.get("x", 0.0))), 2),
                "y": round(float(f.get("y_m", f.get("y", 0.0))), 2),
                "sprint": round(float(f.get("max_sprint_speed_m_s", f.get("sprint_speed_m_s", fielding_dict.get("sprint_speed_m_s", 7.0)))), 2),
                "react": round(float(f.get("reaction_time_s", fielding_dict.get("reaction_time_s", 0.35))), 3),
                "reach": round(float(f.get("reach_radius_m", f.get("catching_radius", fielding_dict.get("reach_radius_m", 1.8)))), 2),
            }
            for f in fielders
        ]
    encoded = json.dumps(canonical_dict, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


@dataclass
class ExperimentConfig:
    name: str = "Experiment"
    input_mode: str = "manual_velocity"   # "manual_velocity", "manual_angles", "camera_tracking"
    pos0: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.90])
    vel0: List[float] = field(default_factory=lambda: [28.0, 10.0, 6.2])
    speed0_kmh: Optional[float] = None
    elevation_deg: Optional[float] = None
    azimuth_deg: Optional[float] = None
    ball: Dict[str, Any] = field(default_factory=lambda: BallModel().to_dict())
    environment: Dict[str, Any] = field(default_factory=lambda: EnvironmentModel().to_dict())
    stadium: Dict[str, Any] = field(default_factory=lambda: StadiumModel().to_dict())
    fielding: Dict[str, Any] = field(default_factory=lambda: FieldingSetupModel.from_preset("powerplay").to_dict())
    solver: Dict[str, Any] = field(default_factory=lambda: {
        "method": "RK45",
        "rtol": 1e-7,
        "atol": 1e-9,
        "max_step": 0.02,
        "max_duration_s": 12.0,
    })

    def sync_velocity_and_angles(self) -> None:
        """Ensures bidirectional consistency between velocity vector and speed/elevation/azimuth."""
        if (
            self.input_mode in ("manual_angles", "angles")
            or (
                self.speed0_kmh is not None
                and self.elevation_deg is not None
                and self.azimuth_deg is not None
                and self.vel0 == [28.0, 10.0, 6.2]
            )
        ):
            spd = float(self.speed0_kmh) / 3.6
            elev = math.radians(float(self.elevation_deg))
            azim = math.radians(float(self.azimuth_deg))
            vxy = spd * math.cos(elev)
            self.vel0 = [
                round(float(vxy * math.cos(azim)), 4),
                round(float(vxy * math.sin(azim)), 4),
                round(float(spd * math.sin(elev)), 4),
            ]
        elif self.vel0 is not None:
            vx, vy, vz = self.vel0
            speed_m_s = math.sqrt(vx**2 + vy**2 + vz**2)
            self.speed0_kmh = round(speed_m_s * 3.6, 2)
            self.elevation_deg = round(math.degrees(math.atan2(vz, math.hypot(vx, vy))), 2)
            self.azimuth_deg = round(math.degrees(math.atan2(vy, vx)), 2)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExperimentResult:
    fingerprint: str
    flight_time_s: float
    carry_distance_m: float
    max_height_m: float
    time_to_apex_s: float
    first_landing_pos_m: List[float]
    total_bounces: int
    post_bounce_roll_m: float
    total_distance_m: float
    final_stopping_pos_m: List[float]
    clears_rope: bool
    residual_speed_at_rope_kmh: Optional[float]
    margin_to_rope_m: float
    outcome_call: str
    estimated_runs: int
    fielder_interception: Optional[Dict[str, Any]] = None
    unconstrained_rollout_m: Optional[float] = None
    boundary_distance_m: Optional[float] = None
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExperimentRecord:
    experiment_id: str
    name: str
    description: str
    created_at: str
    tags: List[str] = field(default_factory=list)
    config: ExperimentConfig = field(default_factory=ExperimentConfig)
    results: Optional[ExperimentResult] = None
    fingerprint: str = ""
    is_cached: bool = False
    artifacts: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "tags": self.tags,
            "fingerprint": self.fingerprint,
            "is_cached": self.is_cached,
            "config": self.config.to_dict(),
            "results": self.results.to_dict() if self.results else None,
            "artifacts": self.artifacts,
        }
