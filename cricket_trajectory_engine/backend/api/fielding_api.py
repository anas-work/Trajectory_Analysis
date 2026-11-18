"""
Fielding REST API: Preset retrieval and format rule validation.
"""

from fastapi import APIRouter
from typing import Dict, Any, List

from cricket_trajectory_engine.models.fielder import (
    FieldingSetupModel,
    FIELDING_PRESETS,
    FielderModel,
)

router = APIRouter(prefix="/api/fielding", tags=["fielding"])


@router.get("/presets")
def get_presets():
    """Returns tactical fielding presets (Powerplay, Attacking, Middle, Death) and descriptions."""
    return {
        "presets": FIELDING_PRESETS,
        "available_formats": [
            {"id": "t20_powerplay", "name": "T20 Powerplay (Overs 1-6)", "max_outside_circle": 2},
            {"id": "t20", "name": "T20 Non-Powerplay (Overs 7-20)", "max_outside_circle": 5},
            {"id": "odi_p1", "name": "ODI Powerplay 1 (Overs 1-10)", "max_outside_circle": 2},
            {"id": "odi_p2", "name": "ODI Powerplay 2 (Overs 11-40)", "max_outside_circle": 4},
            {"id": "odi_p3", "name": "ODI Powerplay 3 (Overs 41-50)", "max_outside_circle": 5},
            {"id": "test", "name": "Test Cricket", "max_outside_circle": 9},
            {"id": "custom", "name": "Custom / Unrestricted", "max_outside_circle": 9},
        ]
    }


@router.post("/validate")
def validate_fielding(payload: Dict[str, Any]):
    """Validates 11-player count, circle restrictions, and leg-side fielders."""
    fielders_raw = payload.get("fielders", [])
    format_rules = payload.get("format_rules", "t20")

    f_list = [
        FielderModel(
            id=f.get("id", f"f_{i}"),
            name=f.get("name", "Fielder"),
            role=f.get("role", "fielder"),
            x_m=float(f.get("x", f.get("x_m", 0.0))),
            y_m=float(f.get("y", f.get("y_m", 0.0))),
        )
        for i, f in enumerate(fielders_raw)
    ]

    setup = FieldingSetupModel(fielders=f_list, format_rules=format_rules)
    warnings = setup.validate_rules()

    return {
        "valid": len(warnings) == 0,
        "total_fielders": len(f_list),
        "warnings": warnings,
        "outside_circle_count": sum(1 for f in f_list if not f.is_inside_circle()),
    }

