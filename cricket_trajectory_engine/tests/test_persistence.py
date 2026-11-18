"""
Unit tests for Experiment Persistence and Deterministic Caching.
Validates SHA-256 simulation fingerprinting, disk persistence structure,
and zero-latency cache hits.
"""

import os
import shutil
import tempfile
import pytest

from cricket_trajectory_engine.models.experiment import (
    ExperimentConfig,
    ExperimentRecord,
    compute_simulation_fingerprint,
)
from cricket_trajectory_engine.services.simulation_service import SimulationService
from cricket_trajectory_engine.services.experiment_service import ExperimentService


@pytest.fixture
def temp_exp_service():
    """Create a temporary experiment service directory for testing."""
    temp_dir = tempfile.mkdtemp()
    service = ExperimentService(base_dir=temp_dir)
    yield service
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_simulation_fingerprint_deterministic():
    """Verify that identical physical parameters yield identical SHA-256 fingerprints."""
    pos = [0.0, 0.0, 0.9]
    vel = [28.0, 10.0, 6.2]
    ball = {"mass_kg": 0.160, "diameter_m": 0.0725}
    env = {"air_density_kg_m3": 1.225, "gravity_m_s2": 9.80665}
    stadium = {"boundary_radius_m": 70.0}
    solver = {}

    fp1 = compute_simulation_fingerprint(pos, vel, ball, env, stadium, solver)
    fp2 = compute_simulation_fingerprint(pos, vel, ball, env, stadium, solver)
    
    # Changed velocity
    fp3 = compute_simulation_fingerprint(pos, [29.0, 10.0, 6.2], ball, env, stadium, solver)

    assert fp1 == fp2, "Fingerprints must match when physics parameters are identical"
    assert fp1 != fp3, "Fingerprints must differ when physics parameters differ"


def test_experiment_service_save_and_cache_hit(temp_exp_service):
    """Verify experiment execution, disk persistence, and instant cache hit on repeat run."""
    cfg = ExperimentConfig(
        pos0=[0.0, 0.0, 0.9],
        vel0=[28.0, 10.0, 6.2],
    )
    cfg.sync_velocity_and_angles()

    sim_service = SimulationService()
    res_obj, trace, res_multibounce, outcome = sim_service.run_simulation(cfg)

    record = ExperimentRecord(
        experiment_id="EXP_TEST_001",
        name=cfg.name,
        description="Testing persistence",
        created_at="2026-11-05T00:00:00",
        tags=["test"],
        config=cfg,
        results=res_obj,
        fingerprint=res_obj.fingerprint,
    )

    # 1. Save to disk
    saved_id = temp_exp_service.save_experiment(
        record=record,
        multi_bounce_res=res_multibounce,
        trace=trace,
    )
    assert saved_id == "EXP_TEST_001"

    # Check directory structure on disk
    exp_dir = os.path.join(temp_exp_service.base_dir, saved_id)
    assert os.path.isdir(exp_dir)
    assert os.path.isfile(os.path.join(exp_dir, "experiment.json"))
    assert os.path.isfile(os.path.join(exp_dir, "configuration.json"))
    assert os.path.isfile(os.path.join(exp_dir, "results.json"))
    assert os.path.isfile(os.path.join(exp_dir, "trajectory.csv"))
    assert os.path.isfile(os.path.join(exp_dir, "calculation_trace.json"))

    # 2. Check cache lookup
    cached_id = temp_exp_service.find_cached_experiment(res_obj.fingerprint)
    assert cached_id == saved_id


def test_experiment_service_crud(temp_exp_service):
    """Verify list, get, duplicate, and delete operations."""
    cfg = ExperimentConfig(pos0=[0.0, 0.0, 0.9], vel0=[25.0, 12.0, 5.0])
    cfg.sync_velocity_and_angles()

    sim_service = SimulationService()
    res_obj, trace, res_multibounce, outcome = sim_service.run_simulation(cfg)

    record = ExperimentRecord(
        experiment_id="EXP_CRUD_001",
        name="CRUD Shot",
        description="CRUD testing",
        created_at="2026-11-05T00:00:00",
        tags=["crud"],
        config=cfg,
        results=res_obj,
        fingerprint=res_obj.fingerprint,
    )

    temp_exp_service.save_experiment(record, res_multibounce, trace)

    # List
    exp_list = temp_exp_service.list_experiments()
    assert len(exp_list) == 1
    assert exp_list[0]["id"] == "EXP_CRUD_001"

    # Get
    fetched = temp_exp_service.get_experiment("EXP_CRUD_001")
    assert fetched is not None
    assert fetched["id"] == "EXP_CRUD_001"

    # Duplicate
    dup = temp_exp_service.duplicate_experiment("EXP_CRUD_001", new_name="Duplicated Shot")
    assert dup is not None
    assert dup.experiment_id != "EXP_CRUD_001"
    assert dup.name == "Duplicated Shot"
    assert len(temp_exp_service.list_experiments()) == 2

    # Delete
    deleted = temp_exp_service.delete_experiment("EXP_CRUD_001")
    assert deleted is True
    assert temp_exp_service.get_experiment("EXP_CRUD_001") is None
    assert len(temp_exp_service.list_experiments()) == 1


def test_seeded_deliveries_prioritized_in_listing(temp_exp_service):
    """Verify that seeded delivery records appear first in natural ascending order over custom experiments."""
    cfg = ExperimentConfig(pos0=[0.0, 0.0, 0.9], vel0=[25.0, 12.0, 5.0])
    sim_service = SimulationService()
    res_obj, trace, res_multibounce, outcome = sim_service.run_simulation(cfg)

    # Save a custom experiment that alphabetically precedes DELIVERY (e.g. EXP_...)
    rec_custom = ExperimentRecord(
        experiment_id="EXP_20261106_120000",
        name="Custom Shot",
        description="A custom experiment",
        created_at="2026-11-06T12:00:00",
        tags=["user_simulation"],
        config=cfg,
        results=res_obj,
        fingerprint="fp_custom",
    )
    temp_exp_service.save_experiment(rec_custom, res_multibounce, trace)

    # Save two delivery experiments: DELIVERY_02_CAM1 and DELIVERY_01_CAM1
    rec_d2 = ExperimentRecord(
        experiment_id="DELIVERY_02_CAM1",
        name="Delivery 02 (CAM1)",
        description="Seeded match delivery 2",
        created_at="2026-11-05T14:30:00",
        tags=["real_delivery"],
        config=cfg,
        results=res_obj,
        fingerprint="fp_d2",
    )
    temp_exp_service.save_experiment(rec_d2, res_multibounce, trace)

    rec_d1 = ExperimentRecord(
        experiment_id="DELIVERY_01_CAM1",
        name="Delivery 01 (CAM1)",
        description="Seeded match delivery 1",
        created_at="2026-11-05T14:30:00",
        tags=["real_delivery"],
        config=cfg,
        results=res_obj,
        fingerprint="fp_d1",
    )
    temp_exp_service.save_experiment(rec_d1, res_multibounce, trace)

    items = temp_exp_service.list_experiments()
    assert len(items) == 3
    # Deliveries must appear first in natural order
    assert items[0]["id"] == "DELIVERY_01_CAM1"
    assert items[0]["is_seeded_delivery"] is True
    assert items[1]["id"] == "DELIVERY_02_CAM1"
    assert items[1]["is_seeded_delivery"] is True
    # Custom experiment appears after deliveries
    assert items[2]["id"] == "EXP_20261106_120000"
    assert items[2]["is_seeded_delivery"] is False
