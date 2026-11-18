"""
Cricket Trajectory-Pose Fusion Shot Classification Engine.

Combines Ball Trajectory Direction (Signal A: Azimuth, Elevation, Speed) with
Batter Biomechanics (Signal B: Stride, Stance, Angles, Rotation) to produce
cricket-aware, explainable batting stroke classifications.
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple


def compute_batter_relative_azimuth(ball_azimuth_deg: float, handedness: str = "RHB") -> float:
    """
    Transforms world/ground ball launch azimuth into batter-relative azimuth.
    
    Convention:
      0°: Straight down the ground past the bowler.
      > 0°: Always Off-Side (Cover, Point, Third Man).
      < 0°: Always Leg-Side (Mid-on, Mid-wicket, Square Leg, Fine Leg).
    """
    if handedness.upper() == "LHB":
        return -ball_azimuth_deg
    return ball_azimuth_deg


def determine_shot_direction_sector(phi: float) -> Dict[str, Any]:
    """
    Map batter-relative azimuth to tactical cricket ground sectors.
    """
    abs_phi = abs(phi)
    
    # Cricket tactical side and direction label
    if abs_phi <= 12.0:
        side = "Straight"
        direction_label = "Straight"
    elif phi > 0:
        side = "Off side"
        if phi <= 75.0:
            direction_label = "Off side"
        elif phi <= 105.0:
            direction_label = "Square (Off side)"
        else:
            direction_label = "Behind square (Off side)"
    else:
        side = "Leg side"
        if abs_phi <= 75.0:
            direction_label = "Leg side"
        elif abs_phi <= 105.0:
            direction_label = "Square leg"
        else:
            direction_label = "Behind square (Leg side)"
    
    if -10.0 <= phi <= 10.0:
        sector_name = "Straight down the pitch (Long-off / Long-on)"
    elif 10.0 < phi <= 25.0:
        sector_name = "Through mid-off"
    elif 25.0 < phi <= 55.0:
        sector_name = "Through extra cover / cover"
    elif 55.0 < phi <= 80.0:
        sector_name = "Square cover / point"
    elif 80.0 < phi <= 105.0:
        sector_name = "Square of the wicket (Point / Gully)"
    elif 105.0 < phi <= 145.0:
        sector_name = "Behind point (Backward point / Third man)"
    elif 145.0 < phi <= 180.0 or phi < -165.0:
        sector_name = "Behind slips / Third man"
    elif -28.0 <= phi < -10.0:
        sector_name = "Through mid-on"
    elif -55.0 <= phi < -28.0:
        sector_name = "Through mid-wicket"
    elif -80.0 <= phi < -55.0:
        sector_name = "Forward square leg"
    elif -105.0 <= phi < -80.0:
        sector_name = "Square leg"
    elif -145.0 <= phi < -105.0:
        sector_name = "Behind square leg towards fine leg"
    else:
        sector_name = "Fine leg"

    return {
        "side": side,
        "direction_label": direction_label,
        "sector_name": sector_name,
        "is_straight": abs_phi <= 12.0,
        "is_off_side": phi > 5.0,
        "is_leg_side": phi < -5.0,
        "is_behind_square": abs_phi > 90.0,
    }


def classify_shot_fusion(
    ball_azimuth_deg: float,
    ball_elevation_deg: float,
    ball_speed_kmh: float,
    features: List[Dict],
    phases: Dict[str, Tuple[int, int]],
    handedness: str = "RHB",
) -> Dict[str, Any]:
    """
    Multi-Signal Fusion Classification combining Ball Trajectory (Signal A)
    and Batter Pose Kinematics (Signal B).
    """
    phi_batter = compute_batter_relative_azimuth(ball_azimuth_deg, handedness)
    direction_info = determine_shot_direction_sector(phi_batter)

    # Extract impact interval features
    imp_start, imp_end = phases["impact_interval"]
    hit_window = [f for f in features if imp_start <= f.get("frame", 0) <= imp_end and f.get("valid")]
    if not hit_window:
        hit_feat = features[min(len(features) - 1, imp_start)]
    else:
        hit_feat = hit_window[len(hit_window) // 2]

    # Stride and footwork features
    lead_disp_pitch = hit_feat.get("lead_disp_pitch", 0.0)
    stride_ratio = hit_feat.get("stride_ratio", 0.5)
    lead_knee_flex = hit_feat.get("lead_knee_flex", 160.0)
    trail_knee_flex = hit_feat.get("trail_knee_flex", 160.0)
    torso_inc = hit_feat.get("torso_inclination", 20.0)
    shoulder_rot = hit_feat.get("shoulder_rot_from_stance", 15.0)
    lead_elbow = hit_feat.get("lead_elbow_flex", 130.0)
    arm_extension = hit_feat.get("arm_extension", 0.85)
    hip_drop = hit_feat.get("hip_drop_ratio", 0.0)

    # Follow-through features
    ft_start, ft_end = phases["follow_through"]
    ft_window = [f for f in features if ft_start <= f.get("frame", 0) <= min(ft_start + 15, len(features) - 1) and f.get("valid")]
    max_ft_wrist_speed = max([f.get("wrist_speed", 0.0) for f in ft_window], default=0.0)
    avg_ft_arm_ext = np.mean([f.get("arm_extension", 0.85) for f in ft_window]) if ft_window else arm_extension

    # -------------------------------------------------------------------------
    # 1. Independent Footwork Classification
    # -------------------------------------------------------------------------
    if lead_disp_pitch > 22.0 or stride_ratio > 0.45:
        footwork = "Front-foot"
        footwork_conf = min(0.95, 0.70 + max(0.0, lead_disp_pitch) * 0.003 + stride_ratio * 0.15)
        footwork_evidence = f"Forward pitch stride of {lead_disp_pitch:+.1f} px with stride-to-torso ratio of {stride_ratio:.2f}."
    elif lead_disp_pitch < -20.0:
        footwork = "Back-foot"
        footwork_conf = 0.88
        footwork_evidence = f"Weight transferred back towards stumps (pitch displacement {lead_disp_pitch:+.1f} px)."
    else:
        footwork = "Neutral"
        footwork_conf = 0.75
        footwork_evidence = f"Compact crease stance (displacement {lead_disp_pitch:+.1f} px within neutral threshold)."

    # -------------------------------------------------------------------------
    # 2. Independent Trajectory Elevation Classification
    # -------------------------------------------------------------------------
    if ball_elevation_deg >= +12.0:
        trajectory_category = "Lofted"
        elevation_conf = 0.92
        elev_evidence = f"Steep launch elevation of {ball_elevation_deg:+.1f}° clearing the infield."
    elif ball_elevation_deg <= +3.0:
        trajectory_category = "Grounded"
        elevation_conf = 0.90
        elev_evidence = f"Downward/flat launch elevation of {ball_elevation_deg:+.1f}° keeping ball on turf."
    else:
        trajectory_category = "Firm / Low-Loft"
        elevation_conf = 0.78
        elev_evidence = f"Intermediate launch elevation of {ball_elevation_deg:+.1f}°."

    # -------------------------------------------------------------------------
    # 3. Combined Shot Type Classification (Signal A + Signal B)
    # -------------------------------------------------------------------------
    shot_type = "Unclassified"
    alt_shot = None
    confidence = 0.70
    reasons = []

    # Check for Sweep / Kneeling family
    if trail_knee_flex < 115.0 or hip_drop > 0.35:
        if phi_batter > 45.0:
            shot_type = "Reverse Sweep"
            alt_shot = "Grounded Sweep"
            confidence = 0.82
            reasons.append("Kneeling low posture with off-side bat presentation.")
        else:
            shot_type = "Sweep" if trajectory_category == "Grounded" else "Lofted Sweep"
            alt_shot = "Paddle Sweep" if phi_batter < -90.0 else "Forward Defence"
            confidence = 0.85
            reasons.append(f"Kneeling rear knee ({trail_knee_flex:.1f}°) with horizontal bat sweeping across leg side.")

    # Check for Horizontal Bat Cross-Bat Shots (Pull / Cut / Hook)
    elif footwork == "Back-foot" and phi_batter > 65.0:
        if phi_batter > 95.0:
            shot_type = "Late Cut"
            alt_shot = "Square Cut"
            confidence = 0.86
            reasons.append(f"Back-foot position with open face directing ball behind point ({phi_batter:+.1f}°).")
        else:
            shot_type = "Square Cut"
            alt_shot = "Late Cut"
            confidence = 0.88
            reasons.append(f"Back-foot cross-bat horizontal stroke square on off-side ({phi_batter:+.1f}°).")

    elif shoulder_rot > 45.0 and phi_batter < -40.0:
        if phi_batter < -95.0:
            shot_type = "Hook"
            alt_shot = "Pull"
            confidence = 0.83
            reasons.append(f"Extensive upper-body rotation ({shoulder_rot:.1f}°) sending ball behind square leg.")
        else:
            shot_type = "Pull" if trajectory_category == "Grounded" else "Lofted Pull"
            alt_shot = "On-Side Flick"
            confidence = 0.86
            reasons.append(f"Rotational cross-bat swing ({shoulder_rot:.1f}° torso turn) directed to mid-wicket ({phi_batter:+.1f}°).")

    # Vertical Bat Shots (Drives vs. Defences vs. Flicks)
    else:
        # Check Defensive Block criteria:
        # Low speed (< 26 km/h), checked follow-through (wrist speed < 750 px/s, extension < 0.92)
        is_defensive_intent = (
            ball_speed_kmh < 26.5 and
            (max_ft_wrist_speed < 780.0 or avg_ft_arm_ext < 0.90) and
            ball_elevation_deg < +8.0
        )

        if is_defensive_intent:
            if footwork == "Back-foot":
                shot_type = "Back-Foot Defence"
                alt_shot = "Defensive Block"
                confidence = 0.86
                reasons.append("Upright back-foot posture with checked wrists and soft hands.")
            else:
                shot_type = "Forward Defence"
                alt_shot = "Forward Defensive Push"
                confidence = 0.88
                reasons.append(f"Textbook forward stride ({lead_disp_pitch:+.1f} px) with checked wrists and soft exit speed ({ball_speed_kmh:.1f} km/h).")

        # Attacking / Controlled Drives and Flicks:
        elif trajectory_category == "Lofted" and ball_speed_kmh > 35.0:
            if phi_batter > 20.0:
                shot_type = "Lofted Cover Drive"
                alt_shot = "Lofted Drive"
                confidence = 0.90
            elif -15.0 <= phi_batter <= 20.0:
                shot_type = "Lofted Straight Drive"
                alt_shot = "Lofted On-Drive"
                confidence = 0.92
            else:
                shot_type = "Lofted On-Drive"
                alt_shot = "Lofted Flick"
                confidence = 0.90
            reasons.append(f"High launch elevation ({ball_elevation_deg:+.1f}°) and aerial follow-through extension ({avg_ft_arm_ext:.2f}).")

        # Grounded / Controlled Drives:
        else:
            # Differentiate based on Azimuth Sector:
            if -12.0 <= phi_batter <= 12.0:
                shot_type = "Straight Drive"
                alt_shot = "Off Drive" if phi_batter > 0 else "On Drive"
                confidence = 0.88
                reasons.append(f"Bat swing aligned straight in the 'V' downfield ({phi_batter:+.1f}° azimuth) past bowler.")

            elif 12.0 < phi_batter <= 28.0:
                shot_type = "Off Drive"
                alt_shot = "Cover Drive"
                confidence = 0.86
                reasons.append(f"Off-side presentation directed through mid-off ({phi_batter:+.1f}°).")

            elif 28.0 < phi_batter <= 60.0:
                shot_type = "Cover Drive"
                alt_shot = "Square Drive" if phi_batter > 50.0 else "Off Drive"
                confidence = 0.90
                reasons.append(f"High lead elbow ({lead_elbow:.1f}°) with diagonal forward stride through cover ({phi_batter:+.1f}°).")

            elif 60.0 < phi_batter <= 85.0:
                shot_type = "Square Drive"
                alt_shot = "Cover Drive"
                confidence = 0.84
                reasons.append(f"Full forward stride carving the ball through point ({phi_batter:+.1f}°).")

            elif -28.0 <= phi_batter < -12.0:
                shot_type = "On Drive"
                alt_shot = "Flick"
                confidence = 0.87
                reasons.append(f"Straight vertical presentation playing the ball through mid-on ({phi_batter:+.1f}°).")

            elif -65.0 <= phi_batter < -28.0:
                # Flick vs. On-Drive: check wrist rotation & shoulder turn
                if shoulder_rot > 20.0:
                    shot_type = "Flick"
                    alt_shot = "On Drive"
                    confidence = 0.88
                    reasons.append(f"Rolling wrist action with upper body rotation ({shoulder_rot:.1f}°) through mid-wicket ({phi_batter:+.1f}°).")
                else:
                    shot_type = "On Drive"
                    alt_shot = "Flick"
                    confidence = 0.84
                    reasons.append(f"Vertical bat presented through mid-on/mid-wicket ({phi_batter:+.1f}°).")

            elif phi_batter < -65.0:
                shot_type = "Leg Glance"
                alt_shot = "Flick"
                confidence = 0.85
                reasons.append(f"Subtle deflection off pads directing ball fine of square leg ({phi_batter:+.1f}°).")

    # Combine technical explanation
    s_evidence = (
        f"[Signal A: Trajectory] Ball exit azimuth {phi_batter:+.1f}° ({direction_info['sector_name']}), "
        f"launch speed {ball_speed_kmh:.1f} km/h, elevation {ball_elevation_deg:+.1f}° ({trajectory_category}). "
        f"[Signal B: Pose] {footwork} posture (pitch stride {lead_disp_pitch:+.1f} px, ratio {stride_ratio:.2f}), "
        f"torso lean {torso_inc:.1f}°, shoulder rotation {shoulder_rot:.1f}°, lead elbow {lead_elbow:.1f}°. "
        + " ".join(reasons)
    )

    return {
        "shot_type": shot_type,
        "alternative_shot": alt_shot,
        "footwork": footwork,
        "trajectory_category": trajectory_category,
        "shot_direction": direction_info["direction_label"],
        "batter_azimuth_deg": round(phi_batter, 1),
        "ball_speed_kmh": round(ball_speed_kmh, 1),
        "ball_elevation_deg": round(ball_elevation_deg, 1),
        "confidence": round(confidence, 2),
        "footwork_confidence": round(footwork_conf, 2),
        "elevation_confidence": round(elevation_conf, 2),
        "sector_name": direction_info["sector_name"],
        "supporting_evidence": s_evidence,
        "biomechanics": {
            "lead_disp_pitch_px": round(lead_disp_pitch, 1),
            "stride_ratio": round(stride_ratio, 2),
            "lead_knee_deg": round(lead_knee_flex, 1),
            "trail_knee_deg": round(trail_knee_flex, 1),
            "torso_inclination_deg": round(torso_inc, 1),
            "shoulder_rot_deg": round(shoulder_rot, 1),
            "lead_elbow_deg": round(lead_elbow, 1),
            "follow_through_extension": round(avg_ft_arm_ext, 2),
            "max_wrist_speed_px_s": round(max_ft_wrist_speed, 1),
        }
    }
