"""
Comparison Service: Multi-experiment comparative analytics,
parameter sweep comparisons, and ground-truth validation.
"""

import math
from typing import List, Dict, Any, Optional
import numpy as np


class ComparisonService:
    def compare_experiments(self, experiments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Performs side-by-side comparative analysis across multiple experiments."""
        if not experiments:
            return {"error": "No experiments provided for comparison"}

        comparison_table = []
        for exp in experiments:
            exp_id = exp.get("experiment_id", "")
            name = exp.get("name", exp_id)
            cfg = exp.get("config", {})
            res = exp.get("results") or {}
            env = cfg.get("environment", {})
            ball = cfg.get("ball", {})

            # Robust extraction of launch angles and speed (from config or vel0)
            speed_kmh = cfg.get("speed0_kmh")
            elev_deg = cfg.get("elevation_deg")
            azim_deg = cfg.get("azimuth_deg")

            if speed_kmh is None or elev_deg is None or azim_deg is None:
                vel0 = cfg.get("vel0", [0.0, 0.0, 0.0])
                if len(vel0) >= 3:
                    vx, vy, vz = float(vel0[0]), float(vel0[1]), float(vel0[2])
                    vxy = math.hypot(vx, vy)
                    spd = math.hypot(vxy, vz)
                    if speed_kmh is None:
                        speed_kmh = round(spd * 3.6, 2)
                    if elev_deg is None:
                        elev_deg = round(math.degrees(math.atan2(vz, vxy)), 2)
                    if azim_deg is None:
                        azim_deg = round(math.degrees(math.atan2(vy, vx)), 2)

            cd_val = env.get("constant_cd")
            if cd_val is None:
                cd_val = env.get("cd", 0.32)

            restit_val = env.get("restitution_normal")
            if restit_val is None:
                restit_val = env.get("restitution_coeff", 0.55)

            wind_vec = env.get("wind_vector_m_s")
            if wind_vec is None:
                wind_vec = env.get("wind_vector", [0.0, 0.0, 0.0])

            comparison_table.append({
                "experiment_id": exp_id,
                "name": name,
                "launch_speed_kmh": round(float(speed_kmh or 0.0), 2),
                "elevation_deg": round(float(elev_deg or 0.0), 2),
                "azimuth_deg": round(float(azim_deg or 0.0), 2),
                "drag_coefficient_cd": round(float(cd_val or 0.32), 3),
                "restitution_en": round(float(restit_val or 0.55), 3),
                "wind_m_s": wind_vec,
                "carry_distance_m": round(float(res.get("carry_distance_m", 0.0)), 2),
                "apex_height_m": round(float(res.get("max_height_m", 0.0)), 2),
                "flight_time_s": round(float(res.get("flight_time_s", 0.0)), 2),
                "post_bounce_roll_m": round(float(res.get("post_bounce_roll_m", 0.0)), 2),
                "total_distance_m": round(float(res.get("total_distance_m", 0.0)), 2),
                "clears_rope": bool(res.get("clears_rope", False)),
                "margin_to_rope_m": round(float(res.get("margin_to_rope_m", 0.0)), 2),
                "outcome_call": res.get("outcome_call", "PENDING"),
                "estimated_runs": int(res.get("estimated_runs", 0)),
            })

        # Calculate deltas relative to baseline (first experiment):
        baseline = comparison_table[0]
        deltas = []
        for item in comparison_table:
            carry_delta = round(item["carry_distance_m"] - baseline["carry_distance_m"], 2)
            apex_delta = round(item["apex_height_m"] - baseline["apex_height_m"], 2)
            dist_delta = round(item["total_distance_m"] - baseline["total_distance_m"], 2)
            time_delta = round(item["flight_time_s"] - baseline["flight_time_s"], 2)
            speed_delta = round(item["launch_speed_kmh"] - baseline["launch_speed_kmh"], 2)
            elev_delta = round(item["elevation_deg"] - baseline["elevation_deg"], 2)
            azim_delta = round(item["azimuth_deg"] - baseline["azimuth_deg"], 2)
            roll_delta = round(item["post_bounce_roll_m"] - baseline["post_bounce_roll_m"], 2)
            cd_delta = round(item["drag_coefficient_cd"] - baseline["drag_coefficient_cd"], 3)
            en_delta = round(item["restitution_en"] - baseline["restitution_en"], 3)

            delta_dict = {
                "experiment_id": item["experiment_id"],
                "name": item["name"],
                "delta_carry_m": carry_delta,
                "delta_apex_m": apex_delta,
                "delta_max_height_m": apex_delta,  # Backward compatibility alias
                "delta_total_dist_m": dist_delta,
                "delta_horizontal_distance_m": dist_delta,  # Backward compatibility alias
                "delta_flight_time_s": time_delta,
                "delta_speed_kmh": speed_delta,
                "delta_elevation_deg": elev_delta,
                "delta_azimuth_deg": azim_delta,
                "delta_post_bounce_roll_m": roll_delta,
                "delta_drag_coefficient_cd": cd_delta,
                "delta_restitution_en": en_delta,
                "baseline_outcome": baseline["outcome_call"],
                "comparison_outcome": item["outcome_call"],
                "baseline_name": baseline["name"],
                "comparison_name": item["name"],
            }
            deltas.append(delta_dict)

        deltas_map = {d["experiment_id"]: d for d in deltas}

        # Structure experiments payload for 2D trajectory plotting
        experiments_payload = []
        for exp in experiments:
            exp_id = exp.get("experiment_id") or exp.get("id", "")
            res = exp.get("results") or {}
            cfg = exp.get("config") or {}
            traj = exp.get("trajectory") or []
            outcome = res.get("outcome_call") or "IN_PLAY"
            experiments_payload.append({
                "experiment_id": exp_id,
                "id": exp_id,
                "name": exp.get("name") or exp_id,
                "trajectory": traj,
                "summary": {
                    "outcome": outcome,
                    "max_height_m": res.get("max_height_m", 0.0),
                    "total_distance_m": res.get("total_distance_m", 0.0),
                    "carry_distance_m": res.get("carry_distance_m", 0.0),
                    "flight_time_s": res.get("flight_time_s", 0.0),
                },
                "results": res,
                "config": cfg,
            })

        return {
            "total_compared": len(experiments),
            "comparison_table": comparison_table,
            "deltas_vs_baseline": deltas,
            "deltas_map": deltas_map,
            "baseline_experiment_id": baseline["experiment_id"],
            "experiments": experiments_payload,
        }

    def evaluate_ground_truth_accuracy(
        self,
        predicted_res: Dict[str, Any],
        measured_ground_truth: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Evaluates prediction accuracy against real measured match outcomes.
        Distinguishes between initial frame fitting agreement and true future outcome prediction.
        """
        eval_metrics = {}
        pred_carry = predicted_res.get("carry_distance_m", 0.0)
        meas_carry = measured_ground_truth.get("carry_distance_m")
        if meas_carry is not None:
            eval_metrics["carry_error_m"] = round(pred_carry - float(meas_carry), 2)
            eval_metrics["carry_pct_error"] = round(abs(pred_carry - float(meas_carry)) / float(meas_carry) * 100, 1)

        pred_apex = predicted_res.get("max_height_m", 0.0)
        meas_apex = measured_ground_truth.get("max_height_m")
        if meas_apex is not None:
            eval_metrics["apex_error_m"] = round(pred_apex - float(meas_apex), 2)

        pred_outcome = predicted_res.get("outcome_call", "")
        meas_outcome = measured_ground_truth.get("outcome_call", "")
        if meas_outcome:
            eval_metrics["outcome_correct"] = (pred_outcome.upper() == meas_outcome.upper())

        return eval_metrics

