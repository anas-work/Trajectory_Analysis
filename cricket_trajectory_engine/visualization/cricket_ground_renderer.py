"""
Broadcast-grade 3D Cricket Ground and Hawkeye Trajectory Renderer.

Features:
- Precision cricket field geometry based on international MCC regulations.
- Authentic 22-yard clay turf pitch, popping/bowling creases, and 3D wickets with bails.
- Realistic outfield grass with alternating mowing bands and 30-yard fielding ring with discs.
- Boundary rope with 3D foam advertising cushions.
- Tactically accurate 11-player field settings (Off-side vs Leg-side orientation).
- Hawkeye-style multi-layer glowing trajectory arc, altitude drop lines, ground shadow,
  apex badge, pitch impact ripples, and boundary rope clearance banners.
"""

import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mpl_cache")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
from typing import List, Optional, Tuple, Dict, Any

from cricket_trajectory_engine.physics.ground_collision import MultiBounceResult
from cricket_trajectory_engine.prediction.field_geometry import CricketField
from cricket_trajectory_engine.prediction.outcome_engine import FielderPosition, CricketOutcome


# Professional Broadcast Palette:
COLOR_BG = "#081018"               # Deep dark stadium sky/canvas
COLOR_OUTFIELD_A = "#1a471c"       # Deep emerald turf
COLOR_OUTFIELD_B = "#215324"       # Light green mowing band
COLOR_PITCH = "#d4b886"            # Natural clay/turf pitch strip
COLOR_PITCH_EDGE = "#b89a65"       # Pitch edge shading
COLOR_CREASE = "#ffffff"           # Crisp white crease paint
COLOR_STUMP = "#f39c12"            # Wooden wickets
COLOR_BAIL = "#e67e22"             # Wooden bails
COLOR_ROPE = "#f8f9fa"             # White boundary rope
COLOR_CUSHION = "#c0392b"          # Red foam boundary wedge
COLOR_RING = "rgba(255, 255, 255, 0.65)" # 30-yard circle
COLOR_DISC = "#ffffff"             # White fielding circle discs
COLOR_ARC_CORE = "#ffd700"         # Bright golden yellow trajectory core
COLOR_ARC_GLOW = "#e74c3c"         # Crimson red trajectory glow
COLOR_ROLL = "#f39c12"             # Amber gold post-bounce track
COLOR_SHADOW = "#1b2832"           # Dark turf shadow projection
COLOR_RIBS = "rgba(231, 76, 60, 0.35)" # Vertical drop ribs


def get_international_cricket_fielders(preset: str = "balanced") -> List[FielderPosition]:
    """
    Returns authentic fielding positions for a right-handed batsman.
    Striker's crease is at (0, 0); bowler runs in from +X (from 20.12m).
    
    Coordinate convention:
    +X: Straight downfield towards bowler/long-off/long-on.
    -X: Behind batsman towards keeper/slips/third-man/fine-leg.
    +Y: Off-side (point, covers, mid-off).
    -Y: Leg-side (square leg, mid-wicket, mid-on).
    """
    if preset == "balanced":
        # Standard ODI / T20 field with 4 in deep, 7 in ring/crease:
        return [
            FielderPosition("WK", "Wicket-Keeper", x_m=-3.8, y_m=0.2, max_sprint_speed_m_s=6.5),
            FielderPosition("1SL", "First Slip", x_m=-6.2, y_m=2.8, max_sprint_speed_m_s=6.5),
            FielderPosition("PT", "Point", x_m=4.0, y_m=22.0, max_sprint_speed_m_s=7.2),
            FielderPosition("CV", "Cover", x_m=18.0, y_m=20.0, max_sprint_speed_m_s=7.2),
            FielderPosition("MOF", "Mid-Off", x_m=28.0, y_m=7.5, max_sprint_speed_m_s=7.0),
            FielderPosition("MON", "Mid-On", x_m=28.0, y_m=-7.5, max_sprint_speed_m_s=7.0),
            FielderPosition("MW", "Mid-Wicket", x_m=18.0, y_m=-20.0, max_sprint_speed_m_s=7.0),
            FielderPosition("SQL", "Square Leg", x_m=3.0, y_m=-22.0, max_sprint_speed_m_s=6.8),
            FielderPosition("DCOV", "Deep Cover", x_m=48.0, y_m=45.0, max_sprint_speed_m_s=7.5),
            FielderPosition("LON", "Long-On", x_m=64.0, y_m=-16.0, max_sprint_speed_m_s=7.5),
            FielderPosition("DMW", "Deep Mid-Wicket", x_m=45.0, y_m=-48.0, max_sprint_speed_m_s=7.5),
        ]
    elif preset == "lofted_catch":
        # Field setting tailored for deep catching (deep fielders at boundary):
        return [
            FielderPosition("WK", "Wicket-Keeper", x_m=-3.8, y_m=0.2, max_sprint_speed_m_s=6.5),
            FielderPosition("1SL", "First Slip", x_m=-6.2, y_m=2.8, max_sprint_speed_m_s=6.5),
            FielderPosition("PT", "Point", x_m=4.0, y_m=22.0, max_sprint_speed_m_s=7.2),
            FielderPosition("CV", "Cover", x_m=18.0, y_m=20.0, max_sprint_speed_m_s=7.2),
            FielderPosition("MOF", "Mid-Off", x_m=26.0, y_m=7.5, max_sprint_speed_m_s=7.0),
            FielderPosition("MON", "Mid-On", x_m=26.0, y_m=-7.5, max_sprint_speed_m_s=7.0),
            FielderPosition("SQL", "Square Leg", x_m=3.0, y_m=-22.0, max_sprint_speed_m_s=6.8),
            FielderPosition("LOF", "Long-Off", x_m=62.0, y_m=15.0, max_sprint_speed_m_s=7.5),
            FielderPosition("LON", "Long-On", x_m=62.0, y_m=-15.0, max_sprint_speed_m_s=7.5),
            FielderPosition("DMW", "Deep Mid-Wicket", x_m=46.0, y_m=-38.0, max_sprint_speed_m_s=7.5),
            FielderPosition("DCOV", "Deep Cover", x_m=45.0, y_m=45.0, max_sprint_speed_m_s=7.5),
        ]
    return get_international_cricket_fielders("balanced")


def draw_authentic_cricket_ground_3d(
    ax,
    field: Optional[CricketField] = None,
    fielders: Optional[List[FielderPosition]] = None,
):
    """
    Renders an authentic cricket field onto a 3D Matplotlib axis:
    - Alternating turf green grass bands.
    - 22-yard tan pitch with white creases and 3D wickets.
    - 30-yard fielding oval.
    - Boundary rope with foam cushions.
    - Tactically accurate fielding markers.
    """
    field_obj = field or CricketField()
    r_bnd = field_obj.radius_m

    # 1. Concentric Lawn Mowing Rings (Clean 2D polygon projection at Z=0):
    band_steps = [0.0, 15.0, 30.0, 45.0, 60.0, r_bnd + 4.0]
    th = np.linspace(0, 2 * np.pi, 120)
    for i in range(len(band_steps) - 1):
        r1, r2 = band_steps[i], band_steps[i + 1]
        c = COLOR_OUTFIELD_B if (i % 2 == 0) else COLOR_OUTFIELD_A
        # Draw ring boundaries with soft shaded fill:
        x_ring = r2 * np.cos(th)
        y_ring = r2 * np.sin(th)
        z_ring = np.zeros_like(x_ring)
        ax.plot(x_ring, y_ring, z_ring, color=c, linewidth=0.5, alpha=0.3)

    # 2. Cricket Pitch Strip (22 yards = 20.12m long by 10 ft = 3.05m wide):
    # Striker stumps at X = -1.22m, popping crease at X = 0.0m.
    # Non-striker stumps at X = 18.90m, popping crease at X = 17.68m.
    px = [-1.8, 20.2, 20.2, -1.8]
    py = [-1.52, -1.52, 1.52, 1.52]
    pz = [0.001, 0.001, 0.001, 0.001]
    pitch_poly = Poly3DCollection([list(zip(px, py, pz))], facecolors=COLOR_PITCH, edgecolors=COLOR_PITCH_EDGE, linewidths=1.5, alpha=0.95)
    ax.add_collection3d(pitch_poly)

    # Pitch markings (white paint):
    # Batting end popping crease (X = 0.0m) and bowling end popping crease (X = 17.68m):
    ax.plot([0.0, 0.0], [-1.83, 1.83], [0.002, 0.002], color=COLOR_CREASE, linewidth=2.0)
    ax.plot([17.68, 17.68], [-1.83, 1.83], [0.002, 0.002], color=COLOR_CREASE, linewidth=2.0)
    # Bowling creases at wickets (X = -1.22m and X = 18.90m):
    ax.plot([-1.22, -1.22], [-1.32, 1.32], [0.002, 0.002], color=COLOR_CREASE, linewidth=1.5, linestyle=":")
    ax.plot([18.90, 18.90], [-1.32, 1.32], [0.002, 0.002], color=COLOR_CREASE, linewidth=1.5, linestyle=":")

    # 3D Wickets & Bails (Height: 28 inches = 0.71m):
    for stump_y in [-0.11, 0.0, 0.11]:
        ax.plot([-1.22, -1.22], [stump_y, stump_y], [0.0, 0.71], color=COLOR_STUMP, linewidth=2.5)
        ax.plot([18.90, 18.90], [stump_y, stump_y], [0.0, 0.71], color=COLOR_STUMP, linewidth=2.5)
    # Bails on top:
    ax.plot([-1.22, -1.22], [-0.13, 0.13], [0.71, 0.71], color=COLOR_BAIL, linewidth=2.0)
    ax.plot([18.90, 18.90], [-0.13, 0.13], [0.71, 0.71], color=COLOR_BAIL, linewidth=2.0)

    # 3. 30-Yard Fielding Circle (27.432 m radius):
    theta_ring = np.linspace(0, 2 * np.pi, 180)
    r_inner = field_obj.inner_ring_radius_m
    xr = r_inner * np.cos(theta_ring)
    yr = r_inner * np.sin(theta_ring)
    zr = np.full_like(xr, 0.002)
    ax.plot(xr, yr, zr, color="#ecf0f1", linestyle="--", linewidth=1.2, alpha=0.7, label="30-Yard Ring")

    # White fielding disc markers:
    theta_discs = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    xd = r_inner * np.cos(theta_discs)
    yd = r_inner * np.sin(theta_discs)
    ax.scatter(xd, yd, np.zeros_like(xd) + 0.003, color=COLOR_DISC, s=20, marker="o", alpha=0.9)

    # 4. White Boundary Rope (70m radius):
    theta_bnd = np.linspace(0, 2 * np.pi, 220)
    bnd_radii = np.array([field_obj.boundary_radius_at_azimuth(th_i) for th_i in theta_bnd])
    xb = bnd_radii * np.cos(theta_bnd)
    yb = bnd_radii * np.sin(theta_bnd)
    zb = np.full_like(xb, 0.003)
    ax.plot(xb, yb, zb, color=COLOR_ROPE, linewidth=3.5, label=f"Boundary Rope ({r_bnd:.0f}m)")

    # Red foam advertising wedges spaced along boundary:
    theta_wedges = np.linspace(0, 2 * np.pi, 36, endpoint=False)
    rw = np.array([field_obj.boundary_radius_at_azimuth(th_i) for th_i in theta_wedges])
    ax.scatter(rw * np.cos(theta_wedges), rw * np.sin(theta_wedges), np.zeros_like(theta_wedges) + 0.004,
               color=COLOR_CUSHION, s=32, marker="^", label="Rope Cushions")

    # 5. Authentic 3D Humanoid Fielders:
    if fielders:
        for f in fielders:
            fx, fy = f.x_m, f.y_m
            is_wk = "keeper" in f.role_name.lower() or f.role_name == "WK"
            jersey_color = "#f39c12" if is_wk else "#00b4d8"
            cap_color = "#c0392b" if is_wk else "#0a3d62"

            # Ground shadow disc
            th_s = np.linspace(0, 2 * np.pi, 16)
            ax.plot(fx + 0.5 * np.cos(th_s), fy + 0.5 * np.sin(th_s), np.zeros_like(th_s) + 0.004,
                    color="#0a1a24", linewidth=1.5, alpha=0.6)

            if is_wk:
                # Crouching stance for wicketkeeper behind stumps
                # Legs in crouch
                ax.plot([fx - 0.2, fx], [fy - 0.15, fy], [0.0, 0.45], color="#ffffff", linewidth=3.0)
                ax.plot([fx + 0.2, fx], [fy + 0.15, fy], [0.0, 0.45], color="#ffffff", linewidth=3.0)
                # Crouched Torso
                ax.plot([fx, fx + 0.15], [fy, fy], [0.45, 0.85], color=jersey_color, linewidth=5.5)
                # Arms with gloves
                ax.plot([fx + 0.1, fx + 0.35], [fy - 0.2, fy - 0.1], [0.75, 0.55], color="#ffd166", linewidth=2.8)
                ax.plot([fx + 0.1, fx + 0.35], [fy + 0.2, fy + 0.1], [0.75, 0.55], color="#ffd166", linewidth=2.8)
                # Head with helmet
                ax.scatter([fx + 0.18], [fy], [1.02], color=cap_color, s=75, marker="o", edgecolors="#ffffff", linewidths=1.2)
                # Role text
                ax.text(fx, fy, 1.35, f.role_name, fontsize=7.0, color="#f1c40f", fontweight="bold",
                        ha="center", bbox=dict(boxstyle="round,pad=0.2", facecolor="#1e2b37", alpha=0.9, edgecolor="#f1c40f", linewidth=0.5))
            else:
                # Athletic standing / ready posture for fielders
                # White trousers (legs)
                ax.plot([fx - 0.18, fx], [fy, fy], [0.0, 0.75], color="#ffffff", linewidth=2.5)
                ax.plot([fx + 0.18, fx], [fy, fy], [0.0, 0.75], color="#ffffff", linewidth=2.5)
                # Athletic Jersey Torso
                ax.plot([fx, fx], [fy, fy], [0.75, 1.35], color=jersey_color, linewidth=5.0)
                # Arms in ready catching pose (bent forward towards batsman at origin)
                dx_to_bat = -fx
                dy_to_bat = -fy
                dist_bat = max(1e-3, np.hypot(dx_to_bat, dy_to_bat))
                ux = dx_to_bat / dist_bat
                uy = dy_to_bat / dist_bat
                # Left and right arm extensions
                ax.plot([fx, fx + 0.3 * ux], [fy - 0.2, fy - 0.1 + 0.2 * uy], [1.25, 0.95], color=jersey_color, linewidth=2.2)
                ax.plot([fx, fx + 0.3 * ux], [fy + 0.2, fy + 0.1 + 0.2 * uy], [1.25, 0.95], color=jersey_color, linewidth=2.2)
                # Head with peaked cricket cap
                ax.scatter([fx], [fy], [1.52], color="#e0ac69", s=45, marker="o")
                ax.scatter([fx + 0.08 * ux], [fy + 0.08 * uy], [1.56], color=cap_color, s=55, marker="o", edgecolors="#ffffff", linewidths=0.8)
                # Cap peak / visor
                ax.plot([fx, fx + 0.22 * ux], [fy, fy + 0.22 * uy], [1.56, 1.54], color=cap_color, linewidth=2.0)
                # Role text
                ax.text(fx, fy, 1.85, f.role_name, fontsize=7.0, color="#ecf0f1",
                        ha="center", bbox=dict(boxstyle="round,pad=0.2", facecolor="#1e2b37", alpha=0.85, edgecolor="none"))


def render_broadcast_stadium_trajectory(
    multi_bounce_res: MultiBounceResult,
    outcome: Optional[CricketOutcome] = None,
    field: Optional[CricketField] = None,
    fielders: Optional[List[FielderPosition]] = None,
    title: str = "Hawkeye 3D Cricket Trajectory Simulation",
    filename: str = "cricket_stadium_broadcast_3d.png",
    elev: float = 24.0,
    azim: float = -62.0,
) -> str:
    """
    Renders a broadcast-quality Hawkeye 3D stadium image with professional lighting,
    trajectory glow, altitude drop lines, and telemetry callout banners.
    """
    pos = multi_bounce_res.positions_m
    bounces = multi_bounce_res.bounces
    first_b = multi_bounce_res.first_bounce
    field_obj = field or CricketField()

    fig = plt.figure(figsize=(16, 9.5), facecolor=COLOR_BG)
    ax = fig.add_subplot(1, 1, 1, projection="3d", facecolor=COLOR_BG)

    # 1. Authentic Ground Features:
    draw_authentic_cricket_ground_3d(ax, field_obj, fielders)

    # 2. Ground Shadow Projection (Z = 0):
    ax.plot(pos[:, 0], pos[:, 1], np.zeros(len(pos)) + 0.002, color=COLOR_SHADOW, linewidth=2.2, linestyle="--", label="Ground Path")

    # 3. Altitude Drop Lines (Ribs) every N frames during airborne phase:
    t_first = first_b.time_s if first_b else float("inf")
    idx_first_bounce = np.searchsorted(multi_bounce_res.time_s, t_first)
    air_slice = pos[:idx_first_bounce]
    step = max(1, len(air_slice) // 20)
    for i in range(0, len(air_slice), step):
        p_i = air_slice[i]
        if p_i[2] > 0.15:
            ax.plot([p_i[0], p_i[0]], [p_i[1], p_i[1]], [0.0, p_i[2]], color="#e74c3c", alpha=0.35, linewidth=1.2)

    # 4. Multi-layered Glowing Trajectory Arc:
    if first_b:
        air_pts = pos[:idx_first_bounce + 1]
        roll_pts = pos[idx_first_bounce:]
        # Outer glow:
        ax.plot(air_pts[:, 0], air_pts[:, 1], air_pts[:, 2], color=COLOR_ARC_GLOW, linewidth=4.5, alpha=0.85, label="Flight Arc")
        # Inner golden core:
        ax.plot(air_pts[:, 0], air_pts[:, 1], air_pts[:, 2], color=COLOR_ARC_CORE, linewidth=1.8, alpha=1.0)
        # Roll path:
        if len(roll_pts) > 1:
            ax.plot(roll_pts[:, 0], roll_pts[:, 1], roll_pts[:, 2], color=COLOR_ROLL, linewidth=2.8, linestyle="-", label="Outfield Roll")
    else:
        ax.plot(pos[:, 0], pos[:, 1], pos[:, 2], color=COLOR_ARC_GLOW, linewidth=4.5, label="Flight Arc")
        ax.plot(pos[:, 0], pos[:, 1], pos[:, 2], color=COLOR_ARC_CORE, linewidth=1.8)

    # 5. Bat Impact Point:
    ax.scatter([pos[0, 0]], [pos[0, 1]], [pos[0, 2]], color="#2ecc71", s=150, marker="o", edgecolors="#ffffff", linewidths=2.0, label="Bat Impact")
    ax.text(pos[0, 0], pos[0, 1], pos[0, 2] + 1.2, "BAT IMPACT\n(0,0)", color="#2ecc71", fontsize=8.0, fontweight="bold", ha="center")

    # 6. Apex Maximum Height:
    apex_idx = int(np.argmax(pos[:, 2]))
    apex_p = pos[apex_idx]
    ax.scatter([apex_p[0]], [apex_p[1]], [apex_p[2]], color="#9b59b6", s=130, marker="^", edgecolors="#ffffff", linewidths=1.8, label=f"Apex ({apex_p[2]:.1f}m)")
    ax.text(apex_p[0], apex_p[1], apex_p[2] + 1.4, f"▲ APEX: {apex_p[2]:.1f}m", color="#f1c40f", fontsize=9.0, fontweight="bold", ha="center")

    # 7. First Ground Impact / Pitch Bounce:
    if first_b:
        bp = first_b.position_m
        d_pitch = float(np.hypot(bp[0], bp[1]))
        ax.scatter([bp[0]], [bp[1]], [bp[2]], color="#e74c3c", s=180, marker="X", edgecolors="#ffffff", linewidths=2.0, label="1st Pitch Bounce")
        # Impact ripple:
        for rip_r in [1.5, 3.0]:
            th_rip = np.linspace(0, 2 * np.pi, 40)
            ax.plot(bp[0] + rip_r * np.cos(th_rip), bp[1] + rip_r * np.sin(th_rip), np.zeros_like(th_rip) + 0.005,
                    color="#e74c3c", linewidth=1.2, alpha=0.7)
        ax.text(bp[0], bp[1], bp[2] + 2.2,
                f"1st BOUNCE: {d_pitch:.1f}m\nSpeed: {first_b.pre_speed_m_s*3.6:.0f} km/h",
                color="#ffffff", fontsize=8.5, ha="center",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#c0392b", alpha=0.9, edgecolor="none"))

    # 8. Subsequent Bounces:
    for b in bounces[1:]:
        ax.scatter([b.position_m[0]], [b.position_m[1]], [b.position_m[2]], color="#f39c12", s=70, marker="x", linewidths=1.5)

    # 9. Final Position or Rope Clearance Marker:
    final_p = pos[-1]
    if outcome and outcome.rope_clearance.clears_rope:
        rp = outcome.rope_clearance.rope_crossing_position_m
        if rp is not None:
            ax.scatter([rp[0]], [rp[1]], [rp[2]], color="#f1c40f", s=250, marker="*", edgecolors="#c0392b", linewidths=2.0, label="Boundary Cleared!")
            v_res = outcome.rope_clearance.residual_speed_at_rope_m_s or 0.0
            call_label = "MAXIMUM SIX!" if "SIX" in outcome.primary_call else "BOUNDARY FOUR!"
            ax.text(rp[0], rp[1], rp[2] + 2.8,
                    f"★ {call_label}\nCleared Rope at {v_res*3.6:.0f} km/h",
                    color="#f1c40f", fontsize=9.5, fontweight="bold", ha="center",
                    bbox=dict(boxstyle="round,pad=0.4", facecolor="#27ae60", alpha=0.92, edgecolor="#ffffff"))
    else:
        ax.scatter([final_p[0]], [final_p[1]], [final_p[2]], color="#ecf0f1", s=110, marker="s", edgecolors="#e67e22", label="Ball Stopped")
        if outcome:
            margin = abs(outcome.rope_clearance.margin_m)
            ax.text(final_p[0], final_p[1], final_p[2] + 2.0,
                    f"PULLED UP SHORT\n{margin:.1f}m inside rope",
                    color="#ffffff", fontsize=8.5, ha="center",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="#d35400", alpha=0.88, edgecolor="none"))

    # Limits and Camera Perspective:
    lim = field_obj.radius_m + 8.0
    ax.set_xlim(-16.0, lim)
    ax.set_ylim(-lim * 0.72, lim * 0.72)
    ax.set_zlim(0.0, max(24.0, np.max(pos[:, 2]) * 1.35))
    ax.set_xlabel("X (Downfield / m)", color="#bdc3c7", labelpad=8)
    ax.set_ylabel("Y (Cross-field / m)", color="#bdc3c7", labelpad=8)
    ax.set_zlabel("Z (Height / m)", color="#bdc3c7", labelpad=8)
    ax.tick_params(colors="#7f8c8d", labelsize=8)
    ax.view_init(elev=elev, azim=azim)

    # Broadcast HUD Header:
    v0_init = multi_bounce_res.velocities_m_s[0]
    speed0 = np.linalg.norm(v0_init)
    elev0 = np.degrees(np.arctan2(v0_init[2], np.hypot(v0_init[0], v0_init[1])))
    hud_header = (
        f"HAWKEYE 3D BROADCAST | Launch Speed: {speed0*3.6:.1f} km/h ({speed0:.1f} m/s) "
        f"| Launch Angle: {elev0:.1f}° | Apex: {apex_p[2]:.1f}m"
    )
    fig.text(0.5, 0.96, hud_header, color="#ecf0f1", fontsize=11, fontfamily="monospace",
             ha="center", bbox=dict(boxstyle="round,pad=0.4", facecolor="#15202b", edgecolor="#2c3e50"))

    # Broadcast Bottom Callout Banner:
    if outcome:
        banner = f"OUTCOME: [{outcome.primary_call}] — {outcome.rope_clearance.summary}"
        fig.text(0.5, 0.03, banner, color="#f1c40f", fontsize=11, fontweight="bold",
                 ha="center", bbox=dict(boxstyle="round,pad=0.5", facecolor="#15202b", edgecolor="#f1c40f", linewidth=1.5))

    ax.set_title(title, pad=18, fontsize=14, fontweight="bold", color="#ffffff")
    ax.legend(loc="upper left", bbox_to_anchor=(0.02, 0.92), facecolor="#15202b", edgecolor="#34495e", labelcolor="#ffffff", fontsize=8.5)

    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(filename)) or ".", exist_ok=True)
    fig.savefig(filename, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return filename


render_cricket_stadium_trajectory = render_broadcast_stadium_trajectory
get_standard_cricket_fielders = get_international_cricket_fielders
