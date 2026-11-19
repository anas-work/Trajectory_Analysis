#!/usr/bin/env python3
"""
Batch Cricket Trajectory-Pose Fusion Shot Classification & Biomechanical Evaluation Study
for 3d_hits_39_more_deliveries.

Processes all 39 deliveries:
1. Tracks striker batter at the crease across all frames (filtering out foreground bowler).
2. Extracts biomechanical features (stride, knee flexion, torso inclination, relative shoulder rotation, elbow angles).
3. Segments 6 temporal shot phases (Stance, Backswing, Stride, Execution, Impact Interval, Follow-through).
4. Fuses ball azimuth and batter pose into distinct outputs:
   - Shot Type (from 27+ stroke cricket catalog)
   - Footwork (Front-foot, Back-foot, Neutral)
   - Trajectory Category (Grounded, Lofted)
   - Shot Direction Sector (Straight, Off side, Leg side, Square of the wicket, Behind square)
5. Renders native aspect ratio, web-compatible (H.264 avc1 yuv420p faststart) analytical HUD videos.
6. Generates 4-panel movement kinematics graphs.
7. Exports consolidated results to CSV and JSON, and copies web assets to frontend.
"""

from __future__ import annotations

import csv
import glob
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXP_DIR = ROOT / "experiments" / "batter_shot_classification"
if str(EXP_DIR) not in sys.path:
    sys.path.insert(0, str(EXP_DIR))

os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib_cache"
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import onnxruntime as ort
import imageio_ffmpeg

from infer_pose_onnx_occluded import (
    PLAYER_CLASS_ID,
    letterbox,
    postprocess,
    restore_coordinates,
    keypoint_states,
    OCCLUDED_COLOR,
)

from pose_features import (
    extract_kinematic_features,
    segment_batting_phases,
)
from shot_classifier import (
    classify_shot_fusion,
    compute_batter_relative_azimuth,
    determine_shot_direction_sector,
)

MODEL_PATH = ROOT / "yolov9s_pose_v1.3_input640.onnx"
DATASET_DIR = ROOT / "3d_hits_39_more_deliveries"
DATA_DIR = EXP_DIR / "data"
VIDEOS_DIR = EXP_DIR / "videos"
PLOTS_DIR = EXP_DIR / "plots"
SUMMARY_TRAJ_CSV = ROOT / "cricket_trajectory_engine" / "data" / "real_deliveries_videos" / "real_39_deliveries_cam1_cam2_summary.csv"


class PoseTracker:
    def __init__(self, onnx_path: Path):
        self.session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name

    def infer_frame(self, frame: np.ndarray):
        padded, gain, pad = letterbox(frame, 640, 640)
        blob = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB).transpose(2, 0, 1)[None].astype(np.float32) / 255.0
        preds = self.session.run(None, {self.input_name: blob})[0][0]
        dets = postprocess(preds)
        restore_coordinates(dets, gain, pad, frame.shape)
        return dets


def select_batter(dets: list, prev_box: np.ndarray | None, frame_shape: tuple, crease_anchor: tuple | None = None) -> tuple | None:
    """Select the striker batter based on bounding box geometry, crease proximity, and IoU tracking."""
    players = [d for d in dets if d[2] == PLAYER_CLASS_ID and d[1] > 0.15]
    if not players:
        return None

    # Filter out foreground bowler:
    striker_candidates = []
    for p in players:
        box = p[0]
        w = box[2] - box[0]
        h = box[3] - box[1]
        area = w * h
        cx = (box[0] + box[2]) / 2.0
        cy = (box[1] + box[3]) / 2.0

        # Reject foreground bowler
        if area > 280000 or h > 750 or w > 420:
            continue

        # If crease_anchor is known, reject detections too far (> 700 px) from crease
        if crease_anchor is not None and crease_anchor[0] is not None:
            dist_to_anchor = np.hypot(cx - crease_anchor[0], cy - crease_anchor[1])
            if dist_to_anchor > 700:
                continue

        striker_candidates.append(p)

    if not striker_candidates:
        fallback = [p for p in players if (p[0][2] - p[0][0]) * (p[0][3] - p[0][1]) < 280000]
        if fallback:
            if crease_anchor is not None and crease_anchor[0] is not None:
                return min(fallback, key=lambda c: np.hypot(
                    (c[0][0] + c[0][2])/2 - crease_anchor[0],
                    (c[0][1] + c[0][3])/2 - crease_anchor[1]
                ))
            return max(fallback, key=lambda c: c[1])
        return None

    if prev_box is None:
        if crease_anchor is not None and crease_anchor[0] is not None:
            return min(striker_candidates, key=lambda c: np.hypot(
                (c[0][0] + c[0][2])/2 - crease_anchor[0],
                (c[0][1] + c[0][3])/2 - crease_anchor[1]
            ))
        return min(striker_candidates, key=lambda c: abs((c[0][0] + c[0][2])/2 - 1600))

    def score_candidate(c):
        bx = c[0]
        tl = np.maximum(prev_box[:2], bx[:2])
        br = np.minimum(prev_box[2:], bx[:2])
        inter = np.prod(np.maximum(br - tl, 0))
        a1 = (prev_box[2] - prev_box[0]) * (prev_box[3] - prev_box[1])
        a2 = (bx[2] - bx[0]) * (bx[3] - bx[1])
        union = a1 + a2 - inter
        iou = inter / union if union > 0 else 0.0

        c_prev = np.array([(prev_box[0] + prev_box[2]) / 2.0, (prev_box[1] + prev_box[3]) / 2.0])
        c_cur = np.array([(bx[0] + bx[2]) / 2.0, (bx[1] + bx[3]) / 2.0])
        dist = np.linalg.norm(c_cur - c_prev)
        return iou - (dist / 1000.0)

    return max(striker_candidates, key=score_candidate)


def draw_hud(
    frame: np.ndarray,
    fr_num: int,
    time_s: float,
    current_phase: str,
    cls_res: dict,
    batter_box: np.ndarray | None,
    kpts: np.ndarray | None,
) -> np.ndarray:
    """Draw professional broadcast analytical HUD with pose skeleton, ball sector, and multi-signal classification."""
    out = frame.copy()
    h, w = out.shape[:2]

    # Draw batter detection and skeleton if available
    if batter_box is not None and kpts is not None:
        bx1, by1, bx2, by2 = np.rint(batter_box).astype(int)
        cv2.rectangle(out, (bx1, by1), (bx2, by2), (0, 255, 180), 3)
        # Batsman label above box
        label_bg_y1 = max(0, by1 - 32)
        cv2.rectangle(out, (bx1, label_bg_y1), (bx1 + 290, by1), (15, 23, 42), -1)
        cv2.putText(out, "BATSMAN (STRIKER)", (bx1 + 8, by1 - 8),
                    cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 255, 180), 2, cv2.LINE_AA)

        points, skeleton, findable, visible, occluded = keypoint_states(0, kpts)
        for p1, p2 in skeleton:
            if findable[p1] and findable[p2]:
                pt1 = tuple(np.rint(points[p1, :2]).astype(int))
                pt2 = tuple(np.rint(points[p2, :2]).astype(int))
                cv2.line(out, pt1, pt2, (0, 240, 255), 3, cv2.LINE_AA)

        for idx in np.flatnonzero(visible):
            pt = tuple(np.rint(points[idx, :2]).astype(int))
            cv2.circle(out, pt, 5, (0, 255, 0), -1, cv2.LINE_AA)
        for idx in np.flatnonzero(occluded):
            pt = tuple(np.rint(points[idx, :2]).astype(int))
            cv2.circle(out, pt, 6, OCCLUDED_COLOR, -1, cv2.LINE_AA)

    # Broadcast Top Overlay Banner
    hud_h = 240
    overlay = out[:hud_h, :].copy()
    cv2.rectangle(overlay, (0, 0), (w, hud_h), (15, 23, 42), -1)
    cv2.addWeighted(overlay, 0.82, out[:hud_h, :], 0.18, 0, out[:hud_h, :])

    # Left Section: Engine & Timing
    cv2.putText(out, "CRICKET TRAJECTORY ENGINE | MULTI-SIGNAL FUSION CLASSIFIER", (40, 48),
                cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(out, f"FRAME: {fr_num:03d} | TIME: {time_s:5.2f}s", (40, 95),
                cv2.FONT_HERSHEY_SIMPLEX, 0.85, (148, 163, 184), 2, cv2.LINE_AA)

    phase_colors = {
        "STANCE": (148, 163, 184),
        "BACKSWING": (250, 204, 21),
        "STRIDE": (56, 189, 248),
        "EXECUTION": (251, 146, 60),
        "IMPACT": (239, 68, 68),
        "FOLLOW-THROUGH": (34, 197, 94),
    }
    col = phase_colors.get(current_phase.upper(), (255, 255, 255))
    cv2.putText(out, f"PHASE: [{current_phase.upper()}]", (40, 150),
                cv2.FONT_HERSHEY_DUPLEX, 1.15, col, 3, cv2.LINE_AA)
    cv2.putText(out, "TARGET: BATSMAN AT BATTING CREASE [BOWLER FILTERED OUT]", (40, 200),
                cv2.FONT_HERSHEY_SIMPLEX, 0.72, (34, 197, 94), 2, cv2.LINE_AA)

    # Right Section: Multi-Signal Fusion Classification Badges
    right_x = max(w - 1200, w // 2)
    alt_txt = f" (Alt: {cls_res['alternative_shot']})" if cls_res.get("alternative_shot") else ""
    cv2.putText(out, f"SHOT: {cls_res['shot_type'].upper()}{alt_txt}", (right_x, 50),
                cv2.FONT_HERSHEY_DUPLEX, 1.05, (0, 255, 200), 2, cv2.LINE_AA)
    
    cv2.putText(out, f"SIGNAL A (TRAJECTORY): Azim {cls_res['batter_azimuth_deg']:+.1f}° [{cls_res['sector_name']}] | Elev {cls_res['ball_elevation_deg']:+.1f}° ({cls_res['trajectory_category']})",
                (right_x, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (56, 189, 248), 2, cv2.LINE_AA)
    
    stride_val = cls_res["biomechanics"]["stride_ratio"]
    disp_val = cls_res["biomechanics"]["lead_disp_pitch_px"]
    cv2.putText(out, f"SIGNAL B (POSE): {cls_res['footwork'].upper()} (Stride {disp_val:+.1f}px, ratio {stride_val:.2f}x) | Torso {cls_res['biomechanics']['torso_inclination_deg']:.1f}° | Rot {cls_res['biomechanics']['shoulder_rot_deg']:.1f}°",
                (right_x, 148), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (250, 204, 21), 2, cv2.LINE_AA)
    
    cv2.putText(out, f"CONFIDENCE: {cls_res['confidence'] * 100:.0f}% | DIRECTION: {cls_res['shot_direction'].upper()} | SPEED: {cls_res['ball_speed_kmh']:.1f} km/h",
                (right_x, 195), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (226, 232, 240), 2, cv2.LINE_AA)

    return out


def plot_delivery_graphs(features: list[dict], phases: dict, del_id: str, out_path: Path):
    """Plot comprehensive 4-panel movement analysis graphs over time."""
    frames = [f["frame"] for f in features if f["valid"]]
    stride_ratios = [f["stride_ratio"] for f in features if f["valid"]]
    lead_knees = [f["lead_knee_flex"] for f in features if f["valid"]]
    trail_knees = [f["trail_knee_flex"] for f in features if f["valid"]]
    shoulder_angles = [f["shoulder_angle"] for f in features if f["valid"]]
    torso_incs = [f["torso_inclination"] for f in features if f["valid"]]
    wrist_speeds = [f["wrist_speed"] for f in features if f["valid"]]
    arm_extensions = [f["arm_extension"] for f in features if f["valid"]]

    fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)
    plt.subplots_adjust(hspace=0.25)

    def shade_phases(ax):
        if "stance" in phases:
            ax.axvspan(phases["stance"][0], phases["stance"][1], color="gray", alpha=0.15, label="Stance" if ax == axes[0] else None)
        if "backswing" in phases:
            ax.axvspan(phases["backswing"][0], phases["backswing"][1], color="gold", alpha=0.15, label="Backswing" if ax == axes[0] else None)
        if "stride" in phases:
            ax.axvspan(phases["stride"][0], phases["stride"][1], color="skyblue", alpha=0.15, label="Stride" if ax == axes[0] else None)
        if "execution" in phases:
            ax.axvspan(phases["execution"][0], phases["execution"][1], color="orange", alpha=0.15, label="Execution" if ax == axes[0] else None)
        if "impact_interval" in phases:
            ax.axvspan(phases["impact_interval"][0], phases["impact_interval"][1], color="red", alpha=0.35, label="Impact Window" if ax == axes[0] else None)
        if "follow_through" in phases:
            ax.axvspan(phases["follow_through"][0], phases["follow_through"][1], color="lightgreen", alpha=0.15, label="Follow-Through" if ax == axes[0] else None)

    # Panel 1: Stride Ratio and Foot Placement
    axes[0].plot(frames, stride_ratios, color="teal", lw=2.2, label="Stride / Torso Ratio")
    axes[0].set_ylabel("Stride Ratio")
    axes[0].set_title(f"Delivery {del_id} (39-Set): Temporal Batting Kinematics & Phase Segmentation", fontsize=14, weight="bold")
    axes[0].grid(True, ls="--", alpha=0.5)
    shade_phases(axes[0])
    axes[0].legend(loc="upper left", ncol=7, fontsize=9)

    # Panel 2: Knee Flexion Angles
    axes[1].plot(frames, lead_knees, color="blue", lw=2, label="Lead (Front) Knee Flexion (°)")
    axes[1].plot(frames, trail_knees, color="purple", lw=2, ls="--", label="Trailing (Back) Knee Flexion (°)")
    axes[1].set_ylabel("Knee Angle (°)")
    axes[1].grid(True, ls="--", alpha=0.5)
    shade_phases(axes[1])
    axes[1].legend(loc="upper right", fontsize=9)

    # Panel 3: Torso and Shoulder Orientation
    axes[2].plot(frames, shoulder_angles, color="darkorange", lw=2, label="Shoulder Line Angle (°)")
    axes[2].plot(frames, torso_incs, color="brown", lw=2, ls=":", label="Torso Forward Lean (°)")
    axes[2].set_ylabel("Orientation (°)")
    axes[2].grid(True, ls="--", alpha=0.5)
    shade_phases(axes[2])
    axes[2].legend(loc="upper right", fontsize=9)

    # Panel 4: Wrist Kinetic Speed & Arm Extension
    ax4_ext = axes[3].twinx()
    axes[3].plot(frames, wrist_speeds, color="crimson", lw=2, label="Wrist Speed (px/s)")
    ax4_ext.plot(frames, arm_extensions, color="green", lw=1.8, ls="-.", label="Arm Extension Ratio")
    axes[3].set_ylabel("Wrist Speed (px/s)", color="crimson")
    ax4_ext.set_ylabel("Arm Extension", color="green")
    axes[3].set_xlabel("Clip Frame (30 fps)")
    axes[3].grid(True, ls="--", alpha=0.5)
    shade_phases(axes[3])
    axes[3].legend(loc="upper left", fontsize=9)
    ax4_ext.legend(loc="upper right", fontsize=9)

    plt.savefig(str(out_path), dpi=150, bbox_inches="tight")
    plt.close()


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("STARTING TRAJECTORY-POSE FUSION CRICKET SHOT STUDY (39 DELIVERIES)")
    print("=" * 80)

    # Load Signal A Trajectory Parameters
    traj_summary = {}
    if SUMMARY_TRAJ_CSV.exists():
        with open(SUMMARY_TRAJ_CSV) as f:
            for r in csv.DictReader(f):
                # Map by delivery_id (e.g. "01")
                did = r["delivery_id"].zfill(2)
                if did not in traj_summary:
                    traj_summary[did] = r

    tracker = PoseTracker(MODEL_PATH)
    delivery_dirs = sorted([d for d in glob.glob(str(DATASET_DIR / "*")) if os.path.isdir(d) and not os.path.basename(d).startswith(".")])

    consolidated_results = []
    total_start_time = time.time()
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    for idx, del_path_str in enumerate(delivery_dirs, 1):
        del_path = Path(del_path_str)
        del_id = f"{idx:02d}"

        # Determine hit frame and crease anchor
        hit_frame = 50
        crease_anchor = None
        fbf_csv = del_path / "3d_frame_by_frame_cam2.csv"
        if not fbf_csv.exists():
            fbf_csv = del_path / "3d_frame_by_frame_cam1.csv"
        if fbf_csv.exists():
            try:
                with open(fbf_csv) as f_csv:
                    for r_c in csv.DictReader(f_csv):
                        if "hit" in (r_c.get("event") or ""):
                            hit_frame = int(r_c["clip_frame"])
                            if r_c.get("u_px") and r_c.get("v_px"):
                                crease_anchor = (float(r_c["u_px"]), float(r_c["v_px"]))
                            break
            except Exception:
                pass

        print(f"\n[{del_id}/{len(delivery_dirs)}] Processing {del_path.name} (Hit Frame: {hit_frame})...")

        video_path = del_path / "clip_cam2.mp4"
        if not video_path.exists():
            video_path = del_path / "clip_cam1.mp4"

        json_out = DATA_DIR / f"batter_pose_track_del39_{del_id}.json"
        raw_trajectory = []

        # Check existing pose track
        if json_out.exists():
            try:
                with open(json_out) as f:
                    raw_trajectory = json.load(f)
                if len(raw_trajectory) > 50:
                    print(f"  -> Loaded existing pose track ({len(raw_trajectory)} frames) from cache.")
            except Exception:
                raw_trajectory = []

        if len(raw_trajectory) <= 50:
            cap = cv2.VideoCapture(str(video_path))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            prev_box = None
            raw_trajectory = []

            t0 = time.time()
            for fr_idx in range(total_frames):
                ret, frame = cap.read()
                if not ret:
                    break

                dets = tracker.infer_frame(frame)
                batter_det = select_batter(dets, prev_box, frame.shape, crease_anchor)
                if batter_det is not None:
                    box, score, cid, kpts = batter_det
                    prev_box = box
                    raw_trajectory.append({
                        "frame": fr_idx,
                        "time_s": fr_idx / fps,
                        "valid": True,
                        "box": box.tolist(),
                        "conf": float(score),
                        "kpts": kpts.tolist(),
                    })
                else:
                    raw_trajectory.append({
                        "frame": fr_idx,
                        "time_s": fr_idx / fps,
                        "valid": False,
                        "box": None,
                        "conf": 0.0,
                        "kpts": None,
                    })
            cap.release()
            t_elapsed = time.time() - t0
            print(f"  -> Processed {len(raw_trajectory)} frames in {t_elapsed:.1f}s ({len(raw_trajectory) / t_elapsed:.1f} fps)")

            with open(json_out, "w") as f:
                json.dump(raw_trajectory, f, indent=2)

        # Extract Biomechanical Features
        features = extract_kinematic_features(raw_trajectory, handedness="RHB", camera_id="cam2")

        # Temporal Phase Segmentation
        phases = segment_batting_phases(features, hit_frame)

        # Retrieve Trajectory Parameters (Signal A)
        traj_item = traj_summary.get(del_id, {})
        v_azim = float(traj_item.get("launch_azimuth_deg", 0.0))
        v_elev = float(traj_item.get("launch_elevation_deg", 0.0))
        v_spd = float(traj_item.get("launch_speed_kmh", 25.0))

        # Multi-Signal Fusion Classification
        cls_res = classify_shot_fusion(v_azim, v_elev, v_spd, features, phases, handedness="RHB")

        print(f"  -> Shot: {cls_res['shot_type']} (Alt: {cls_res['alternative_shot']}) [Conf: {cls_res['confidence'] * 100:.0f}%]")
        print(f"  -> Footwork: {cls_res['footwork']} | Trajectory: {cls_res['trajectory_category']} | Direction: {cls_res['shot_direction']}")
        print(f"  -> Azimuth: {cls_res['batter_azimuth_deg']:+.1f}° [{cls_res['sector_name']}] | Speed: {cls_res['ball_speed_kmh']} km/h")

        # Render Annotated Video Preserving Native Aspect Ratio
        cap_probe = cv2.VideoCapture(str(video_path))
        src_w = int(cap_probe.get(cv2.CAP_PROP_FRAME_WIDTH))
        src_h = int(cap_probe.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap_probe.get(cv2.CAP_PROP_FPS) or 30.0
        cap_probe.release()

        if src_w >= src_h:
            out_vid_w = 1920
            out_vid_h = int(round(1920 * (src_h / src_w)))
            if out_vid_h % 2 != 0: out_vid_h += 1
        else:
            out_vid_h = 1920
            out_vid_w = int(round(1920 * (src_w / src_h)))
            if out_vid_w % 2 != 0: out_vid_w += 1

        out_vid_path = VIDEOS_DIR / f"annotated_shot_del39_{del_id}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        vid_writer = cv2.VideoWriter(str(out_vid_path), fourcc, fps, (out_vid_w, out_vid_h))

        cap_render = cv2.VideoCapture(str(video_path))
        for fr_idx in range(len(raw_trajectory)):
            ret, frame = cap_render.read()
            if not ret:
                break

            time_s = fr_idx / fps
            curr_phase = "STANCE"
            for p_name, (p_start, p_end) in phases.items():
                if p_start <= fr_idx <= p_end:
                    curr_phase = p_name.replace("_", " ").upper()
                    break

            item = raw_trajectory[fr_idx] if fr_idx < len(raw_trajectory) else None
            box = np.array(item["box"]) if (item and item["valid"]) else None
            kpts = np.array(item["kpts"]) if (item and item["valid"]) else None

            hud_frame = draw_hud(frame, fr_idx, time_s, curr_phase, cls_res, box, kpts)
            resized_hud = cv2.resize(hud_frame, (out_vid_w, out_vid_h))
            vid_writer.write(resized_hud)

        cap_render.release()
        vid_writer.release()

        # Re-encode to H.264
        h264_tmp_path = VIDEOS_DIR / f"annotated_shot_del39_{del_id}_h264.mp4"
        cmd = [
            ffmpeg_exe, "-y",
            "-i", str(out_vid_path),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(h264_tmp_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and h264_tmp_path.exists():
            shutil.move(str(h264_tmp_path), str(out_vid_path))
            print(f"  -> Saved web-compatible video ({out_vid_w}x{out_vid_h}): {out_vid_path.name}")

        # Render Movement Kinematics Graphs
        graph_out_path = PLOTS_DIR / f"kinematics_del39_{del_id}.png"
        plot_delivery_graphs(features, phases, del_id, graph_out_path)
        print(f"  -> Saved movement graph: {graph_out_path.name}")

        # Consolidate Results
        cls_res["delivery_id"] = del_id
        cls_res["folder"] = del_path.name
        cls_res["hit_frame"] = hit_frame
        cls_res["phases_str"] = ", ".join(f"{k}:{v[0]}-{v[1]}" for k, v in phases.items())
        consolidated_results.append(cls_res)

    # Save CSV & JSON
    out_csv = EXP_DIR / "consolidated_shot_classification_results_39.csv"
    csv_fields = [
        "delivery_id", "folder", "hit_frame", "shot_type", "alternative_shot",
        "footwork", "trajectory_category", "shot_direction", "batter_azimuth_deg",
        "ball_speed_kmh", "ball_elevation_deg", "sector_name", "confidence",
        "lead_disp_pitch_px", "stride_ratio", "torso_inclination_deg",
        "shoulder_rot_deg", "lead_elbow_deg", "supporting_evidence", "phases"
    ]
    with open(out_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(csv_fields)
        for r in consolidated_results:
            bm = r["biomechanics"]
            writer.writerow([
                r["delivery_id"], r["folder"], r["hit_frame"], r["shot_type"],
                r["alternative_shot"], r["footwork"], r["trajectory_category"],
                r["shot_direction"], r["batter_azimuth_deg"], r["ball_speed_kmh"],
                r["ball_elevation_deg"], r["sector_name"], r["confidence"],
                bm["lead_disp_pitch_px"], bm["stride_ratio"], bm["torso_inclination_deg"],
                bm["shoulder_rot_deg"], bm["lead_elbow_deg"], r["supporting_evidence"],
                r["phases_str"]
            ])

    out_json = EXP_DIR / "consolidated_shot_classification_results_39.json"
    with open(out_json, "w") as f:
        json.dump(consolidated_results, f, indent=2)

    # Copy generated assets to frontend public and dist folders
    pub_assets = ROOT / "cricket_trajectory_engine" / "frontend" / "public" / "assets" / "pose_study"
    dist_assets = ROOT / "cricket_trajectory_engine" / "frontend" / "dist" / "assets" / "pose_study"
    pub_assets.mkdir(parents=True, exist_ok=True)
    dist_assets.mkdir(parents=True, exist_ok=True)

    for vid in VIDEOS_DIR.glob("annotated_shot_del39_*.mp4"):
        shutil.copy2(vid, pub_assets / vid.name)
        shutil.copy2(vid, dist_assets / vid.name)

    for plt_f in PLOTS_DIR.glob("kinematics_del39_*.png"):
        shutil.copy2(plt_f, pub_assets / plt_f.name)
        shutil.copy2(plt_f, dist_assets / plt_f.name)

    print("\n" + "=" * 80)
    print("39 DELIVERIES POSE & SHOT EXPERIMENT COMPLETE!")
    print(f"Total processing time: {time.time() - total_start_time:.1f}s")
    print(f"Results saved in: {EXP_DIR}")
    print("=" * 80)


if __name__ == "__main__":
    main()
