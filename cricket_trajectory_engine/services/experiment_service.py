"""
Experiment Service: Manages persistence, directory structures,
SQLite relational database storage, and retrieval.
"""

import os
import csv
import json
import shutil
import sqlite3
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from cricket_trajectory_engine.models.experiment import (
    ExperimentRecord,
    ExperimentConfig,
    ExperimentResult,
    compute_simulation_fingerprint,
)
from cricket_trajectory_engine.core.calculation_trace import CalculationTrace
from cricket_trajectory_engine.physics.ground_collision import MultiBounceResult


class ExperimentService:
    def __init__(self, base_dir: str = "experiments"):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)
        self.db_path = os.path.join(self.base_dir, "experiments.db")
        self.index_file = os.path.join(self.base_dir, "experiments_index.json")
        self.cache_file = os.path.join(self.base_dir, "cache_index.json")
        self._ensure_indices()
        self._init_db()
        self.sync_from_disk()

    def _ensure_indices(self) -> None:
        if not os.path.exists(self.index_file):
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump([], f)
        if not os.path.exists(self.cache_file):
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _init_db(self) -> None:
        """Initializes the SQLite schema for relational storage and fast queries."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                input_mode TEXT DEFAULT 'manual_velocity',
                launch_speed_kmh REAL DEFAULT 0.0,
                elevation_deg REAL DEFAULT 0.0,
                azimuth_deg REAL DEFAULT 0.0,
                v0_x REAL DEFAULT 0.0,
                v0_y REAL DEFAULT 0.0,
                v0_z REAL DEFAULT 0.0,
                pos0_x REAL DEFAULT 0.0,
                pos0_y REAL DEFAULT 0.0,
                pos0_z REAL DEFAULT 0.9,
                ball_mass_kg REAL DEFAULT 0.156,
                ball_diameter_m REAL DEFAULT 0.072,
                drag_model TEXT DEFAULT 'constant',
                cd REAL DEFAULT 0.32,
                restitution REAL DEFAULT 0.50,
                friction REAL DEFAULT 0.35,
                rolling_coeff REAL DEFAULT 0.10,
                boundary_radius_m REAL DEFAULT 70.0,
                carry_distance_m REAL DEFAULT 0.0,
                total_distance_m REAL DEFAULT 0.0,
                max_height_m REAL DEFAULT 0.0,
                outcome_call TEXT DEFAULT 'IN_PLAY',
                clears_rope INTEGER DEFAULT 0,
                margin_to_rope_m REAL DEFAULT 0.0,
                has_ground_truth_clip INTEGER DEFAULT 0,
                ground_truth_clip_url TEXT,
                video_mp4_url TEXT,
                video_gif_url TEXT,
                is_seeded_delivery INTEGER DEFAULT 0,
                tags TEXT DEFAULT '[]',
                config_json TEXT,
                results_json TEXT,
                calculation_trace_json TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _get_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def sync_from_disk(self) -> None:
        """Scans disk directories and synchronizes records into SQLite."""
        if not os.path.exists(self.base_dir):
            return

        disk_exp_ids = set()
        for folder_name in os.listdir(self.base_dir):
            exp_dir = os.path.join(self.base_dir, folder_name)
            meta_path = os.path.join(exp_dir, "experiment.json")
            if not os.path.isdir(exp_dir) or folder_name.startswith(".") or not os.path.exists(meta_path):
                continue
            disk_exp_ids.add(folder_name)

        conn = self._get_db()
        cur = conn.cursor()

        # Remove any database records whose disk folders were deleted
        cur.execute("SELECT id FROM experiments")
        db_ids = {row["id"] for row in cur.fetchall()}
        stale_ids = db_ids - disk_exp_ids
        for stale_id in stale_ids:
            cur.execute("DELETE FROM experiments WHERE id = ?", (stale_id,))

        # Insert or update each disk record
        for exp_id in disk_exp_ids:
            exp_dir = os.path.join(self.base_dir, exp_id)
            meta_path = os.path.join(exp_dir, "experiment.json")
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                cfg = data.get("config") or {}
                res = data.get("results") or {}
                real_id = data.get("experiment_id", exp_id)
                tags = data.get("tags", [])
                is_delivery = 1 if ("DELIVERY_" in real_id or "real_delivery" in tags) else 0

                gt_path = os.path.join(exp_dir, "videos", "ground_truth_clip.mp4")
                has_gt = 1 if os.path.exists(gt_path) else 0
                gt_url = f"/artifacts/{exp_id}/videos/ground_truth_clip.mp4" if has_gt else None

                mp4_path = os.path.join(exp_dir, "videos", "simulation_presentation.mp4")
                has_mp4 = 1 if os.path.exists(mp4_path) else 0
                mp4_url = f"/artifacts/{exp_id}/videos/simulation_presentation.mp4" if has_mp4 else None

                gif_path = os.path.join(exp_dir, "videos", "simulation_presentation.gif")
                has_gif = 1 if os.path.exists(gif_path) else 0
                gif_url = f"/artifacts/{exp_id}/videos/simulation_presentation.gif" if has_gif else None

                pos0 = cfg.get("pos0", [0.0, 0.0, 0.9])
                vel0 = cfg.get("vel0", [0.0, 0.0, 0.0])

                cur.execute("""
                    INSERT OR REPLACE INTO experiments (
                        id, name, description, created_at, input_mode,
                        launch_speed_kmh, elevation_deg, azimuth_deg,
                        v0_x, v0_y, v0_z, pos0_x, pos0_y, pos0_z,
                        ball_mass_kg, ball_diameter_m, drag_model, cd,
                        restitution, friction, rolling_coeff, boundary_radius_m,
                        carry_distance_m, total_distance_m, max_height_m,
                        outcome_call, clears_rope, margin_to_rope_m,
                        has_ground_truth_clip, ground_truth_clip_url,
                        video_mp4_url, video_gif_url, is_seeded_delivery,
                        tags, config_json, results_json, updated_at
                    ) VALUES (
                        ?, ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, ?,
                        ?, ?, ?,
                        ?, ?, ?, ?
                    )
                """, (
                    real_id, data.get("name", exp_id), data.get("description", ""),
                    data.get("created_at", datetime.now().isoformat()),
                    cfg.get("input_mode", "manual_velocity"),
                    cfg.get("speed0_kmh", 0.0), cfg.get("elevation_deg", 0.0), cfg.get("azimuth_deg", 0.0),
                    vel0[0] if len(vel0) > 0 else 0.0,
                    vel0[1] if len(vel0) > 1 else 0.0,
                    vel0[2] if len(vel0) > 2 else 0.0,
                    pos0[0] if len(pos0) > 0 else 0.0,
                    pos0[1] if len(pos0) > 1 else 0.0,
                    pos0[2] if len(pos0) > 2 else 0.9,
                    cfg.get("ball", {}).get("mass_kg", 0.156),
                    cfg.get("ball", {}).get("diameter_m", 0.072),
                    cfg.get("environment", {}).get("drag_model", "constant"),
                    cfg.get("environment", {}).get("constant_cd", 0.32),
                    cfg.get("environment", {}).get("restitution_normal", 0.50),
                    cfg.get("environment", {}).get("friction_tangential", 0.35),
                    cfg.get("environment", {}).get("rolling_resistance_coeff", 0.10),
                    cfg.get("stadium", {}).get("boundary_radius_m", 70.0),
                    res.get("carry_distance_m", 0.0),
                    res.get("total_distance_m", 0.0),
                    res.get("max_height_m", 0.0),
                    res.get("outcome_call", "IN_PLAY"),
                    1 if res.get("clears_rope") else 0,
                    res.get("margin_to_rope_m", 0.0),
                    has_gt, gt_url,
                    mp4_url, gif_url, is_delivery,
                    json.dumps(tags), json.dumps(cfg), json.dumps(res),
                    datetime.now().isoformat()
                ))
            except Exception:
                continue

        conn.commit()
        conn.close()

    def _read_cache(self) -> Dict[str, str]:
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_cache(self, cache: Dict[str, str]) -> None:
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)

    def find_cached_experiment(self, fingerprint: str) -> Optional[str]:
        """Returns experiment_id if an identical physical simulation has already been computed."""
        cache = self._read_cache()
        exp_id = cache.get(fingerprint)
        if exp_id and os.path.exists(os.path.join(self.base_dir, exp_id, "results.json")):
            return exp_id
        return None

    def list_experiments(self) -> List[Dict[str, Any]]:
        """
        Returns structured list of all experiments from SQLite database.
        Seeded deliveries appear first in natural ascending order (DELIVERY_01_CAM1 ...),
        followed by custom experiments ordered by creation time descending.
        """
        conn = self._get_db()
        cur = conn.cursor()

        # 1. Fetch seeded match deliveries
        cur.execute("""
            SELECT * FROM experiments
            WHERE is_seeded_delivery = 1
            ORDER BY id ASC
        """)
        deliveries = [self._row_to_summary(dict(row)) for row in cur.fetchall()]

        # 2. Fetch custom user experiments
        cur.execute("""
            SELECT * FROM experiments
            WHERE is_seeded_delivery = 0
            ORDER BY created_at DESC, id DESC
        """)
        custom = [self._row_to_summary(dict(row)) for row in cur.fetchall()]

        conn.close()
        return deliveries + custom

    def _row_to_summary(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Maps an SQLite row dict to the API summary format."""
        exp_id = row["id"]
        tags = []
        try:
            tags = json.loads(row.get("tags") or "[]")
        except Exception:
            tags = []

        is_delivery = bool(row.get("is_seeded_delivery", 0))
        has_gt = bool(row.get("has_ground_truth_clip", 0))
        gt_url = row.get("ground_truth_clip_url")
        mp4_url = row.get("video_mp4_url")
        gif_url = row.get("video_gif_url")

        # Double check disk for videos if not recorded in DB
        if not mp4_url:
            disk_mp4 = os.path.join(self.base_dir, exp_id, "videos", "simulation_presentation.mp4")
            if os.path.exists(disk_mp4):
                mp4_url = f"/artifacts/{exp_id}/videos/simulation_presentation.mp4"
                gif_url = f"/artifacts/{exp_id}/videos/simulation_presentation.gif"

        return {
            "id": exp_id,
            "experiment_id": exp_id,
            "name": row.get("name") or exp_id,
            "description": row.get("description") or "",
            "created_at": row.get("created_at") or "",
            "fingerprint": "",
            "is_cached": False,
            "input_mode": row.get("input_mode") or "manual_velocity",
            "launch_speed_kmh": float(row.get("launch_speed_kmh") or 0.0),
            "elevation_deg": float(row.get("elevation_deg") or 0.0),
            "azimuth_deg": float(row.get("azimuth_deg") or 0.0),
            "outcome_call": row.get("outcome_call") or "IN_PLAY",
            "carry_distance_m": float(row.get("carry_distance_m") or 0.0),
            "total_distance_m": float(row.get("total_distance_m") or 0.0),
            "max_height_m": float(row.get("max_height_m") or 0.0),
            "clears_rope": bool(row.get("clears_rope") or 0),
            "margin_to_rope_m": float(row.get("margin_to_rope_m") or 0.0),
            "has_ground_truth_clip": has_gt,
            "ground_truth_clip_url": gt_url,
            "video_mp4_url": mp4_url,
            "video_gif_url": gif_url,
            "tags": tags,
            "is_seeded_delivery": is_delivery,
            "storage_engine": "sqlite"
        }

    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Loads complete experiment package including config, results, and calculation trace."""
        exp_dir = os.path.join(self.base_dir, experiment_id)
        meta_path = os.path.join(exp_dir, "experiment.json")
        if not os.path.exists(meta_path):
            return None

        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["id"] = data.get("experiment_id", experiment_id)

        # Attach calculation trace if available:
        trace_path = os.path.join(exp_dir, "calculation_trace.json")
        if os.path.exists(trace_path):
            try:
                with open(trace_path, "r", encoding="utf-8") as f:
                    data["calculation_trace"] = json.load(f)
            except Exception:
                data["calculation_trace"] = None

        # Attach downsampled trajectory points from CSV if available:
        csv_path = os.path.join(exp_dir, "trajectory.csv")
        if os.path.exists(csv_path):
            pts = []
            try:
                with open(csv_path, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    next(reader, None)  # header
                    for row in reader:
                        if len(row) >= 7:
                            pts.append([float(x) for x in row[:7]])
                if pts:
                    n_p = len(pts)
                    if n_p <= 250:
                        data["trajectory"] = pts
                    else:
                        step = max(1, n_p // 200)
                        sampled = pts[::step]
                        if (n_p - 1) % step != 0:
                            sampled.append(pts[-1])
                        data["trajectory"] = sampled
            except Exception:
                data["trajectory"] = []

        # Attach ground truth clip if available:
        gt_clip_path = os.path.join(exp_dir, "videos", "ground_truth_clip.mp4")
        if os.path.exists(gt_clip_path):
            data["has_ground_truth_clip"] = True
            data["ground_truth_clip_url"] = f"/artifacts/{experiment_id}/videos/ground_truth_clip.mp4"
        else:
            data["has_ground_truth_clip"] = False
            data["ground_truth_clip_url"] = None

        # Attach video presentation if available:
        video_path = os.path.join(exp_dir, "videos", "simulation_presentation.mp4")
        if os.path.exists(video_path):
            data["video_mp4_url"] = f"/artifacts/{experiment_id}/videos/simulation_presentation.mp4"
            data["video_gif_url"] = f"/artifacts/{experiment_id}/videos/simulation_presentation.gif"

        return data

    def save_experiment(
        self,
        record: ExperimentRecord,
        multi_bounce_res: MultiBounceResult,
        trace: CalculationTrace,
    ) -> str:
        """Saves experiment JSON, trajectory CSV, calculation trace, and inserts into SQLite database."""
        exp_id = record.experiment_id
        exp_dir = os.path.join(self.base_dir, exp_id)
        os.makedirs(exp_dir, exist_ok=True)
        os.makedirs(os.path.join(exp_dir, "visualizations"), exist_ok=True)
        os.makedirs(os.path.join(exp_dir, "videos"), exist_ok=True)

        # 1. Save trajectory CSV:
        csv_path = os.path.join(exp_dir, "trajectory.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["time_s", "x_m", "y_m", "z_m", "vx_m_s", "vy_m_s", "vz_m_s"])
            for t, p, v in zip(multi_bounce_res.time_s, multi_bounce_res.positions_m, multi_bounce_res.velocities_m_s):
                writer.writerow([
                    f"{t:.4f}", f"{p[0]:.4f}", f"{p[1]:.4f}", f"{p[2]:.4f}",
                    f"{v[0]:.4f}", f"{v[1]:.4f}", f"{v[2]:.4f}"
                ])
        record.artifacts["trajectory_csv"] = os.path.relpath(csv_path, self.base_dir)

        # 2. Save calculation trace JSON:
        trace_path = os.path.join(exp_dir, "calculation_trace.json")
        trace.save_json(trace_path)
        record.artifacts["calculation_trace"] = os.path.relpath(trace_path, self.base_dir)

        # 3. Save configuration & results:
        cfg_dict = record.config.to_dict()
        with open(os.path.join(exp_dir, "configuration.json"), "w", encoding="utf-8") as f:
            json.dump(cfg_dict, f, indent=2)

        res_dict = record.results.to_dict() if record.results else {}
        if record.results:
            with open(os.path.join(exp_dir, "results.json"), "w", encoding="utf-8") as f:
                json.dump(res_dict, f, indent=2)

        # 4. Save main experiment record:
        meta_path = os.path.join(exp_dir, "experiment.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, indent=2)

        # 5. Insert into SQLite:
        is_delivery = 1 if ("DELIVERY_" in exp_id or "real_delivery" in record.tags) else 0
        gt_clip_path = os.path.join(exp_dir, "videos", "ground_truth_clip.mp4")
        has_gt = 1 if os.path.exists(gt_clip_path) else 0
        gt_url = f"/artifacts/{exp_id}/videos/ground_truth_clip.mp4" if has_gt else None

        mp4_path = os.path.join(exp_dir, "videos", "simulation_presentation.mp4")
        has_mp4 = 1 if os.path.exists(mp4_path) else 0
        mp4_url = f"/artifacts/{exp_id}/videos/simulation_presentation.mp4" if has_mp4 else None

        gif_path = os.path.join(exp_dir, "videos", "simulation_presentation.gif")
        has_gif = 1 if os.path.exists(gif_path) else 0
        gif_url = f"/artifacts/{exp_id}/videos/simulation_presentation.gif" if has_gif else None

        pos0 = record.config.pos0 or [0.0, 0.0, 0.9]
        vel0 = record.config.vel0 or [0.0, 0.0, 0.0]

        conn = self._get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO experiments (
                id, name, description, created_at, input_mode,
                launch_speed_kmh, elevation_deg, azimuth_deg,
                v0_x, v0_y, v0_z, pos0_x, pos0_y, pos0_z,
                ball_mass_kg, ball_diameter_m, drag_model, cd,
                restitution, friction, rolling_coeff, boundary_radius_m,
                carry_distance_m, total_distance_m, max_height_m,
                outcome_call, clears_rope, margin_to_rope_m,
                has_ground_truth_clip, ground_truth_clip_url,
                video_mp4_url, video_gif_url, is_seeded_delivery,
                tags, config_json, results_json, calculation_trace_json, updated_at
            ) VALUES (
                ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?, ?
            )
        """, (
            exp_id, record.name, record.description, record.created_at,
            record.config.input_mode or "manual_velocity",
            record.config.speed0_kmh if record.config.speed0_kmh is not None else 0.0,
            record.config.elevation_deg if record.config.elevation_deg is not None else 0.0,
            record.config.azimuth_deg if record.config.azimuth_deg is not None else 0.0,
            vel0[0] if len(vel0) > 0 else 0.0,
            vel0[1] if len(vel0) > 1 else 0.0,
            vel0[2] if len(vel0) > 2 else 0.0,
            pos0[0] if len(pos0) > 0 else 0.0,
            pos0[1] if len(pos0) > 1 else 0.0,
            pos0[2] if len(pos0) > 2 else 0.9,
            record.config.ball.get("mass_kg", 0.156),
            record.config.ball.get("diameter_m", 0.072),
            record.config.environment.get("drag_model", "constant"),
            record.config.environment.get("constant_cd", 0.32),
            record.config.environment.get("restitution_normal", 0.50),
            record.config.environment.get("friction_tangential", 0.35),
            record.config.environment.get("rolling_resistance_coeff", 0.10),
            record.config.stadium.get("boundary_radius_m", 70.0),
            res_dict.get("carry_distance_m", 0.0),
            res_dict.get("total_distance_m", 0.0),
            res_dict.get("max_height_m", 0.0),
            res_dict.get("outcome_call", "IN_PLAY"),
            1 if res_dict.get("clears_rope") else 0,
            res_dict.get("margin_to_rope_m", 0.0),
            has_gt, gt_url,
            mp4_url, gif_url, is_delivery,
            json.dumps(record.tags), json.dumps(cfg_dict), json.dumps(res_dict),
            json.dumps(trace.to_dict()), datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()

        # 6. Register in cache:
        if record.fingerprint:
            cache = self._read_cache()
            cache[record.fingerprint] = exp_id
            self._write_cache(cache)

        return exp_id

    def update_video_urls(self, experiment_id: str, mp4_url: Optional[str] = None, gif_url: Optional[str] = None) -> None:
        """Updates video URLs for an experiment in the SQLite database."""
        conn = self._get_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE experiments
            SET video_mp4_url = COALESCE(?, video_mp4_url),
                video_gif_url = COALESCE(?, video_gif_url),
                updated_at = ?
            WHERE id = ?
        """, (mp4_url, gif_url, datetime.now().isoformat(), experiment_id))
        conn.commit()
        conn.close()

    def delete_experiment(self, experiment_id: str) -> bool:
        """Deletes experiment folder from disk and removes its record from SQLite."""
        exp_dir = os.path.join(self.base_dir, experiment_id)
        deleted = False
        if os.path.exists(exp_dir):
            shutil.rmtree(exp_dir)
            deleted = True

        conn = self._get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM experiments WHERE id = ?", (experiment_id,))
        if cur.rowcount > 0:
            deleted = True
        conn.commit()
        conn.close()

        # Remove from cache:
        cache = self._read_cache()
        updated_cache = {k: v for k, v in cache.items() if v != experiment_id}
        self._write_cache(updated_cache)
        return deleted

    def duplicate_experiment(self, experiment_id: str, new_name: Optional[str] = None) -> Optional[ExperimentRecord]:
        """Duplicates experiment directory, updates SQLite record, and returns duplicated record."""
        source = self.get_experiment(experiment_id)
        if not source:
            return None
        new_id = f"EXP_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        src_dir = os.path.join(self.base_dir, experiment_id)
        dst_dir = os.path.join(self.base_dir, new_id)
        if os.path.exists(src_dir):
            shutil.copytree(src_dir, dst_dir)
            meta_path = os.path.join(dst_dir, "experiment.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                meta["experiment_id"] = new_id
                meta["id"] = new_id
                meta["name"] = new_name or f"Copy of {source.get('name', experiment_id)}"
                meta["created_at"] = datetime.now().isoformat()
                meta["tags"] = ["duplicate"] + meta.get("tags", [])
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2)

        cfg_dict = source.get("config", {})
        cfg = ExperimentConfig(
            input_mode=cfg_dict.get("input_mode", "manual_velocity"),
            pos0=cfg_dict.get("pos0", [0, 0, 0.9]),
            vel0=cfg_dict.get("vel0", [28, 10, 6.2]),
            ball=cfg_dict.get("ball", {}),
            environment=cfg_dict.get("environment", {}),
            stadium=cfg_dict.get("stadium", {}),
            fielding=cfg_dict.get("fielding", {}),
            solver=cfg_dict.get("solver", {}),
        )
        cfg.sync_velocity_and_angles()

        # Sync newly copied folder into SQLite
        self.sync_from_disk()

        return ExperimentRecord(
            experiment_id=new_id,
            name=new_name or f"Copy of {source.get('name', experiment_id)}",
            description=f"Duplicated from {experiment_id}",
            created_at=datetime.now().isoformat(),
            config=cfg,
            tags=["duplicate"] + source.get("tags", []),
        )
