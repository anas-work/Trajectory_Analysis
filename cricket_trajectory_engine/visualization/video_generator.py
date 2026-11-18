"""
Animated broadcast-grade video generator for 3D cricket ball trajectories.

Generates multiple high-definition presentation videos at different input values:
1. Cover Drive Clearing Rope for FOUR.
2. High-Lofted Shot Clearing Rope on Full for SIX.
3. Controlled Push Pulling Up Short of Rope (2 Runs).
4. Towering Skyer Intercepted for a CATCH in the Deep.
"""

import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mpl_cache")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
import numpy as np
import imageio
from typing import Optional, List, Dict, Any

from cricket_trajectory_engine.physics.ground_collision import MultiBounceResult
from cricket_trajectory_engine.prediction.field_geometry import CricketField
from cricket_trajectory_engine.prediction.outcome_engine import CricketOutcome, FielderPosition
from cricket_trajectory_engine.visualization.cricket_ground_renderer import (
    draw_authentic_cricket_ground_3d,
    get_international_cricket_fielders,
    COLOR_BG,
    COLOR_ARC_CORE,
    COLOR_ARC_GLOW,
    COLOR_ROLL,
    COLOR_SHADOW,
)


def generate_single_video_animation(
    multi_bounce_res: MultiBounceResult,
    outcome: Optional[CricketOutcome] = None,
    field: Optional[CricketField] = None,
    fielders: Optional[List[FielderPosition]] = None,
    output_mp4_path: str = "cricket_trajectory.mp4",
    output_gif_path: Optional[str] = "cricket_trajectory.gif",
    scenario_title: str = "Hawkeye 3D Cricket Trajectory",
    pipeline_metadata: Optional[Dict[str, Any]] = None,
    fps: int = 25,
    max_duration_s: float = 6.0,
    dpi: int = 120,
) -> Dict[str, str]:
    """
    Renders and encodes a frame-by-frame 3D broadcast animation of the cricket ball flight.
    Displays:
    - 3D stadium, turf pitch, wickets, crease lines, fielders, and boundary rope.
    - 3D ball, glowing Hawkeye trail, ground shadow, altitude ribs, and bounce markers.
    - Input data used from tracking, extra physics parameters added, predicted results, and live telemetry.
    """
    field_obj = field or CricketField()
    fielders_list = fielders if fielders is not None else get_international_cricket_fielders()

    all_times = multi_bounce_res.time_s
    all_positions = multi_bounce_res.positions_m
    all_velocities = multi_bounce_res.velocities_m_s

    total_time = all_times[-1]
    anim_duration = min(total_time, max_duration_s)
    n_frames = int(anim_duration * fps)
    frame_times = np.linspace(0.0, anim_duration, n_frames)

    first_b = multi_bounce_res.first_bounce
    t_first_bounce = first_b.time_s if first_b else float("inf")
    pos_first_bounce = first_b.position_m if first_b else None

    # Apex:
    apex_idx = int(np.argmax(all_positions[:, 2]))
    t_apex = all_times[apex_idx]
    pos_apex = all_positions[apex_idx]

    # Pre-interpolate state for each animation frame:
    interp_pos = np.zeros((n_frames, 3))
    interp_vel = np.zeros((n_frames, 3))
    for ax_i in range(3):
        interp_pos[:, ax_i] = np.interp(frame_times, all_times, all_positions[:, ax_i])
        interp_vel[:, ax_i] = np.interp(frame_times, all_times, all_velocities[:, ax_i])

    # Initial launch parameters:
    v0 = all_velocities[0]
    speed0 = np.linalg.norm(v0)
    elev0 = np.degrees(np.arctan2(v0[2], np.hypot(v0[0], v0[1])))
    azim0 = np.degrees(np.arctan2(v0[1], v0[0]))

    # Set up figure (widescreen 16:9):
    fig = plt.figure(figsize=(15.2, 8.2), facecolor=COLOR_BG, dpi=dpi)
    ax = fig.add_axes([0.16, 0.08, 0.68, 0.84], projection="3d", facecolor=COLOR_BG)

    # Static authentic ground features:
    draw_authentic_cricket_ground_3d(ax, field_obj, fielders_list)

    # View bounds:
    r_field = field_obj.radius_m
    ax.set_xlim(-16.0, r_field + 6.0)
    ax.set_ylim(-r_field * 0.72, r_field * 0.72)
    ax.set_zlim(0.0, max(24.0, pos_apex[2] * 1.35))
    ax.set_xlabel("X (Forward / m)", color="#95a5a6", labelpad=8)
    ax.set_ylabel("Y (Lateral / m)", color="#95a5a6", labelpad=8)
    ax.set_zlabel("Z (Height / m)", color="#95a5a6", labelpad=8)
    ax.tick_params(colors="#7f8c8d", labelsize=8)
    ax.view_init(elev=20, azim=-88)

    # Setup imageio video writers:
    os.makedirs(os.path.dirname(os.path.abspath(output_mp4_path)) or ".", exist_ok=True)
    mp4_writer = imageio.get_writer(output_mp4_path, fps=fps, codec="libx264", quality=8)
    gif_frames = []

    # Dynamic line elements:
    air_glow, = ax.plot([], [], [], color=COLOR_ARC_GLOW, linewidth=4.0, alpha=0.85)
    air_core, = ax.plot([], [], [], color=COLOR_ARC_CORE, linewidth=1.6, alpha=1.0)
    roll_line, = ax.plot([], [], [], color=COLOR_ROLL, linewidth=2.8, linestyle="-")
    shadow_line, = ax.plot([], [], [], color=COLOR_SHADOW, linewidth=1.8, linestyle="--")

    # Ball marker:
    ball_scatter = ax.scatter([], [], [], color="#ffffff", s=110, edgecolors="#e74c3c", linewidths=2.5)

    # Altitude ribs (vertical drop lines):
    rib_lines = [ax.plot([], [], [], color="#e74c3c", alpha=0.35, linewidth=1.0)[0] for _ in range(18)]

    # HUD Overlays:
    hud_bg_left = dict(boxstyle="round,pad=0.45", facecolor="#10171e", edgecolor="#00b4d8", alpha=0.93, linewidth=1.2)
    hud_bg_right = dict(boxstyle="round,pad=0.45", facecolor="#10171e", edgecolor="#f5a623", alpha=0.93, linewidth=1.2)

    # Left text box:
    hud_left_text = fig.text(
        0.015, 0.95, "", color="#ffffff", fontsize=7.8, fontfamily="monospace",
        verticalalignment="top", bbox=hud_bg_left
    )

    # Right text box:
    hud_right_text = fig.text(
        0.825, 0.95, "", color="#ffffff", fontsize=7.8, fontfamily="monospace",
        verticalalignment="top", bbox=hud_bg_right
    )

    # Status / Call banner at bottom center:
    call_bg = dict(boxstyle="round,pad=0.45", facecolor="#1a252f", edgecolor="#f1c40f", linewidth=1.8)
    call_text = fig.text(0.50, 0.035, "", color="#f1c40f", fontsize=10.5, fontweight="bold",
                         ha="center", bbox=call_bg, visible=False)

    title_text = fig.text(0.50, 0.965, scenario_title, color="#ffffff", fontsize=12.5, fontweight="bold", ha="center")

    print(f"Encoding {n_frames} animation frames ({fps} fps) for: {os.path.basename(output_mp4_path)}")

    # Extract metadata components if provided:
    meta_in = pipeline_metadata.get("input_data", {}) if pipeline_metadata else {}
    meta_pipe = pipeline_metadata.get("pipeline_params", {}) if pipeline_metadata else {}
    meta_res = pipeline_metadata.get("results_data", {}) if pipeline_metadata else {}

    for f_idx in range(n_frames):
        t_curr = frame_times[f_idx]
        pos_curr = interp_pos[f_idx]
        vel_curr = interp_vel[f_idx]
        speed_curr = float(np.linalg.norm(vel_curr))
        dist_curr = float(np.hypot(pos_curr[0], pos_curr[1]))

        hist_p = interp_pos[:f_idx + 1]
        hist_t = frame_times[:f_idx + 1]

        # Update ball position:
        ball_scatter._offsets3d = ([pos_curr[0]], [pos_curr[1]], [pos_curr[2]])

        # Update trajectory trail:
        if t_curr <= t_first_bounce:
            air_glow.set_data(hist_p[:, 0], hist_p[:, 1])
            air_glow.set_3d_properties(hist_p[:, 2])
            air_core.set_data(hist_p[:, 0], hist_p[:, 1])
            air_core.set_3d_properties(hist_p[:, 2])
            roll_line.set_data([], [])
            roll_line.set_3d_properties([])
        else:
            idx_b = np.searchsorted(hist_t, t_first_bounce)
            air_p = hist_p[:idx_b]
            roll_p = hist_p[idx_b - 1:]

            air_glow.set_data(air_p[:, 0], air_p[:, 1])
            air_glow.set_3d_properties(air_p[:, 2])
            air_core.set_data(air_p[:, 0], air_p[:, 1])
            air_core.set_3d_properties(air_p[:, 2])

            roll_line.set_data(roll_p[:, 0], roll_p[:, 1])
            roll_line.set_3d_properties(roll_p[:, 2])

        # Ground shadow:
        shadow_line.set_data(hist_p[:, 0], hist_p[:, 1])
        shadow_line.set_3d_properties(np.zeros(len(hist_p)) + 0.002)

        # Altitude ribs:
        n_ribs = len(rib_lines)
        if len(hist_p) > 1 and t_curr <= t_first_bounce:
            rib_indices = np.linspace(0, len(hist_p) - 1, n_ribs, dtype=int)
            for r_i, p_idx in enumerate(rib_indices):
                rp = hist_p[p_idx]
                if rp[2] > 0.15:
                    rib_lines[r_i].set_data([rp[0], rp[0]], [rp[1], rp[1]])
                    rib_lines[r_i].set_3d_properties([0.0, rp[2]])
                else:
                    rib_lines[r_i].set_data([], [])
                    rib_lines[r_i].set_3d_properties([])
        else:
            for r_i in range(n_ribs):
                rib_lines[r_i].set_data([], [])
                rib_lines[r_i].set_3d_properties([])

        # Left HUD Box: [1. INPUT TRACKED DATA] & [2. ADDED PHYSICS PIPELINE]
        if pipeline_metadata:
            left_lines = [
                "1. INPUT TRACKED DATA",
                "────────────────────────",
                f"ID:      {meta_in.get('delivery_id', 'N/A')}",
                f"Date:    {meta_in.get('created_at', '2026-11-05')}",
                f"Bowl V:  {meta_in.get('bowler_speed_kmh', 'N/A')} km/h",
                f"Bat V:   {meta_in.get('bat_hit_speed_kmh', 'N/A')} km/h",
                f"Tracked: {meta_in.get('n_points', 'N/A')} frames",
                f"Vel v0:  {meta_in.get('v0_str', f'[{v0[0]:.1f},{v0[1]:.1f},{v0[2]:.1f}]')}",
                f"Speed:   {speed0*3.6:5.1f} km/h",
                f"Launch:  {elev0:+.1f}° el, {azim0:+.1f}° az",
                "",
                "2. ADDED PHYSICS PIPELINE",
                "────────────────────────",
                f"Ball:    {meta_pipe.get('mass_dia', '160g / 72.5mm')}",
                f"Air / g: {meta_pipe.get('air_gravity', '1.225 kg/m³ | 9.81 m/s²')}",
                f"Drag:    Cd = {meta_pipe.get('cd', '0.32')}",
                f"Spin:    {meta_pipe.get('spin_model', 'Disabled')}",
                f"Turf:    en={meta_pipe.get('en', '0.55')}, μt={meta_pipe.get('mu_t', '0.38')}",
                f"Roll:    μroll = {meta_pipe.get('mu_roll', '0.20')}",
                f"Rope:    R = {meta_pipe.get('boundary_r', '70.0 m')}",
            ]
            hud_left_text.set_text("\n".join(left_lines))
        else:
            # Fallback concise HUD
            hud_left_text.set_text(
                f"INPUT METRICS\n"
                f"─────────────\n"
                f"Launch: {speed0*3.6:5.1f} km/h\n"
                f"Elev:   {elev0:+.1f}°\n"
                f"Azim:   {azim0:+.1f}°\n"
                f"v0: [{v0[0]:.1f},{v0[1]:.1f},{v0[2]:.1f}]"
            )

        # Right HUD Box: [3. PREDICTED RESULTS] & [4. LIVE TELEMETRY]
        if pipeline_metadata:
            is_four = "FOUR" in str(meta_res.get('outcome_call', ''))
            total_d_str = f"{meta_res.get('d_total', '70.0')} m (Rope)" if is_four else f"{meta_res.get('d_total', 'N/A')} m"
            right_lines = [
                "3. PREDICTED RESULTS",
                "────────────────────────",
                f"Carry:   {meta_res.get('d_pitch', 'N/A')} m",
                f"Apex:    {meta_res.get('apex', f'{pos_apex[2]:.1f}')} m",
                f"Total d: {total_d_str}",
                f"Rollout: {meta_res.get('d_roll', 'N/A')} m",
            ]
            if is_four and meta_res.get("d_unconstrained"):
                right_lines.append(f"Roll* :  {meta_res.get('d_unconstrained')}m (No rope)")
            right_lines.extend([
                f"Rope:    {meta_res.get('rope_clearance', 'N/A')}",
                f"Outcome: {meta_res.get('outcome_call', 'N/A')}",
                "",
                "4. LIVE TELEMETRY",
                "────────────────────────",
                f"Time:    {t_curr:5.2f} s",
                f"Speed:   {speed_curr*3.6:5.1f} km/h",
                f"Height:  {pos_curr[2]:5.2f} m",
                f"Range:   {dist_curr:5.1f} m",
            ])
            hud_right_text.set_text("\n".join(right_lines))
        else:
            hud_right_text.set_text(
                f"HAWKEYE TELEMETRY\n"
                f"─────────────────\n"
                f"Time:  {t_curr:5.2f} s\n"
                f"Speed: {speed_curr*3.6:5.1f} km/h\n"
                f"Z Alt: {pos_curr[2]:5.2f} m\n"
                f"Range: {dist_curr:5.1f} m"
            )

        # Dynamic Status Announcements at bottom center:
        if t_curr <= 0.18:
            call_text.set_text(f"BAT IMPACT: {speed0*3.6:.0f} km/h @ {elev0:.1f}°")
            call_text.set_visible(True)
        elif t_curr >= t_apex and pos_apex is not None and t_curr < (t_apex + 0.75):
            call_text.set_text(f"▲ APEX REACHED: {pos_apex[2]:.2f}m Altitude")
            call_text.set_visible(True)
        elif t_curr >= t_first_bounce and t_curr < (t_first_bounce + 0.75):
            carry_d = np.hypot(pos_first_bounce[0], pos_first_bounce[1]) if pos_first_bounce is not None else 0
            call_text.set_text(f"▼ 1st PITCH BOUNCE: Carry = {carry_d:.1f}m")
            call_text.set_visible(True)
        elif t_curr >= (t_first_bounce + 0.75) and outcome:
            if outcome.rope_clearance.clears_rope:
                v_res = outcome.rope_clearance.residual_speed_at_rope_m_s or 0.0
                call_label = "MAXIMUM SIX!" if "SIX" in outcome.primary_call else "BOUNDARY FOUR!"
                call_text.set_text(f"★ {call_label} | Cleared Rope at {v_res*3.6:.0f} km/h")
            elif outcome.primary_call == "POTENTIAL_CATCH":
                call_text.set_text("✕ WICKET! CAUGHT IN DEEP BY FIELDER")
            elif outcome.primary_call == "DOUBLE":
                call_text.set_text(f"● IN-PLAY (2 RUNS) | Stopped {abs(outcome.rope_clearance.margin_m):.1f}m inside rope")
            elif outcome.primary_call == "SINGLE":
                call_text.set_text(f"● IN-PLAY (1 RUN) | Stopped {abs(outcome.rope_clearance.margin_m):.1f}m inside rope")
            else:
                call_text.set_text(f"● DOT BALL | Stopped {abs(outcome.rope_clearance.margin_m):.1f}m inside rope")
            call_text.set_visible(True)

        fig.canvas.draw()
        frame_img = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
        mp4_writer.append_data(frame_img)

        if output_gif_path and f_idx % 2 == 0:
            gif_frames.append(frame_img)

    mp4_writer.close()
    plt.close(fig)

    results = {"mp4": output_mp4_path}
    if output_gif_path and gif_frames:
        imageio.mimsave(output_gif_path, gif_frames, fps=fps // 2, loop=0)
        results["gif"] = output_gif_path

    return results


def generate_presentation_video_suite(output_dir: str) -> Dict[str, Dict[str, str]]:
    """
    Generates a suite of 4 distinct presentation videos at different input values:
    1. Cover Drive Clearing Rope for FOUR.
    2. High-Lofted Shot Clearing Rope on Full for SIX.
    3. Controlled Push Pulling Up Short of Rope (2 Runs).
    4. Towering Skyer Intercepted for a CATCH in the Deep.
    """
    from cricket_trajectory_engine.config.physics_config import BallConfig, EnvironmentConfig, AerodynamicsConfig, FieldConfig
    from cricket_trajectory_engine.physics.ground_collision import simulate_multi_bounce
    from cricket_trajectory_engine.prediction.outcome_engine import evaluate_outcome

    ball = BallConfig()
    env = EnvironmentConfig()
    aero = AerodynamicsConfig(constant_cd=0.32)
    field_cfg = FieldConfig(boundary_radius_m=70.0)
    field_obj = CricketField(field_cfg)
    fielders_std = get_international_cricket_fielders("balanced")
    fielders_catch = get_international_cricket_fielders("lofted_catch")

    video_configs = [
        {
            "id": "video_1_four_cover_drive",
            "title": "Video 1: Cover Drive Clearing Rope for FOUR",
            "v0": np.array([28.5, 9.8, 6.2]),   # Speed: 30.7 m/s (110 km/h), Launch: 11.6 deg
            "p0": np.array([0.0, 0.0, 0.85]),
            "fielders": fielders_std,
            "max_duration_s": 5.0,
        },
        {
            "id": "video_2_six_long_on",
            "title": "Video 2: High-Lofted Shot Clearing Rope on Full for SIX",
            "v0": np.array([31.0, -3.0, 20.0]), # Speed: 37.0 m/s (133 km/h), Launch: 32.6 deg
            "p0": np.array([0.0, 0.0, 1.10]),
            "fielders": fielders_std,
            "max_duration_s": 5.5,
        },
        {
            "id": "video_3_pulled_up_short",
            "title": "Video 3: Controlled Push Pulling Up Short (2 Runs)",
            "v0": np.array([21.0, -6.5, 4.8]),  # Speed: 22.5 m/s (81 km/h), Launch: 12.3 deg
            "p0": np.array([0.0, 0.0, 0.90]),
            "fielders": fielders_std,
            "max_duration_s": 4.5,
        },
        {
            "id": "video_4_caught_deep_midwicket",
            "title": "Video 4: Towering Skyer Caught at Deep Mid-Wicket",
            "v0": np.array([24.0, -14.0, 22.0]),# Speed: 35.4 m/s (127 km/h), Steep Launch: 38.4 deg
            "p0": np.array([0.0, 0.0, 1.00]),
            "fielders": fielders_catch,
            "max_duration_s": 5.5,
        },
    ]

    all_results = {}

    for cfg in video_configs:
        vid_id = cfg["id"]
        res = simulate_multi_bounce(cfg["p0"], cfg["v0"], ball, env, aero)
        outcome = evaluate_outcome(res, field_config=field_cfg, fielders=cfg["fielders"])

        mp4_path = os.path.join(output_dir, f"{vid_id}.mp4")
        gif_path = os.path.join(output_dir, f"{vid_id}.gif")

        vid_files = generate_single_video_animation(
            multi_bounce_res=res,
            outcome=outcome,
            field=field_obj,
            fielders=cfg["fielders"],
            output_mp4_path=mp4_path,
            output_gif_path=gif_path,
            scenario_title=cfg["title"],
            fps=25,
            max_duration_s=cfg["max_duration_s"],
        )
        all_results[vid_id] = vid_files

    return all_results


# Compatibility alias for main.py:
def generate_trajectory_video(
    multi_bounce_res: MultiBounceResult,
    outcome: Optional[CricketOutcome] = None,
    field: Optional[CricketField] = None,
    fielders: Optional[List[FielderPosition]] = None,
    output_mp4_path: str = "cricket_trajectory_demo.mp4",
    output_gif_path: Optional[str] = "cricket_trajectory_demo.gif",
    fps: int = 25,
    max_duration_s: float = 6.0,
    dpi: int = 120,
) -> Dict[str, str]:
    return generate_single_video_animation(
        multi_bounce_res=multi_bounce_res,
        outcome=outcome,
        field=field,
        fielders=fielders,
        output_mp4_path=output_mp4_path,
        output_gif_path=output_gif_path,
        scenario_title="Hawkeye 3D Trajectory Simulation",
        fps=fps,
        max_duration_s=max_duration_s,
        dpi=dpi,
    )
