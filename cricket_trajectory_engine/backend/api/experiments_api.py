"""
Experiments REST API: CRUD operations, persistence, and video rendering.
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any, Optional
from datetime import datetime
import os
import shutil
import time
import json
import base64
import math

from cricket_trajectory_engine.models.experiment import (
    ExperimentRecord,
    ExperimentConfig,
    ExperimentResult,
)
from cricket_trajectory_engine.services.simulation_service import SimulationService
from cricket_trajectory_engine.services.experiment_service import ExperimentService
from cricket_trajectory_engine.visualization.video_generator import generate_single_video_animation
from cricket_trajectory_engine.prediction.field_geometry import CricketField
from cricket_trajectory_engine.config.physics_config import FieldConfig
from cricket_trajectory_engine.prediction.outcome_engine import FielderPosition

router = APIRouter(prefix="/api/experiments", tags=["experiments"])
sim_service = SimulationService()
exp_service = ExperimentService()


@router.get("")
def list_experiments():
    return {"experiments": exp_service.list_experiments()}


@router.get("/{experiment_id}")
def get_experiment(experiment_id: str):
    data = exp_service.get_experiment(experiment_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found")
    return data


@router.post("")
def create_and_save_experiment(payload: Dict[str, Any]):
    """Runs simulation, records calculation trace, and saves full package to disk."""
    name = payload.get("name", f"Experiment {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    description = payload.get("description", "Manual simulation run")
    tags = payload.get("tags", ["manual"])
    cfg_dict = payload.get("config", payload)

    pos0 = cfg_dict.get("pos0") or cfg_dict.get("initial_position") or [0.0, 0.0, 0.9]
    if isinstance(pos0, list) and len(pos0) >= 3:
        pos0 = [float(pos0[0]), float(pos0[1]), float(pos0[2])]

    vel0 = cfg_dict.get("vel0") or cfg_dict.get("initial_velocity")
    has_speed_or_angles = any(
        cfg_dict.get(k) is not None for k in (
            "speed", "speed_m_s", "speed0_kmh", "launch_speed_kmh",
            "elevation", "elevation_deg", "elev", "launch_elevation_deg",
            "azimuth", "azimuth_deg", "azim", "launch_azimuth_deg"
        )
    )

    if not vel0 and has_speed_or_angles:
        if cfg_dict.get("speed_m_s") is not None:
            spd = float(cfg_dict["speed_m_s"])
        elif cfg_dict.get("speed") is not None:
            spd = float(cfg_dict["speed"])
        elif cfg_dict.get("speed0_kmh") is not None:
            spd = float(cfg_dict["speed0_kmh"]) / 3.6
        elif cfg_dict.get("launch_speed_kmh") is not None:
            spd = float(cfg_dict["launch_speed_kmh"]) / 3.6
        else:
            spd = 30.0

        if cfg_dict.get("elevation_deg") is not None:
            raw_elev = float(cfg_dict["elevation_deg"])
        elif cfg_dict.get("elevation") is not None:
            raw_elev = float(cfg_dict["elevation"])
        elif cfg_dict.get("elev") is not None:
            raw_elev = float(cfg_dict["elev"])
        elif cfg_dict.get("launch_elevation_deg") is not None:
            raw_elev = float(cfg_dict["launch_elevation_deg"])
        else:
            raw_elev = 25.0

        if cfg_dict.get("azimuth_deg") is not None:
            raw_azim = float(cfg_dict["azimuth_deg"])
        elif cfg_dict.get("azimuth") is not None:
            raw_azim = float(cfg_dict["azimuth"])
        elif cfg_dict.get("azim") is not None:
            raw_azim = float(cfg_dict["azim"])
        elif cfg_dict.get("launch_azimuth_deg") is not None:
            raw_azim = float(cfg_dict["launch_azimuth_deg"])
        else:
            raw_azim = 0.0

        elev = math.radians(raw_elev)
        azim = math.radians(raw_azim)
        vxy = spd * math.cos(elev)
        vel0 = [float(vxy * math.cos(azim)), float(vxy * math.sin(azim)), float(spd * math.sin(elev))]
    elif isinstance(vel0, list) and len(vel0) >= 3:
        vel0 = [float(vel0[0]), float(vel0[1]), float(vel0[2])]
    else:
        vel0 = [28.0, 10.0, 6.2]

    fielding_data = dict(cfg_dict.get("fielding", {}))
    if not fielding_data and "fielders" in cfg_dict:
        fielding_data = {"fielders": cfg_dict.get("fielders")}

    config = ExperimentConfig(
        input_mode=cfg_dict.get("input_mode", "manual_velocity"),
        pos0=pos0,
        vel0=vel0,
        ball=cfg_dict.get("ball", {}),
        environment=cfg_dict.get("environment", {}),
        stadium=cfg_dict.get("stadium", {}),
        fielding=fielding_data,
        solver=cfg_dict.get("solver", {}),
    )
    config.sync_velocity_and_angles()

    res_obj, trace, res_multibounce, outcome = sim_service.run_simulation(config)

    now = datetime.now()
    base_exp_id = f"EXP_{now.strftime('%Y%m%d_%H%M%S')}"
    exp_id = base_exp_id
    if exp_service.get_experiment(exp_id):
        exp_id = f"{base_exp_id}_{now.microsecond // 1000:03d}"
    record = ExperimentRecord(
        experiment_id=exp_id,
        name=name,
        description=description,
        created_at=now.isoformat(),
        tags=tags,
        config=config,
        results=res_obj,
        fingerprint=res_obj.fingerprint,
    )

    saved_id = exp_service.save_experiment(record, res_multibounce, trace)
    return {"status": "saved", "experiment_id": saved_id, "fingerprint": res_obj.fingerprint}


@router.delete("/{experiment_id}")
def delete_experiment(experiment_id: str):
    success = exp_service.delete_experiment(experiment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {"status": "deleted", "experiment_id": experiment_id}


@router.post("/{experiment_id}/duplicate")
def duplicate_experiment(experiment_id: str):
    dup = exp_service.duplicate_experiment(experiment_id)
    if not dup:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {"status": "duplicated", "experiment": dup.to_dict()}


@router.post("/{experiment_id}/render_video")
def render_experiment_video(experiment_id: str):
    """Renders broadcast MP4 video and saves it to the experiment's directory."""
    if experiment_id == "EXP_ACTIVE":
        all_exps = exp_service.list_experiments()
        if all_exps:
            experiment_id = all_exps[0]["id"]
        else:
            raise HTTPException(status_code=404, detail="No active experiment found to render")

    data = exp_service.get_experiment(experiment_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found")

    cfg_dict = data.get("config", {})
    config = ExperimentConfig(
        pos0=cfg_dict.get("pos0", [0.0, 0.0, 0.9]),
        vel0=cfg_dict.get("vel0", [28.0, 10.0, 6.2]),
        ball=cfg_dict.get("ball", {}),
        environment=cfg_dict.get("environment", {}),
        stadium=cfg_dict.get("stadium", {}),
        fielding=cfg_dict.get("fielding", {}),
    )

    res_obj, trace, res_multibounce, outcome = sim_service.run_simulation(config)

    exp_dir = os.path.join(exp_service.base_dir, experiment_id)
    videos_dir = os.path.join(exp_dir, "videos")
    os.makedirs(videos_dir, exist_ok=True)
    video_path = os.path.join(videos_dir, "simulation_presentation.mp4")
    gif_path = os.path.join(videos_dir, "simulation_presentation.gif")

    field_obj = CricketField(FieldConfig(boundary_radius_m=float(cfg_dict.get("stadium", {}).get("boundary_radius_m", 70.0))))

    raw_fielders = cfg_dict.get("fielding", {}).get("fielders", [])
    fielders_list = [
        FielderPosition(
            fielder_id=str(f.get("fielder_id") or f.get("id") or f"fielder_{i+1}"),
            role_name=str(f.get("role_name") or f.get("name") or "Fielder"),
            x_m=float(f.get("x_m", f.get("x", 0.0))),
            y_m=float(f.get("y_m", f.get("y", 0.0))),
        )
        for i, f in enumerate(raw_fielders)
    ]

    video_meta = {
        "input_data": {
            "delivery_id": experiment_id,
            "created_at": data.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M")),
            "v0_str": f"[{config.vel0[0]:.1f}, {config.vel0[1]:.1f}, {config.vel0[2]:.1f}]",
            "launch_speed_kmh": f"{config.speed0_kmh}",
            "elevation_deg": f"{config.elevation_deg}",
            "azimuth_deg": f"{config.azimuth_deg}",
        },
        "pipeline_params": {
            "mass_dia": f"{config.ball.get('mass_kg', 0.16)*1000:.0f}g / {config.ball.get('diameter_m', 0.0725)*1000:.1f}mm",
            "cd": f"{config.environment.get('constant_cd', 0.32)}",
            "en": f"{config.environment.get('restitution_normal', 0.55)}",
            "mu_roll": f"{config.environment.get('rolling_resistance_coeff', 0.20)}",
            "boundary_r": f"{field_obj.radius_m:.1f} m",
        },
        "results_data": {
            "d_pitch": f"{res_obj.carry_distance_m:.1f}",
            "apex": f"{res_obj.max_height_m:.2f}",
            "d_total": f"{res_obj.total_distance_m:.1f}",
            "d_roll": f"{res_obj.post_bounce_roll_m:.1f}",
            "d_unconstrained": f"{res_obj.unconstrained_rollout_m:.1f}" if res_obj.unconstrained_rollout_m else f"{res_obj.total_distance_m:.1f}",
            "rope_clearance": f"{abs(res_obj.margin_to_rope_m):.1f}m short" if not res_obj.clears_rope else "Cleared",
            "outcome_call": res_obj.outcome_call,
        }
    }

    generate_single_video_animation(
        res_multibounce,
        outcome=outcome,
        field=field_obj,
        fielders=fielders_list,
        output_mp4_path=video_path,
        output_gif_path=gif_path,
        scenario_title=f"{data.get('name', experiment_id)} (Analytical Hawkeye)",
        pipeline_metadata=video_meta,
        fps=20,
        max_duration_s=min(res_multibounce.time_s[-1], 4.5),
        dpi=105,
    )

    if "artifacts" not in data:
        data["artifacts"] = {}
    data["artifacts"]["video_mp4"] = os.path.relpath(video_path, exp_service.base_dir)
    data["artifacts"]["video_gif"] = os.path.relpath(gif_path, exp_service.base_dir)
    with open(os.path.join(exp_dir, "experiment.json"), "w", encoding="utf-8") as f:
        import json
        json.dump(data, f, indent=2)

    cache_buster = int(datetime.now().timestamp())
    mp4_url = f"/artifacts/{experiment_id}/videos/simulation_presentation.mp4?v={cache_buster}"
    gif_url = f"/artifacts/{experiment_id}/videos/simulation_presentation.gif?v={cache_buster}"
    exp_service.update_video_urls(experiment_id, mp4_url=mp4_url, gif_url=gif_url)

    return {
        "status": "video_generated",
        "experiment_id": experiment_id,
        "video_mp4": data["artifacts"]["video_mp4"],
        "video_gif": data["artifacts"]["video_gif"],
        "video_url": mp4_url,
    }


@router.get("/gallery/videos")
def get_video_gallery():
    """Lists all experiments (seeded match deliveries and custom runs) for interactive gallery display."""
    items = []
    base_dir = exp_service.base_dir
    cache_buster = int(datetime.now().timestamp())

    for exp in exp_service.list_experiments():
        exp_id = exp["id"]
        v_path = os.path.join(base_dir, exp_id, "videos", "simulation_presentation.mp4")
        g_path = os.path.join(base_dir, exp_id, "videos", "simulation_presentation.gif")
        has_video = os.path.exists(v_path)
        items.append({
            "experiment_id": exp_id,
            "name": exp.get("name", exp_id),
            "created_at": exp.get("created_at", ""),
            "launch_speed_kmh": exp.get("launch_speed_kmh", 0.0),
            "elevation_deg": exp.get("elevation_deg", 0.0),
            "azimuth_deg": exp.get("azimuth_deg", 0.0),
            "outcome_call": exp.get("outcome_call", "IN_PLAY"),
            "total_distance_m": exp.get("total_distance_m", 0.0),
            "max_height_m": exp.get("max_height_m", 0.0),
            "has_video": has_video,
            "video_url": f"/artifacts/{exp_id}/videos/simulation_presentation.mp4?v={cache_buster}" if has_video else None,
            "gif_url": f"/artifacts/{exp_id}/videos/simulation_presentation.gif?v={cache_buster}" if os.path.exists(g_path) else None,
            "is_seeded_delivery": exp.get("is_seeded_delivery", False),
        })
    return {"videos": items, "total": len(items)}


@router.post("/{experiment_id}/upload_clip")
async def upload_ground_truth_clip(experiment_id: str, request: Request):
    """Uploads an optional ground truth video clip (e.g. match camera footage) for the experiment."""
    exp_dir = os.path.join(exp_service.base_dir, experiment_id)
    if not os.path.exists(exp_dir):
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found")

    videos_dir = os.path.join(exp_dir, "videos")
    os.makedirs(videos_dir, exist_ok=True)
    dest_path = os.path.join(videos_dir, "ground_truth_clip.mp4")

    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.json()
            b64_data = body.get("video_base64") or body.get("clip_data", "")
            if "," in b64_data:
                b64_data = b64_data.split(",", 1)[1]
            video_bytes = base64.b64decode(b64_data)
            with open(dest_path, "wb") as f:
                f.write(video_bytes)
        else:
            # Direct binary stream from file upload
            with open(dest_path, "wb") as f:
                async for chunk in request.stream():
                    f.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video clip: {str(e)}")

    meta_path = os.path.join(exp_dir, "experiment.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                exp_data = json.load(f)
            if "artifacts" not in exp_data:
                exp_data["artifacts"] = {}
            exp_data["artifacts"]["ground_truth_clip"] = f"{experiment_id}/videos/ground_truth_clip.mp4"
            exp_data["has_ground_truth_clip"] = True
            exp_data["ground_truth_clip_url"] = f"/artifacts/{experiment_id}/videos/ground_truth_clip.mp4"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(exp_data, f, indent=2)
        except Exception:
            pass

    cache_buster = int(time.time())
    return {
        "status": "clip_uploaded",
        "experiment_id": experiment_id,
        "ground_truth_clip_url": f"/artifacts/{experiment_id}/videos/ground_truth_clip.mp4?v={cache_buster}"
    }
