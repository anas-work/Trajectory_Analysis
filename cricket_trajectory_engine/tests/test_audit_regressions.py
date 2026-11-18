"""
Regression & forensic audit test suite.
Validates:
1. Boundary Four distance clamping to rope radius (70m) vs unconstrained rollout.
2. Distinct physical inputs produce distinct trajectory arrays and fingerprints.
3. Pre-seeded real delivery experiments integrity.
4. Calculation trace step completeness and formula substitutions.
5. Unique cache-busting and persistence fidelity.
"""

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
