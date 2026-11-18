"""
Comparison REST API: Multi-experiment comparative metrics and accuracy.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from cricket_trajectory_engine.services.experiment_service import ExperimentService
from cricket_trajectory_engine.services.comparison_service import ComparisonService

router = APIRouter(prefix="/api/comparison", tags=["comparison"])
exp_service = ExperimentService()
comp_service = ComparisonService()


@router.post("")
def compare_experiments(payload: Dict[str, Any]):
    """Compares list of experiment IDs side-by-side."""
    exp_ids = payload.get("experiment_ids", [])
    if len(exp_ids) < 2:
        raise HTTPException(status_code=400, detail="Select at least 2 experiments to compare")

    experiments_data = []
    for eid in exp_ids:
        data = exp_service.get_experiment(eid)
        if data:
            experiments_data.append(data)

    if len(experiments_data) < 2:
        raise HTTPException(status_code=404, detail="Could not load specified experiments")

    return comp_service.compare_experiments(experiments_data)

