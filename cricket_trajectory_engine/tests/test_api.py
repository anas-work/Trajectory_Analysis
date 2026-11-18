"""
Unit tests for FastAPI REST API endpoints.
Validates simulation execution, experiment retrieval, fielding validation, and comparisons.
"""

import pytest

from cricket_trajectory_engine.backend.api.simulation_api import run_simulation
from cricket_trajectory_engine.backend.api.experiments_api import (
    list_experiments,
    get_experiment,
    create_and_save_experiment,
    delete_experiment,
)
from cricket_trajectory_engine.backend.api.fielding_api import (
    get_presets,
    validate_fielding,
)
from cricket_trajectory_engine.backend.api.comparison_api import compare_experiments


def test_fielding_presets_api():
    """Verify listing available fielding presets via API."""
    data = get_presets()
    assert "presets" in data
    presets = data["presets"]
    assert "powerplay" in presets
    assert "attacking" in presets
    assert "middle_overs" in presets
    assert "death_overs" in presets
    for name, setup in presets.items():
        assert len(setup["fielders"]) == 11


def test_fielding_validate_api():
    """Verify fielding validation endpoint."""
    data = get_presets()
    req = {
        "fielders": data["presets"]["powerplay"]["fielders"],
        "format_rules": "t20_powerplay",
    }
    res = validate_fielding(req)
    assert res["valid"] is True
    assert len(res["warnings"]) == 0


def test_simulation_run_api():
    """Verify running a full simulation via the API endpoint."""
    req = {
        "pos0": [0.0, 0.0, 0.9],
        "vel0": [28.0, 10.0, 6.2],
        "ball": {"mass_kg": 0.160, "diameter_m": 0.0725},
    }
    res = run_simulation(req)

    assert res["status"] == "success"
    assert "fingerprint" in res
    assert "results" in res
    assert "trajectory_samples" in res
    assert "calculation_trace" in res

    metrics = res["results"]
    assert metrics["max_height_m"] > 0
    assert metrics["total_distance_m"] > 0
    assert "outcome_call" in metrics
    assert len(res["trajectory_samples"]) > 5
    assert len(res["calculation_trace"]["steps"]) >= 8

    # Clean up test artifact
    if "experiment_id" in res:
        delete_experiment(res["experiment_id"])


def test_comparison_api():
    """Verify multi-experiment comparison via API endpoint."""
    # First create two saved experiments
    req1 = {
        "name": "Comp Shot 1",
        "pos0": [0.0, 0.0, 0.9],
        "vel0": [24.0, 10.0, 5.0],
    }
    res1 = create_and_save_experiment(req1)

    req2 = {
        "name": "Comp Shot 2",
        "pos0": [0.0, 0.0, 0.9],
        "vel0": [32.0, 10.0, 8.0],
    }
    res2 = create_and_save_experiment(req2)

    id1 = res1["experiment_id"]
    id2 = res2["experiment_id"]

    comp_req = {
        "experiment_ids": [id1, id2],
    }
    comp_res = compare_experiments(comp_req)

    assert "total_compared" in comp_res
    assert comp_res["total_compared"] == 2
    assert "comparison_table" in comp_res
    assert "deltas_vs_baseline" in comp_res

    deltas = comp_res["deltas_vs_baseline"]
    assert len(deltas) == 2
    second_delta = deltas[1]
    assert second_delta["experiment_id"] == id2
    assert "delta_apex_m" in second_delta
    assert "delta_max_height_m" in second_delta
    assert "delta_total_dist_m" in second_delta
    assert "delta_horizontal_distance_m" in second_delta
    assert "baseline_outcome" in second_delta
    assert "comparison_outcome" in second_delta

    assert "deltas_map" in comp_res
    assert id2 in comp_res["deltas_map"]
    assert "experiments" in comp_res
    assert len(comp_res["experiments"]) == 2
    assert "trajectory" in comp_res["experiments"][0]

    # Clean up test experiments
    delete_experiment(id1)
    delete_experiment(id2)


def test_ground_truth_clip_in_seeded_deliveries():
    """Verify that seeded deliveries expose ground truth clips."""
    data = get_experiment("DELIVERY_01_CAM1")
    assert data["has_ground_truth_clip"] is True
    assert data["ground_truth_clip_url"] is not None
    assert "ground_truth_clip.mp4" in data["ground_truth_clip_url"]


@pytest.mark.anyio
async def test_upload_ground_truth_clip_api():
    """Verify uploading an optional ground truth clip for a simulation experiment."""
    from cricket_trajectory_engine.backend.api.experiments_api import upload_ground_truth_clip

    # Create a fresh experiment
    res = create_and_save_experiment({
        "name": "Test Upload Clip Shot",
        "pos0": [0.0, 0.0, 0.9],
        "vel0": [25.0, 5.0, 4.0],
    })
    exp_id = res["experiment_id"]

    class MockRequest:
        headers = {"content-type": "video/mp4"}
        async def stream(self):
            yield b"ftypisom\x00\x00\x00\x01mock video stream content"

    upload_res = await upload_ground_truth_clip(exp_id, MockRequest())
    assert upload_res["status"] == "clip_uploaded"
    assert "ground_truth_clip_url" in upload_res

    # Retrieve experiment again to verify persistence
    exp_data = get_experiment(exp_id)
    assert exp_data["has_ground_truth_clip"] is True
    assert exp_data["ground_truth_clip_url"] is not None
    assert exp_id in exp_data["ground_truth_clip_url"]

    # Clean up test experiment
    delete_experiment(exp_id)


def test_delete_experiment_api():
    """Verify deleting an experiment via the DELETE endpoint and error handling."""
    from fastapi import HTTPException

    # Create a transient test experiment
    res = create_and_save_experiment({
        "name": "Transient Delete Test Experiment",
        "pos0": [0.0, 0.0, 0.9],
        "vel0": [22.0, 4.0, 5.0],
    })
    exp_id = res["experiment_id"]

    # Verify it exists
    data = get_experiment(exp_id)
    assert data["experiment_id"] == exp_id

    # Delete via API
    del_res = delete_experiment(exp_id)
    assert del_res["status"] == "deleted"
    assert del_res["experiment_id"] == exp_id

    # Subsequent get should raise HTTPException 404
    with pytest.raises(HTTPException) as exc_info:
        get_experiment(exp_id)
    assert exc_info.value.status_code == 404

    # Subsequent delete should raise HTTPException 404
    with pytest.raises(HTTPException) as exc_info:
        delete_experiment(exp_id)
    assert exc_info.value.status_code == 404

