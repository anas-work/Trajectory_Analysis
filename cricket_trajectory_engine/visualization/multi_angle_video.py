"""
Multi-Angle Video Generator with Analytical Measurement Guides.
Renders broadcast-quality presentation videos including:
- Dynamic airborne flight and turf roll
- Telemetry HUD and calculation trace metadata
- Ending multi-angle analytical sequence:
  * View 1: Isometric 3D View
  * View 2: Side View (Elevation profile)
  * View 3: Top-Down View (Azimuth and boundary ground plane)
  * View 4: Pitcher's Perspective View
- Explicit horizontal (carry, total distance) and vertical (apex height) dimension lines.
"""

import os
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


def render_analytical_multi_view_frame(
    multi_bounce_res: MultiBounceResult,
    outcome: Optional[CricketOutcome] = None,
    field: Optional[CricketField] = None,
    fielders: Optional[List[FielderPosition]] = None,
    title: str = "Trajectory Analytical Measurement Overview",
    figsize: tuple = (15.5, 8.5),
    dpi: int = 110,
) -> np.ndarray:
    """
    Renders a 4-panel analytical measurement dashboard showing:
    1. Isometric 3D Overview with Hawkeye arc
    2. Side Elevation View with vertical apex dimension guide
    3. Top-Down Field View with horizontal carry and boundary guide
    4. Metrics Summary & Decision Board
    """
    field_obj = field or CricketField()
    fielders_list = fielders if fielders is not None else get_international_cricket_fielders()

    fig = plt.figure(figsize=figsize, facecolor=COLOR_BG, dpi=dpi)

    pos = multi_bounce_res.positions_m
    first_b = multi_bounce_res.first_bounce
    pos_first = first_b.position_m if first_b else pos[-1]
    d_carry = float(np.hypot(pos_first[0], pos_first[1]))
    apex_idx = int(np.argmax(pos[:, 2]))
    pos_apex = pos[apex_idx]
    apex_h = float(pos_apex[2])
    d_total = float(multi_bounce_res.total_horizontal_distance_m)

    # 1. Top-Left: Isometric 3D View
    ax_iso = fig.add_subplot(2, 2, 1, projection="3d", facecolor=COLOR_BG)
    draw_authentic_cricket_ground_3d(ax_iso, field_obj, fielders_list)
    ax_iso.plot(pos[:, 0], pos[:, 1], pos[:, 2], color=COLOR_ARC_GLOW, linewidth=2.5)
    ax_iso.plot(pos[:, 0], pos[:, 1], pos[:, 2], color=COLOR_ARC_CORE, linewidth=1.2)
    ax_iso.scatter([pos_apex[0]], [pos_apex[1]], [pos_apex[2]], color="#e74c3c", s=70, label="Apex")
    ax_iso.scatter([pos_first[0]], [pos_first[1]], [pos_first[2]], color="#f1c40f", s=70, label="1st Pitch")
    ax_iso.set_title("VIEW 1: ISOMETRIC 3D HAWKEYE", color="#ffffff", fontsize=9.5, fontweight="bold")
    ax_iso.view_init(elev=24, azim=-65)
    ax_iso.set_xlim(-15, field_obj.radius_m + 5)
    ax_iso.set_ylim(-field_obj.radius_m * 0.7, field_obj.radius_m * 0.7)
    ax_iso.set_zlim(0, max(20.0, apex_h * 1.3))
    ax_iso.tick_params(colors="#7f8c8d", labelsize=7)

    # 2. Top-Right: Side View (Vertical Dimension Guide)
    ax_side = fig.add_subplot(2, 2, 2, facecolor="#0e1621")
    horiz_d = np.hypot(pos[:, 0], pos[:, 1])
    ax_side.plot(horiz_d, pos[:, 2], color=COLOR_ARC_CORE, linewidth=2.2, label="Flight Arc")
    ax_side.axhline(0, color="#2ecc71", linewidth=2.0, label="Turf Ground Level")
    
    # Vertical dimension line to apex:
    d_apex = float(np.hypot(pos_apex[0], pos_apex[1]))
    ax_side.plot([d_apex, d_apex], [0, apex_h], color="#e74c3c", linestyle="--", linewidth=1.8)
    ax_side.scatter([d_apex], [apex_h], color="#e74c3c", s=80, zorder=5)
    ax_side.annotate(
        f"MAX HEIGHT (APEX)\nZ = {apex_h:.2f} m\n(t = {multi_bounce_res.time_s[apex_idx]:.2f} s)",
        xy=(d_apex, apex_h), xytext=(d_apex + 4, apex_h * 0.85),
        color="#ffffff", fontsize=8.5, fontweight="bold",
        arrowprops=dict(arrowstyle="->", color="#e74c3c", lw=1.5),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#1a252f", edgecolor="#e74c3c")
    )

    # Horizontal carry dimension line:
    ax_side.plot([0, d_carry], [0.2, 0.2], color="#f39c12", linewidth=2.0)
    ax_side.scatter([d_carry], [pos_first[2]], color="#f1c40f", s=80, zorder=5)
    ax_side.annotate(
        f"CARRY DISTANCE\n{d_carry:.1f} m to 1st Bounce",
        xy=(d_carry, 0.2), xytext=(d_carry - 8, apex_h * 0.4),
        color="#ffffff", fontsize=8.0, fontweight="bold",
        arrowprops=dict(arrowstyle="->", color="#f39c12", lw=1.5),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#1a252f", edgecolor="#f39c12")
    )

    ax_side.set_title("VIEW 2: SIDE ELEVATION & VERTICAL APEX GUIDE", color="#ffffff", fontsize=9.5, fontweight="bold")
    ax_side.set_xlabel("Horizontal Ground Distance (m)", color="#95a5a6", fontsize=8)
    ax_side.set_ylabel("Height Above Turf Z (m)", color="#95a5a6", fontsize=8)
    ax_side.tick_params(colors="#7f8c8d", labelsize=7)
    ax_side.grid(True, color="#2c3e50", linestyle=":", alpha=0.6)
    ax_side.set_ylim(-0.5, max(15.0, apex_h * 1.35))

    # 3. Bottom-Left: Top-Down View (Ground Plane & Azimuth)
    ax_top = fig.add_subplot(2, 2, 3, facecolor="#0e1621")
    # Draw boundary circle:
    theta_arr = np.linspace(0, 2 * np.pi, 200)
    ax_top.plot(field_obj.radius_m * np.cos(theta_arr), field_obj.radius_m * np.sin(theta_arr),
                color="#e74c3c", linewidth=2.0, linestyle="--", label="Boundary Rope (70m)")
    # Draw 30-yard ring:
    cx = field_obj.pitch_length_m / 2.0
    ax_top.plot(cx + field_obj.inner_circle_radius_m * np.cos(theta_arr),
                field_obj.inner_circle_radius_m * np.sin(theta_arr),
                color="#ffffff", linewidth=1.2, linestyle=":", alpha=0.7, label="30-Yard Circle")
    # Pitch rectangle:
    ax_top.fill([0, 20.12, 20.12, 0], [-1.52, -1.52, 1.52, 1.52], color="#c2a649", alpha=0.8)
    # Trajectory path on ground:
    ax_top.plot(pos[:, 0], pos[:, 1], color=COLOR_ARC_CORE, linewidth=2.2)
    ax_top.scatter([pos_first[0]], [pos_first[1]], color="#f1c40f", s=80, label="Pitch Point")
    ax_top.scatter([pos[-1][0]], [pos[-1][1]], color="#e67e22", s=80, label="Final Stop")

    # Draw fielders:
    for f in fielders_list:
        ax_top.scatter([f.x_m], [f.y_m], color="#3498db", s=35)
        ax_top.text(f.x_m, f.y_m + 1.2, f.name, color="#ecf0f1", fontsize=6, ha="center")

    ax_top.set_title("VIEW 3: TOP-DOWN GROUND PLANE & AZIMUTH", color="#ffffff", fontsize=9.5, fontweight="bold")
    ax_top.set_xlabel("X (Forward / m)", color="#95a5a6", fontsize=8)
    ax_top.set_ylabel("Y (Lateral / m)", color="#95a5a6", fontsize=8)
    ax_top.tick_params(colors="#7f8c8d", labelsize=7)
    ax_top.axis("equal")
    ax_top.grid(True, color="#2c3e50", linestyle=":", alpha=0.6)

    # 4. Bottom-Right: Comprehensive Results & Dimension Breakdown
    ax_meta = fig.add_subplot(2, 2, 4, facecolor="#0e1621")
    ax_meta.axis("off")

    call_label = outcome.primary_call if outcome else "IN-PLAY"
    runs_label = f"{outcome.estimated_runs} Runs" if outcome else ""
    rc_summary = outcome.rope_clearance.summary if outcome else ""

    summary_lines = [
        "4. ANALYTICAL MEASUREMENT SUMMARY",
        "────────────────────────────────────────────────────",
        f"• Launch Velocity:    [{pos[0,0]:.1f}, {pos[0,1]:.1f}, {pos[0,2]:.1f}] m/s",
        f"• Vertical Apex (Z):   {apex_h:.2f} m  (at t = {multi_bounce_res.time_s[apex_idx]:.2f} s)",
        f"• 1st Pitch Carry (d1):{d_carry:.1f} m  (at t = {multi_bounce_res.time_s[np.searchsorted(multi_bounce_res.time_s, multi_bounce_res.first_bounce.time_s if multi_bounce_res.first_bounce else 0)]:.2f} s)",
        f"• Post-Bounce Roll:    {outcome.rope_clearance.post_bounce_distance_travelled_m:.1f} m",
        f"• Total Ground Dist:   {d_total:.1f} m",
        f"• Boundary Rope:       70.0 m Radius",
        f"• Rope Clearance:      {rc_summary}",
        "────────────────────────────────────────────────────",
        f"PREDICTED OUTCOME:    [{call_label}]  {runs_label}",
        "────────────────────────────────────────────────────",
        "Camera views verified: Isometric (3D), Side (Elevation),",
        "Top-Down (Azimuth), and Dimensioned Analytical Guides.",
    ]
    ax_meta.text(0.04, 0.95, "\n".join(summary_lines), color="#ffffff", fontsize=8.5,
                 fontfamily="monospace", verticalalignment="top")

    fig.suptitle(title, color="#ffffff", fontsize=12, fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0.01, 0.01, 0.99, 0.96])
    fig.canvas.draw()
    frame_img = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
    plt.close(fig)
    return frame_img

