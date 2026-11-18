"""
Cricket Batter Pose Kinematic Feature Extraction Module.

Extracts biomechanical, temporal, and spatial features from 17 COCO human pose keypoints
tracked across a complete batting delivery sequence.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional


def compute_angle(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> float:
    """Compute 2D angle at vertex p2 formed by lines p1-p2 and p3-p2 in degrees."""
    v1 = p1 - p2
    v2 = p3 - p2
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 < 1e-5 or norm2 < 1e-5:
        return 180.0
    cosine = np.clip(np.dot(v1, v2) / (norm1 * norm2), -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))


def compute_line_angle(p1: np.ndarray, p2: np.ndarray) -> float:
    """Compute angle of directed line p1 -> p2 relative to horizontal axis in degrees."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return float(np.degrees(np.arctan2(dy, dx)))


def extract_kinematic_features(
    trajectory: List[Dict],
    handedness: str = "RHB",
    camera_id: str = "cam2",
) -> List[Dict]:
    """
    Extract cricket-specific biomechanical and movement features across frames.
    
    Parameters:
        trajectory: List of per-frame dictionaries with 'frame', 'time_s', 'valid', 'kpts', 'box'.
        handedness: 'RHB' (Right-Handed Batter) or 'LHB' (Left-Handed Batter).
        camera_id: 'cam2' (pitch-side bowler perspective) or 'cam1' (slips/keeper perspective).
    """
    features = []
    
    # Establish baseline stance from initial 20 frames
    stance_frames = [np.array(f["kpts"]) for f in trajectory[:20] if f.get("valid") and f.get("kpts") is not None]
    
    # Keypoint indices:
    # 5: left_shoulder, 6: right_shoulder
    # 7: left_elbow, 8: right_elbow
    # 9: left_wrist, 10: right_wrist
    # 11: left_hip, 12: right_hip
    # 13: left_knee, 14: right_knee
    # 15: left_ankle, 16: right_ankle
    if handedness == "RHB":
        lead_sh_idx, trail_sh_idx = 5, 6
        lead_el_idx, trail_el_idx = 7, 8
        lead_wr_idx, trail_wr_idx = 9, 10
        lead_hip_idx, trail_hip_idx = 11, 12
        lead_kn_idx, trail_kn_idx = 13, 14
        lead_ak_idx, trail_ak_idx = 15, 16
    else:
        lead_sh_idx, trail_sh_idx = 6, 5
        lead_el_idx, trail_el_idx = 8, 7
        lead_wr_idx, trail_wr_idx = 10, 9
        lead_hip_idx, trail_hip_idx = 12, 11
        lead_kn_idx, trail_kn_idx = 14, 13
        lead_ak_idx, trail_ak_idx = 16, 15

    if stance_frames:
        base_lead_ankle = np.mean([k[lead_ak_idx, :2] for k in stance_frames], axis=0)
        base_trail_ankle = np.mean([k[trail_ak_idx, :2] for k in stance_frames], axis=0)
        base_lead_hip = np.mean([k[lead_hip_idx, :2] for k in stance_frames], axis=0)
        base_shoulder_ang = np.mean([
            compute_line_angle(k[lead_sh_idx, :2], k[trail_sh_idx, :2]) for k in stance_frames
        ])
        base_torso_len = np.mean([
            np.linalg.norm(
                (k[lead_sh_idx, :2] + k[trail_sh_idx, :2]) / 2.0 -
                (k[lead_hip_idx, :2] + k[trail_hip_idx, :2]) / 2.0
            ) for k in stance_frames
        ])
        base_torso_len = max(float(base_torso_len), 10.0)
    else:
        base_lead_ankle = np.array([0.0, 0.0])
        base_trail_ankle = np.array([0.0, 0.0])
        base_lead_hip = np.array([0.0, 0.0])
        base_shoulder_ang = 0.0
        base_torso_len = 300.0

    for item in trajectory:
        if not item.get("valid") or item.get("kpts") is None:
            features.append({"valid": False, "frame": item["frame"], "time_s": item.get("time_s", 0.0)})
            continue

        kpts = np.array(item["kpts"])
        lead_sh, trail_sh = kpts[lead_sh_idx, :2], kpts[trail_sh_idx, :2]
        lead_el, trail_el = kpts[lead_el_idx, :2], kpts[trail_el_idx, :2]
        lead_wr, trail_wr = kpts[lead_wr_idx, :2], kpts[trail_wr_idx, :2]
        lead_hip, trail_hip = kpts[lead_hip_idx, :2], kpts[trail_hip_idx, :2]
        lead_kn, trail_kn = kpts[lead_kn_idx, :2], kpts[trail_kn_idx, :2]
        lead_ak, trail_ak = kpts[lead_ak_idx, :2], kpts[trail_ak_idx, :2]

        sh_mid = (lead_sh + trail_sh) / 2.0
        hip_mid = (lead_hip + trail_hip) / 2.0
        wrist_mid = (lead_wr + trail_wr) / 2.0
        torso_len = max(float(np.linalg.norm(sh_mid - hip_mid)), 10.0)

        # 1. Foot placement and stride
        # In cam2, bowler is towards smaller x (left). Forward stride down the pitch decreases x.
        # Thus, forward displacement = base_x - current_x
        if camera_id == "cam2":
            lead_disp_pitch = float(base_lead_ankle[0] - lead_ak[0])
            trail_disp_pitch = float(base_trail_ankle[0] - trail_ak[0])
        else:
            lead_disp_pitch = float(lead_ak[0] - base_lead_ankle[0])
            trail_disp_pitch = float(trail_ak[0] - base_trail_ankle[0])

        stride_dist = float(np.linalg.norm(lead_ak - trail_ak))
        stride_ratio = float(stride_dist / torso_len)

        # 2. Knee flexion angles (degrees, 180° = fully straight leg)
        lead_knee_flex = compute_angle(lead_hip, lead_kn, lead_ak)
        trail_knee_flex = compute_angle(trail_hip, trail_kn, trail_ak)

        # 3. Torso orientation & Shoulder rotation
        shoulder_ang = compute_line_angle(lead_sh, trail_sh)
        hip_ang = compute_line_angle(lead_hip, trail_hip)
        
        rot_from_stance = float(abs(shoulder_ang - base_shoulder_ang))
        if rot_from_stance > 180.0:
            rot_from_stance = 360.0 - rot_from_stance

        # Torso inclination relative to vertical
        spine_vec = sh_mid - hip_mid
        torso_inclination = float(np.degrees(np.arctan2(abs(spine_vec[0]), -spine_vec[1])))

        # 4. Center-of-gravity drop (relative hip height vs stance)
        hip_drop_ratio = float((lead_hip[1] - base_lead_hip[1]) / torso_len)

        # 5. Arm & Elbow configuration
        lead_elbow_flex = compute_angle(lead_sh, lead_el, lead_wr)
        trail_elbow_flex = compute_angle(trail_sh, trail_el, trail_wr)
        arm_extension = float(np.linalg.norm(wrist_mid - sh_mid) / torso_len)

        features.append({
            "valid": True,
            "frame": item["frame"],
            "time_s": item["time_s"],
            "lead_disp_pitch": lead_disp_pitch,
            "trail_disp_pitch": trail_disp_pitch,
            "stride_ratio": stride_ratio,
            "stride_dist_px": stride_dist,
            "lead_knee_flex": lead_knee_flex,
            "trail_knee_flex": trail_knee_flex,
            "shoulder_angle": shoulder_ang,
            "shoulder_rot_from_stance": rot_from_stance,
            "hip_angle": hip_ang,
            "torso_inclination": torso_inclination,
            "hip_drop_ratio": hip_drop_ratio,
            "lead_elbow_flex": lead_elbow_flex,
            "trail_elbow_flex": trail_elbow_flex,
            "arm_extension": arm_extension,
            "wrist_x": float(wrist_mid[0]),
            "wrist_y": float(wrist_mid[1]),
        })

    # Compute smoothed kinetic wrist speed
    for i in range(len(features)):
        if not features[i]["valid"]:
            features[i]["wrist_speed"] = 0.0
            continue
        if 0 < i < len(features) - 1 and features[i - 1]["valid"] and features[i + 1]["valid"]:
            dt = max(features[i + 1]["time_s"] - features[i - 1]["time_s"], 1e-4)
            vx = (features[i + 1]["wrist_x"] - features[i - 1]["wrist_x"]) / dt
            vy = (features[i + 1]["wrist_y"] - features[i - 1]["wrist_y"]) / dt
            features[i]["wrist_speed"] = float(np.hypot(vx, vy))
        else:
            features[i]["wrist_speed"] = 0.0

    return features


def segment_batting_phases(features: List[Dict], hit_frame: int) -> Dict[str, Tuple[int, int]]:
    """
    Segment the complete temporal delivery sequence into 6 distinct phases.
    """
    total_frames = len(features)
    
    # Backswing detection: wrists begin accelerating upward
    backswing_start = 20
    for f in features[15:min(40, hit_frame - 5)]:
        if f.get("valid") and f.get("wrist_speed", 0.0) > 350.0:
            backswing_start = f["frame"]
            break

    # Stride start: lead foot advances along pitch
    stride_start = max(backswing_start + 4, 30)
    for f in features[backswing_start:min(hit_frame - 5, total_frames)]:
        if f.get("valid") and abs(f.get("lead_disp_pitch", 0.0)) > 20.0:
            stride_start = f["frame"]
            break

    # Execution (downswing into ball line)
    execution_start = max(stride_start + 5, hit_frame - 8)

    # Impact interval
    impact_start = max(0, hit_frame - 1)
    impact_end = min(total_frames - 1, hit_frame + 1)

    # Follow-through
    follow_through_start = min(total_frames - 1, hit_frame + 2)
    follow_through_end = total_frames - 1

    return {
        "stance": (0, max(0, backswing_start - 1)),
        "backswing": (backswing_start, max(backswing_start, stride_start - 1)),
        "stride": (stride_start, max(stride_start, execution_start - 1)),
        "execution": (execution_start, max(execution_start, impact_start - 1)),
        "impact_interval": (impact_start, impact_end),
        "follow_through": (follow_through_start, follow_through_end),
    }
