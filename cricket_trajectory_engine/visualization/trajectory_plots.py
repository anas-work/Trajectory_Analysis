"""
Visualization module for 3D cricket ball trajectories, multi-angle views,
comparative aerodynamics, and Monte Carlo landing dispersions.
"""

import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mpl_cache")

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
import numpy as np
from typing import List, Optional, Dict, Any

from cricket_trajectory_engine.physics.flight_simulator import TrajectoryResult
from cricket_trajectory_engine.physics.ground_collision import MultiBounceResult
from cricket_trajectory_engine.prediction.field_geometry import CricketField
from cricket_trajectory_engine.prediction.outcome_engine import FielderPosition


def plot_3d_trajectory(
    multi_bounce_res: MultiBounceResult,
    field: Optional[CricketField] = None,
    fielders: Optional[List[FielderPosition]] = None,
    title: str = "3D Cricket Ball Trajectory Simulation",
    filename: str = "trajectory_3d.png",
) -> str:
    """Generates a full 3D trajectory visualization with ground boundary."""
    pos = multi_bounce_res.positions_m
    bounces = multi_bounce_res.bounces
    field_obj = field or CricketField()

    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(1, 1, 1, projection="3d")

    # Plot airborne/flight trajectory:
    ax.plot(pos[:, 0], pos[:, 1], pos[:, 2], color="#1f77b4", linewidth=2.5, label="Flight Path")

    # Launch point:
    ax.scatter([pos[0, 0]], [pos[0, 1]], [pos[0, 2]], color="green", s=90, marker="o", label="Launch / Bat Contact")

    # Apex:
    apex_idx = int(np.argmax(pos[:, 2]))
    ax.scatter([pos[apex_idx, 0]], [pos[apex_idx, 1]], [pos[apex_idx, 2]], color="purple", s=80, marker="^", label=f"Apex ({pos[apex_idx, 2]:.1f}m)")

    # First impact:
    if bounces:
        first_b = bounces[0]
        ax.scatter([first_b.position_m[0]], [first_b.position_m[1]], [first_b.position_m[2]],
                   color="red", s=110, marker="X", label=f"1st Impact ({first_b.pre_speed_m_s:.1f} m/s)")
        # Subsequent bounces:
        for b in bounces[1:]:
            ax.scatter([b.position_m[0]], [b.position_m[1]], [b.position_m[2]],
                       color="orange", s=60, marker="x")

    # Stopping position:
    ax.scatter([pos[-1, 0]], [pos[-1, 1]], [pos[-1, 2]], color="black", s=80, marker="s", label="Final Stopping Point")

    # Field Boundary at Z = 0:
    theta_bnd = np.linspace(0, 2 * np.pi, 150)
    bnd_radii = np.array([field_obj.boundary_radius_at_azimuth(th) for th in theta_bnd])
    xb = bnd_radii * np.cos(theta_bnd)
    yb = bnd_radii * np.sin(theta_bnd)
    zb = np.zeros_like(xb)
    ax.plot(xb, yb, zb, color="darkred", linestyle="--", linewidth=1.8, label=f"Boundary ({field_obj.radius_m:.0f}m)")

    # 30-yard inner circle:
    r_inner = field_obj.inner_ring_radius_m
    xi = r_inner * np.cos(theta_bnd)
    yi = r_inner * np.sin(theta_bnd)
    zi = np.zeros_like(xi)
    ax.plot(xi, yi, zi, color="gray", linestyle=":", linewidth=1.2, label="30-Yard Ring")

    # Fielders:
    if fielders:
        fx = [f.x_m for f in fielders]
        fy = [f.y_m for f in fielders]
        fz = [0.0 for _ in fielders]
        ax.scatter(fx, fy, fz, color="darkblue", s=50, marker="d", label="Fielders")

    ax.set_xlabel("X (Forward / m)", labelpad=10)
    ax.set_ylabel("Y (Lateral / m)", labelpad=10)
    ax.set_zlabel("Z (Height / m)", labelpad=10)
    ax.set_title(title, pad=15, fontsize=14, fontweight="bold")
    ax.legend(loc="upper left", bbox_to_anchor=(1.05, 1.0))

    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(filename)) or ".", exist_ok=True)
    fig.savefig(filename, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return filename


def plot_trajectory_views(
    multi_bounce_res: MultiBounceResult,
    field: Optional[CricketField] = None,
    filename: str = "trajectory_multi_views.png",
) -> str:
    """Generates a 3-panel 2D engineering projection (Top-down, Side elevation, and Velocity Profile)."""
    pos = multi_bounce_res.positions_m
    vel = multi_bounce_res.velocities_m_s
    t = multi_bounce_res.time_s
    field_obj = field or CricketField()

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # 1. Top-down view (X vs Y):
    ax0 = axes[0]
    ax0.plot(pos[:, 0], pos[:, 1], color="#1f77b4", linewidth=2, label="Ground Track")
    ax0.scatter([pos[0, 0]], [pos[0, 1]], color="green", s=70, label="Launch")

    if multi_bounce_res.bounces:
        first_b = multi_bounce_res.bounces[0]
        ax0.scatter([first_b.position_m[0]], [first_b.position_m[1]], color="red", marker="X", s=90, label="1st Impact")
        for b in multi_bounce_res.bounces[1:]:
            ax0.scatter([b.position_m[0]], [b.position_m[1]], color="orange", marker="x", s=50)

    theta = np.linspace(0, 2 * np.pi, 200)
    bnd_radii = np.array([field_obj.boundary_radius_at_azimuth(th) for th in theta])
    ax0.plot(bnd_radii * np.cos(theta), bnd_radii * np.sin(theta), "r--", linewidth=1.5, label="Boundary")
    ax0.plot(field_obj.inner_ring_radius_m * np.cos(theta),
             field_obj.inner_ring_radius_m * np.sin(theta), "k:", linewidth=1.0, label="30y Ring")

    ax0.set_xlabel("X (Forward / m)")
    ax0.set_ylabel("Y (Lateral / m)")
    ax0.set_title("Top-Down Ground View (X vs Y)")
    ax0.axis("equal")
    ax0.grid(True, alpha=0.3)
    ax0.legend(loc="best", fontsize=9)

    # 2. Side-elevation view (X vs Z):
    ax1 = axes[1]
    ax1.plot(pos[:, 0], pos[:, 2], color="#1f77b4", linewidth=2, label="Elevation Profile")
    ax1.axhline(0.0, color="brown", linewidth=2.0, label="Ground")
    ax1.set_xlabel("X (Forward / m)")
    ax1.set_ylabel("Z (Height / m)")
    ax1.set_title("Side Elevation View (X vs Z)")
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="best", fontsize=9)

    # 3. Speed & Velocity Components vs Time:
    ax2 = axes[2]
    speeds = np.linalg.norm(vel, axis=1)
    ax2.plot(t, speeds, "k-", linewidth=2.0, label="|V| (Total Speed)")
    ax2.plot(t, vel[:, 0], "b--", label="Vx (Forward)")
    ax2.plot(t, vel[:, 1], "g--", label="Vy (Lateral)")
    ax2.plot(t, vel[:, 2], "r--", label="Vz (Vertical)")
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Velocity (m/s)")
    ax2.set_title("Velocity Evolution vs Time")
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc="best", fontsize=9)

    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(filename)) or ".", exist_ok=True)
    fig.savefig(filename, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return filename


def plot_comparative_physics(
    gravity_res: TrajectoryResult,
    drag_res: TrajectoryResult,
    magnus_topspin_res: Optional[TrajectoryResult] = None,
    magnus_backspin_res: Optional[TrajectoryResult] = None,
    filename: str = "trajectory_physics_comparison.png",
) -> str:
    """
    Compares Gravity-only, Drag, and Magnus-enabled simulations.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Side view:
    ax1.plot(gravity_res.positions_m[:, 0], gravity_res.positions_m[:, 2], "k--", linewidth=2,
             label=f"Vacuum Ballistic (Range: {gravity_res.horizontal_range_m:.1f}m, Apex: {gravity_res.max_height_m:.1f}m)")
    ax1.plot(drag_res.positions_m[:, 0], drag_res.positions_m[:, 2], "b-", linewidth=2,
             label=f"Gravity + Drag (Range: {drag_res.horizontal_range_m:.1f}m, Apex: {drag_res.max_height_m:.1f}m)")

    if magnus_topspin_res:
        ax1.plot(magnus_topspin_res.positions_m[:, 0], magnus_topspin_res.positions_m[:, 2], "r-.", linewidth=2,
                 label=f"Drag + Topspin (Range: {magnus_topspin_res.horizontal_range_m:.1f}m, Apex: {magnus_topspin_res.max_height_m:.1f}m)")
    if magnus_backspin_res:
        ax1.plot(magnus_backspin_res.positions_m[:, 0], magnus_backspin_res.positions_m[:, 2], "g:", linewidth=2,
                 label=f"Drag + Backspin (Range: {magnus_backspin_res.horizontal_range_m:.1f}m, Apex: {magnus_backspin_res.max_height_m:.1f}m)")

    ax1.axhline(0.0, color="brown", linewidth=1.5)
    ax1.set_xlabel("X Forward (m)")
    ax1.set_ylabel("Z Height (m)")
    ax1.set_title("Aerodynamic Effect Comparison (Side View)")
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="upper right", fontsize=8.5)

    # Top-down view:
    ax2.plot(gravity_res.positions_m[:, 0], gravity_res.positions_m[:, 1], "k--", label="Vacuum")
    ax2.plot(drag_res.positions_m[:, 0], drag_res.positions_m[:, 1], "b-", label="Drag")
    if magnus_topspin_res:
        ax2.plot(magnus_topspin_res.positions_m[:, 0], magnus_topspin_res.positions_m[:, 1], "r-.", label="Topspin")
    if magnus_backspin_res:
        ax2.plot(magnus_backspin_res.positions_m[:, 0], magnus_backspin_res.positions_m[:, 1], "g:", label="Backspin")

    ax2.set_xlabel("X Forward (m)")
    ax2.set_ylabel("Y Lateral (m)")
    ax2.set_title("Aerodynamic Effect Comparison (Top-Down)")
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc="best", fontsize=9)

    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(filename)) or ".", exist_ok=True)
    fig.savefig(filename, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return filename


def plot_monte_carlo_distribution(
    mc_summary,
    field: Optional[CricketField] = None,
    filename: str = "trajectory_monte_carlo.png",
) -> str:
    """Generates Monte Carlo landing dispersion and confidence distribution plot."""
    landings = mc_summary.all_landing_positions_m
    ranges = mc_summary.all_ranges_m
    field_obj = field or CricketField()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # 1. 2D Landing Scatter:
    ax1.scatter(landings[:, 0], landings[:, 1], color="#1f77b4", alpha=0.6, s=35, label=f"Simulated Landings (N={mc_summary.n_simulations})")
    ax1.scatter([mc_summary.landing_x_stats_m["mean"]], [mc_summary.landing_y_stats_m["mean"]],
                color="red", marker="P", s=120, label="Mean Landing")

    # Boundary:
    theta = np.linspace(0, 2 * np.pi, 200)
    bnd_radii = np.array([field_obj.boundary_radius_at_azimuth(th) for th in theta])
    ax1.plot(bnd_radii * np.cos(theta), bnd_radii * np.sin(theta), "r--", linewidth=1.8, label="Boundary")

    ax1.set_xlabel("X Forward (m)")
    ax1.set_ylabel("Y Lateral (m)")
    ax1.set_title(f"Landing Dispersion (P(Six)={mc_summary.probability_six*100:.1f}%, P(Four)={mc_summary.probability_four*100:.1f}%)")
    ax1.axis("equal")
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="best", fontsize=8.5)

    # 2. Histogram of Horizontal Ranges:
    ax2.hist(ranges, bins=20, color="skyblue", edgecolor="navy", alpha=0.7)
    ax2.axvline(mc_summary.horizontal_range_stats_m["mean"], color="red", linestyle="-", linewidth=2,
                label=f"Mean Range: {mc_summary.horizontal_range_stats_m['mean']:.1f}m")
    ax2.axvline(mc_summary.horizontal_range_stats_m["p5"], color="orange", linestyle="--",
                label=f"5th %ile: {mc_summary.horizontal_range_stats_m['p5']:.1f}m")
    ax2.axvline(mc_summary.horizontal_range_stats_m["p95"], color="green", linestyle="--",
                label=f"95th %ile: {mc_summary.horizontal_range_stats_m['p95']:.1f}m")
    ax2.set_xlabel("Horizontal Range (m)")
    ax2.set_ylabel("Frequency Count")
    ax2.set_title("Range Distribution (Monte Carlo Ensemble)")
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc="best", fontsize=9)

    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(filename)) or ".", exist_ok=True)
    fig.savefig(filename, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return filename

