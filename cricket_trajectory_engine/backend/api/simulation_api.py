"""
Simulation REST API: Exposes trajectory simulation and calculation trace retrieval.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
import math
import numpy as np

from cricket_trajectory_engine.models.experiment import ExperimentConfig, ExperimentRecord
from cricket_trajectory_engine.services.simulation_service import SimulationService
from cricket_trajectory_engine.services.experiment_service import ExperimentService

router = APIRouter(prefix="/api/simulation", tags=["simulation"])
sim_service = SimulationService()
exp_service = ExperimentService()


@router.post("/run")
def run_simulation(config_dict: Dict[str, Any]):
    """
    Executes physical flight simulation from manual or camera inputs.
    Returns:
    - Experiment results (apex, carry, rollout, outcome, rope clearance)
    - Full mathematical calculation trace with substituted formulas
    - Downsampled 3D trajectory points for Three.js WebGL visualization
    - Simulation fingerprint, experiment_id, and cache status
    """
    try:
        # Extract initial position (support pos0 and initial_position keys)
        pos0 = config_dict.get("pos0") or config_dict.get("initial_position") or [0.0, 0.0, 0.9]
        if isinstance(pos0, list) and len(pos0) >= 3:
            pos0 = [float(pos0[0]), float(pos0[1]), float(pos0[2])]

        # Extract initial velocity (support vel0 and initial_velocity keys, or compute from speed/angles)
        vel0 = config_dict.get("vel0") or config_dict.get("initial_velocity")
        has_speed_or_angles = any(
            config_dict.get(k) is not None for k in (
                "speed", "speed_m_s", "speed0_kmh", "launch_speed_kmh",
                "elevation", "elevation_deg", "elev", "launch_elevation_deg",
                "azimuth", "azimuth_deg", "azim", "launch_azimuth_deg"
            )
        )

        if not vel0 and has_speed_or_angles:
            if config_dict.get("speed_m_s") is not None:
                spd = float(config_dict["speed_m_s"])
            elif config_dict.get("speed") is not None:
                spd = float(config_dict["speed"])
            elif config_dict.get("speed0_kmh") is not None:
                spd = float(config_dict["speed0_kmh"]) / 3.6
            elif config_dict.get("launch_speed_kmh") is not None:
                spd = float(config_dict["launch_speed_kmh"]) / 3.6
            else:
                spd = 30.0

            if config_dict.get("elevation_deg") is not None:
                raw_elev = float(config_dict["elevation_deg"])
            elif config_dict.get("elevation") is not None:
                raw_elev = float(config_dict["elevation"])
            elif config_dict.get("elev") is not None:
                raw_elev = float(config_dict["elev"])
            elif config_dict.get("launch_elevation_deg") is not None:
                raw_elev = float(config_dict["launch_elevation_deg"])
            else:
                raw_elev = 25.0

            if config_dict.get("azimuth_deg") is not None:
                raw_azim = float(config_dict["azimuth_deg"])
            elif config_dict.get("azimuth") is not None:
                raw_azim = float(config_dict["azimuth"])
            elif config_dict.get("azim") is not None:
                raw_azim = float(config_dict["azim"])
            elif config_dict.get("launch_azimuth_deg") is not None:
                raw_azim = float(config_dict["launch_azimuth_deg"])
            else:
                raw_azim = 0.0

            elev = math.radians(raw_elev)
            azim = math.radians(raw_azim)
            vxy = spd * math.cos(elev)
            vel0 = [float(vxy * math.cos(azim)), float(vxy * math.sin(azim)), float(spd * math.sin(elev))]
        elif isinstance(vel0, list) and len(vel0) >= 3:
            vel0 = [float(vel0[0]), float(vel0[1]), float(vel0[2])]
        else:
            vel0 = [28.0, 0.0, 6.2]

        # Normalize environment, aerodynamics, and ball parameters
        env_dict = dict(config_dict.get("environment", {}))
        aero_dict = config_dict.get("aerodynamics", {})
        if aero_dict:
            if "cd_base" in aero_dict and "constant_cd" not in env_dict:
                env_dict["constant_cd"] = float(aero_dict["cd_base"])
            if "drag_model" in aero_dict and "drag_model" not in env_dict:
                env_dict["drag_model"] = aero_dict["drag_model"]
            if "enable_magnus" in aero_dict and "enable_magnus" not in env_dict:
                env_dict["enable_magnus"] = aero_dict["enable_magnus"]
            if "spin_vector" in aero_dict and "spin_rad_s" not in env_dict:
                env_dict["spin_rad_s"] = aero_dict["spin_vector"]
        if "wind_vector" in env_dict and "wind_vector_m_s" not in env_dict:
            env_dict["wind_vector_m_s"] = env_dict["wind_vector"]

        # Ensure drag_model matches PhysicsConfig accepted literals ('constant' or 'reynolds_dependent')
        raw_drag = str(env_dict.get("drag_model", "constant")).lower()
        if "reynolds" in raw_drag or "morrison" in raw_drag:
            env_dict["drag_model"] = "reynolds_dependent"
        else:
            env_dict["drag_model"] = "constant"

        ball_dict = dict(config_dict.get("ball", {}))
        if "mass" in ball_dict and "mass_kg" not in ball_dict:
            ball_dict["mass_kg"] = float(ball_dict["mass"])
        if "diameter" in ball_dict and "diameter_m" not in ball_dict:
            ball_dict["diameter_m"] = float(ball_dict["diameter"])

        stadium_dict = dict(config_dict.get("stadium", {}))
        if "boundary_radius" in stadium_dict and "boundary_radius_m" not in stadium_dict:
            stadium_dict["boundary_radius_m"] = float(stadium_dict["boundary_radius"])

        fielding_data = dict(config_dict.get("fielding", {}))
        if not fielding_data and "fielders" in config_dict:
            fielding_data = {"fielders": config_dict.get("fielders")}

        config = ExperimentConfig(
            name=config_dict.get("name") or "Custom Simulation",
            input_mode=config_dict.get("input_mode", "manual_velocity"),
            pos0=pos0,
            vel0=vel0,
            ball=ball_dict,
            environment=env_dict,
            stadium=stadium_dict,
            fielding=fielding_data,
            solver=config_dict.get("solver", {}),
        )
        config.sync_velocity_and_angles()

        # Check if identical simulation is cached:
        res_obj, trace, res_multibounce, outcome = sim_service.run_simulation(config)
        cached_id = exp_service.find_cached_experiment(res_obj.fingerprint)

        # Generate unique experiment ID and timestamp for every user execution
        now = datetime.now()
        created_at_str = now.isoformat()
        base_exp_id = f"EXP_{now.strftime('%Y%m%d_%H%M%S')}"
        exp_id = base_exp_id
        if exp_service.get_experiment(exp_id):
            exp_id = f"{base_exp_id}_{now.microsecond // 1000:03d}"

        custom_name = config_dict.get("name")
        if not custom_name or custom_name == "Interactive Experiment":
            rec_name = f"Shot ({config.speed0_kmh:.1f} km/h @ {config.elevation_deg:.1f}°, {config.azimuth_deg:.1f}° azim)"
        else:
            rec_name = custom_name

        rec = ExperimentRecord(
            experiment_id=exp_id,
            name=rec_name,
            description=f"Simulated via UI on {now.strftime('%Y-%m-%d at %H:%M:%S')}",
            created_at=created_at_str,
            tags=["ui_simulation", outcome.primary_call.lower()],
            config=config,
            results=res_obj,
            fingerprint=res_obj.fingerprint,
        )
        saved_id = exp_service.save_experiment(rec, res_multibounce, trace)

        # Keyframe-preserving downsampling for fast, millimeter-accurate frontend WebGL rendering:
        ball_radius_m = float(config.ball.get("diameter_m", 0.0725)) / 2.0 if config.ball else 0.03625
        catch_time = None
        catch_pos = None
        if res_obj.fielder_interception and res_obj.fielder_interception.get("can_intercept"):
            catch_time = res_obj.fielder_interception.get("catch_time_s")
            cp = res_obj.fielder_interception.get("intercept_position_m")
            if cp:
                catch_pos = np.array(cp, dtype=float)

        downsampled_points = res_multibounce.to_sampled_points(
            max_points=250,
            ball_radius_m=ball_radius_m,
            catch_time_s=catch_time,
            catch_position_m=catch_pos,
        )

        # Bounces:
        bounces_data = [
            {
                "bounce_idx": b.bounce_index,
                "time_s": round(float(b.time_s), 3),
                "x": round(float(b.position_m[0]), 2),
                "y": round(float(b.position_m[1]), 2),
                "z": round(float(b.position_m[2]), 3),
                "pre_speed_kmh": round(float(b.pre_speed_m_s) * 3.6, 1),
                "post_speed_kmh": round(float(b.post_speed_m_s) * 3.6, 1),
                "energy_loss_pct": round(float(b.energy_loss_ratio) * 100, 1),
            }
            for b in res_multibounce.bounces
        ]

        return {
            "status": "success",
            "experiment_id": exp_id,
            "is_cached": cached_id is not None,
            "cached_experiment_id": cached_id,
            "fingerprint": res_obj.fingerprint,
            "config": config.to_dict(),
            "results": res_obj.to_dict(),
            "calculation_trace": trace.to_dict(),
            "trajectory_samples": downsampled_points,
            "bounces": bounces_data,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
