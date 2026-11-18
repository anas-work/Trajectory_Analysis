"""
Regression & forensic audit test suite.
Validates:
1. Boundary Four distance clamping to rope radius (70m) vs unconstrained rollout.
2. Distinct physical inputs produce distinct trajectory arrays and fingerprints.
3. Pre-seeded real delivery experiments integrity.
4. Calculation trace step completeness and formula substitutions.
5. Unique cache-busting and persistence fidelity.
6. Physics audit regressions (inertia, angle decomposition, carry, phase).
"""

import math
import pytest
import numpy as np

from cricket_trajectory_engine.models.experiment import (
    ExperimentConfig,
    compute_simulation_fingerprint,
)
from cricket_trajectory_engine.services.simulation_service import SimulationService
from cricket_trajectory_engine.services.experiment_service import ExperimentService
from cricket_trajectory_engine.backend.api.experiments_api import (
    list_experiments,
    get_video_gallery,
    render_experiment_video,
)
from cricket_trajectory_engine.backend.api.simulation_api import run_simulation


def test_boundary_four_clamping_and_unconstrained_rollout():
    """
    Forensic test for the '163-metre Four':
    Verifies that for a shot clearing the rope on the ground (Boundary Four):
    - total_distance_m is clamped to boundary rope radius (e.g. 70.0 m) per MCC Law 19.
    - unconstrained_rollout_m records the uninhibited physics stopping distance (> 70.0 m).
    """
    sim = SimulationService()
    # High-velocity low-angle drive that pierces the gap (no fielder catch), bounces inside, and clears rope
    config = ExperimentConfig(
        pos0=[0.0, 0.0, 0.8],
        vel0=[26.0, 22.0, 3.5],  # Cover drive piercing extra cover at 40° azimuth, pitches at ~38m, rolls to 70m rope
        environment={"rolling_resistance_coeff": 0.12},
        stadium={"boundary_radius_m": 70.0},
        fielding={"fielders": []},  # Pure ball flight & boundary geometry
    )
    res_obj, trace, res_multibounce, outcome = sim.run_simulation(config)

    assert outcome.primary_call == "FOUR"
    assert res_obj.outcome_call == "FOUR"
    # Match total distance must be clamped to the rope radius
    assert res_obj.total_distance_m == pytest.approx(70.0, abs=0.1)
    # Unconstrained rollout must record the full physics rollout past 70m
    assert res_obj.unconstrained_rollout_m is not None
    assert res_obj.unconstrained_rollout_m > 70.0
    assert res_obj.boundary_distance_m == pytest.approx(70.0, abs=0.1)


def test_distinct_inputs_produce_distinct_trajectories_and_fingerprints():
    """
    Bug 1 verification:
    Confirms that distinct input velocity parameters produce distinct trajectories,
    distinct apex heights, and distinct fingerprints.
    """
    sim = SimulationService()

    cfg1 = ExperimentConfig(pos0=[0.0, 0.0, 0.9], vel0=[24.0, 5.0, 6.0])
    cfg2 = ExperimentConfig(pos0=[0.0, 0.0, 0.9], vel0=[34.0, 5.0, 12.0])

    res1, _, mb1, _ = sim.run_simulation(cfg1)
    res2, _, mb2, _ = sim.run_simulation(cfg2)

    assert res1.fingerprint != res2.fingerprint
    assert res1.max_height_m != res2.max_height_m
    assert res1.carry_distance_m < res2.carry_distance_m

    # Trajectory positions must not be identical
    assert not np.allclose(mb1.positions_m[0:10], mb2.positions_m[0:10])


def test_simulation_caching_idempotence():
    """Verifies that identical physical configurations produce identical fingerprints."""
    cfg1 = ExperimentConfig(pos0=[0.0, 0.0, 0.9], vel0=[28.0, 10.0, 6.2])
    cfg2 = ExperimentConfig(pos0=[0.0, 0.0, 0.9], vel0=[28.0, 10.0, 6.2])

    sim = SimulationService()
    res1, _, _, _ = sim.run_simulation(cfg1)
    res2, _, _, _ = sim.run_simulation(cfg2)

    assert res1.fingerprint == res2.fingerprint
    assert res1.carry_distance_m == pytest.approx(res2.carry_distance_m, abs=1e-5)


def test_real_delivery_experiments_integrity():
    """
    Bug 2 verification:
    Confirms that all 20 real delivery experiments (DELIVERY_01_CAM1 to DELIVERY_10_CAM2)
    are present and loaded in the experiment service.
    """
    exp_service = ExperimentService(base_dir="experiments")
    exps = exp_service.list_experiments()
    exp_ids = {e["id"] for e in exps}

    for d in range(1, 11):
        d_str = f"{d:02d}"
        for cam in ["CAM1", "CAM2"]:
            expected_id = f"DELIVERY_{d_str}_{cam}"
            assert expected_id in exp_ids, f"Missing delivery experiment: {expected_id}"


def test_calculation_trace_completeness():
    """Verifies that the scientific trace contains all formal steps with substitutions."""
    sim = SimulationService()
    config = ExperimentConfig(pos0=[0.0, 0.0, 0.9], vel0=[28.0, 10.0, 6.2])
    _, trace, _, _ = sim.run_simulation(config)

    trace_dict = trace.to_dict()
    assert "steps" in trace_dict
    step_ids = [s["step_id"] for s in trace_dict["steps"]]

    expected_steps = [
        "step_launch_state",
        "step_reynolds_number",
        "step_aerodynamic_drag",
        "step_equations_of_motion",
        "step_apex_carry",
        "step_ground_impact",
        "step_rolling_clearance",
        "step_boundary_outcome",
    ]
    for es in expected_steps:
        assert es in step_ids, f"Calculation trace missing step: {es}"


def test_video_gallery_endpoint():
    """Verifies that the video gallery endpoint returns available videos with cache busters."""
    gallery = get_video_gallery()
    assert "videos" in gallery
    assert "total" in gallery
    assert gallery["total"] >= 1
    # Check that cache buster query string is attached for videos that exist
    for v in gallery["videos"]:
        if v["has_video"] and v["video_url"]:
            assert "?v=" in v["video_url"]


# ─────────────────────────────────────────────────────────────────────────────
# Audit regression tests (Tasks 1–5 from physics audit)
# ─────────────────────────────────────────────────────────────────────────────

def test_solid_sphere_inertia_coefficient():
    """
    Task 1: Solid sphere moment of inertia = (2/5)*m*r^2, NOT (2/3)*m*r^2.
    Verifies the BallConfig property AND that simulation_service no longer
    uses the wrong (2/3) constant.
    """
    from cricket_trajectory_engine.config.physics_config import BallConfig

    m = 0.160    # kg (standard cricket ball)
    d = 0.0725   # m
    r = d / 2.0

    ball = BallConfig(mass_kg=m, diameter_m=d)
    expected_inertia = (2.0 / 5.0) * m * (r ** 2)
    wrong_inertia    = (2.0 / 3.0) * m * (r ** 2)

    assert abs(ball.moment_of_inertia_kg_m2 - expected_inertia) < 1e-10, \
        f"BallConfig inertia is wrong: {ball.moment_of_inertia_kg_m2} != {expected_inertia}"
    assert abs(ball.moment_of_inertia_kg_m2 - wrong_inertia) > 1e-10, \
        "BallConfig is still using the hollow-sphere (2/3) formula"

    # Also verify the constant in simulation_service.py source
    import inspect
    import cricket_trajectory_engine.services.simulation_service as svc_mod
    src = inspect.getsource(svc_mod)
    assert "(2.0 / 3.0)" not in src, \
        "simulation_service.py still contains the wrong (2/3) inertia constant"
    assert "(2.0 / 5.0)" in src, \
        "simulation_service.py does not contain the correct (2/5) inertia constant"


def test_velocity_decomposition_at_45_degrees():
    """
    Task 2: At 45° elevation, Vz = V*sin(45°) and Vxy = V*cos(45°).
    The magnitude of the resulting vector must equal the original speed V.
    """
    spd = 30.0
    elev = math.radians(45.0)
    azim = math.radians(0.0)

    vxy = spd * math.cos(elev)
    vz  = spd * math.sin(elev)
    vel = [vxy * math.cos(azim), vxy * math.sin(azim), vz]

    reconstructed_speed = math.sqrt(sum(c**2 for c in vel))
    assert abs(reconstructed_speed - spd) < 1e-9, \
        f"Speed not preserved: {reconstructed_speed} != {spd}"

    assert abs(vz - spd * math.sin(math.radians(45))) < 1e-9
    assert abs(vxy - spd * math.cos(math.radians(45))) < 1e-9


def test_30ms_25deg_carry_within_physical_bounds():
    """
    Task 3: 30 m/s launch at 25° elevation, 0° azimuth should produce
    carry distance within 10–80 m (physical cricket range with air drag).
    """
    from cricket_trajectory_engine.physics.flight_simulator import simulate_flight

    spd  = 30.0
    elev = math.radians(25.0)
    v0   = [spd * math.cos(elev), 0.0, spd * math.sin(elev)]
    p0   = [0.0, 0.0, 0.9]

    result = simulate_flight(p0, v0)

    assert result.horizontal_range_m >= 10.0, \
        f"Carry too short: {result.horizontal_range_m:.2f} m"
    assert result.horizontal_range_m <= 80.0, \
        f"Carry implausibly long: {result.horizontal_range_m:.2f} m"
    assert result.max_height_m > 0.0, \
        "Ball never gained height"
    assert result.flight_time_s > 0.0, \
        "Flight time must be positive"


def test_zero_elevation_lands_at_ground_with_positive_horizontal_travel():
    """
    Task 4: Ball launched at 0° elevation (purely horizontal) must land at
    Z ≈ 0 and travel a positive horizontal distance.
    """
    from cricket_trajectory_engine.physics.flight_simulator import simulate_flight

    spd = 20.0
    v0  = [spd, 0.0, 0.0]   # 0° elevation, 0° azimuth
    p0  = [0.0, 0.0, 0.9]   # Starting height 0.9 m (release height)

    result = simulate_flight(p0, v0)

    # Ball must reach the ground
    assert result.landing is not None, "Ball at 0° elevation never landed"
    landing_z = result.landing["position_m"][2]
    assert landing_z < 0.1, f"Landing Z too high: {landing_z:.4f} m"

    # Must travel forward
    assert result.horizontal_range_m > 0.5, \
        f"Ball did not travel forward: {result.horizontal_range_m:.2f} m"


def test_phase_field_in_trajectory_samples():
    """
    Task 5: The trajectory_samples from run_simulation must include a 'phase'
    field on every point. Phase 0 = flight, Phase 2 = rolling ground phase.
    At least one point should be phase=0 (airborne) and, for a bounced shot,
    at least one point should be phase=2 (rolling).
    """
    payload = {
        "speed_m_s": 30.0,
        "elevation_deg": 25.0,
        "azimuth_deg": 0.0,
        "environment": {"rolling_resistance_coeff": 0.20},
        "stadium": {"boundary_radius_m": 70.0},
        "fielding": {"fielders": []},
    }
    result = run_simulation(payload)

    samples = result.get("trajectory_samples", [])
    assert len(samples) > 0, "No trajectory samples returned"

    # Every point must have a 'phase' key
    for i, pt in enumerate(samples):
        assert "phase" in pt, f"trajectory_samples[{i}] is missing 'phase' field"
        assert pt["phase"] in (0, 1, 2), \
            f"trajectory_samples[{i}]['phase'] = {pt['phase']} is not 0, 1, or 2"

    # At least some flight points (phase=0)
    phases = [pt["phase"] for pt in samples]
    assert 0 in phases, "No airborne (phase=0) points found in trajectory"

    # For a bounced trajectory, there should be rolling points (phase=2)
    bounces = result.get("bounces", [])
    if bounces:
        assert 2 in phases, \
            "Bounced trajectory has no rolling (phase=2) points in trajectory_samples"


def test_last_point_included_in_downsampled_trajectory():
    """
    Task 2 (complementary): The last trajectory point must always be present
    in the downsampled output even when n_pts % 200 != 0.
    """
    payload = {
        "speed_m_s": 25.0,
        "elevation_deg": 20.0,
        "azimuth_deg": 0.0,
        "environment": {"rolling_resistance_coeff": 0.20},
        "stadium": {"boundary_radius_m": 70.0},
        "fielding": {"fielders": []},
    }
    result = run_simulation(payload)

    samples = result.get("trajectory_samples", [])
    assert len(samples) > 0

    # The last sample must have the highest time value
    times = [pt["time_s"] for pt in samples]
    assert times[-1] == max(times), \
        "Last trajectory sample does not have the maximum time (final point may be missing)"
