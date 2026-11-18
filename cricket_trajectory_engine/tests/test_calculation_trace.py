"""
Unit tests for the Mathematical Explainability & Calculation Trace module.
Validates structured trace recording, LaTeX formulas, numerical substitutions,
and the dependency graph.
"""

import pytest
import numpy as np

from cricket_trajectory_engine.core.calculation_trace import (
    CalculationStep,
    CalculationTrace,
    get_default_dependency_graph,
)
from cricket_trajectory_engine.services.simulation_service import SimulationService
from cricket_trajectory_engine.models.experiment import ExperimentConfig


def test_calculation_trace_add_and_export():
    """Verify CalculationTrace adds steps correctly and serializes to dict/JSON."""
    trace = CalculationTrace()
    
    trace.add_step(
        step_id="step_reynolds_number",
        stage_name="Aerodynamics",
        formula_latex=r"Re = \frac{\rho \cdot v_{rel} \cdot D}{\mu}",
        formula_text="Re = (rho * v_rel * D) / mu",
        description="Computes Reynolds number for boundary layer flow.",
        inputs={"rho": 1.205, "v_rel": 30.0, "D": 0.072, "mu": 1.81e-5},
        substitution_text="Re = (1.205 * 30.0 * 0.072) / 1.81e-5",
        result_value=143890.0,
        result_formatted="1.44e+05",
        units="dimensionless",
        why_necessary="Determines whether flow is laminar, subcritical, or supercritical.",
        downstream_dependents=["step_drag_coefficient"],
    )

    assert len(trace.steps) == 1
    step = trace.steps[0]
    assert step.step_id == "step_reynolds_number"
    assert step.result_value == 143890.0
    assert "Re" in step.formula_latex

    serialized = trace.to_dict()
    assert "steps" in serialized
    assert len(serialized["steps"]) == 1
    assert serialized["steps"][0]["step_id"] == "step_reynolds_number"


def test_default_dependency_graph():
    """Verify the default dependency graph has all stages connected."""
    graph = get_default_dependency_graph()
    assert isinstance(graph, list)
    assert len(graph) >= 9

    node_ids = {n["id"] for n in graph}
    assert "input_coordinates" in node_ids
    assert "polynomial_fitting" in node_ids
    assert "launch_speed_angles" in node_ids
    assert "reynolds_number" in node_ids
    assert "aerodynamic_drag" in node_ids
    assert "equations_of_motion" in node_ids
    assert "ground_collision" in node_ids
    assert "rolling_deceleration" in node_ids
    assert "boundary_outcome" in node_ids

    for node in graph:
        assert "id" in node
        assert "label" in node
        assert "children" in node


def test_simulation_generates_complete_trace():
    """Verify that running a simulation populates all mathematical steps with live substituted values."""
    config = ExperimentConfig(
        name="Trace Verification Shot",
        pos0=[0.0, 0.0, 0.9],
        vel0=[28.0, 10.0, 6.2],
    )
    config.sync_velocity_and_angles()

    sim_service = SimulationService()
    res_obj, trace, res_multibounce, outcome = sim_service.run_simulation(config)

    assert res_obj is not None
    assert len(res_multibounce.time_s) > 10
    assert isinstance(trace, CalculationTrace)
    assert len(trace.steps) >= 8

    step_ids = [s.step_id for s in trace.steps]
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
    for exp_id in expected_steps:
        assert exp_id in step_ids, f"Missing expected calculation step {exp_id}"

    # Verify numerical substitution text contains numbers, not blank placeholders
    for step in trace.steps:
        assert step.substitution_text != "", f"Empty substitution for {step.step_id}"
        assert step.result_formatted != "", f"Empty result formatted for {step.step_id}"
        assert step.why_necessary != "", f"Missing physical rationale for {step.step_id}"
