"""
Structured Mathematical Explainability Engine & Calculation Trace.

Captures every step of the physics pipeline:
- Formula (LaTeX and text)
- Conceptual explanation
- Input symbols and numerical values used
- Mathematical substitution string
- Calculated result and dimensional units
- Physical significance / why it is necessary
- Downstream dependent calculations
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import json


@dataclass
class CalculationStep:
    step_id: str
    stage_name: str
    formula_latex: str
    formula_text: str
    description: str
    inputs: Dict[str, Any]
    substitution_text: str
    result_value: Any
    result_formatted: str
    units: str
    why_necessary: str
    downstream_dependents: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CalculationTrace:
    """Holds the complete chronological calculation trace of a simulation."""
    steps: List[CalculationStep] = field(default_factory=list)
    stages: List[str] = field(default_factory=list)

    def add_step(
        self,
        step_id: str,
        stage_name: str,
        formula_latex: str,
        formula_text: str,
        description: str,
        inputs: Dict[str, Any],
        substitution_text: str,
        result_value: Any,
        result_formatted: str,
        units: str,
        why_necessary: str,
        downstream_dependents: Optional[List[str]] = None,
    ) -> CalculationStep:
        step = CalculationStep(
            step_id=step_id,
            stage_name=stage_name,
            formula_latex=formula_latex,
            formula_text=formula_text,
            description=description,
            inputs=inputs,
            substitution_text=substitution_text,
            result_value=result_value,
            result_formatted=result_formatted,
            units=units,
            why_necessary=why_necessary,
            downstream_dependents=downstream_dependents or [],
        )
        self.steps.append(step)
        if stage_name not in self.stages:
            self.stages.append(stage_name)
        return step

    def get_step(self, step_id: str) -> Optional[CalculationStep]:
        for s in self.steps:
            if s.step_id == step_id:
                return s
        return None

    def get_stage_steps(self, stage_name: str) -> List[CalculationStep]:
        return [s for s in self.steps if s.stage_name == stage_name]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stages": self.stages,
            "steps": [s.to_dict() for s in self.steps],
            "total_steps": len(self.steps),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def save_json(self, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)


def get_default_dependency_graph() -> List[Dict[str, Any]]:
    """Returns the visual dependency flow graph of the calculation pipeline."""
    return [
        {
            "id": "input_coordinates",
            "label": "1. 3D Coordinates / Input State",
            "description": "Camera stereo triangulation (X, Y, Z) or manual state configuration",
            "children": ["polynomial_fitting", "launch_speed_angles"]
        },
        {
            "id": "polynomial_fitting",
            "label": "2. Polynomial Velocity Estimation",
            "description": "Least-squares 2nd-order fit: p(t) = a0 + a1*t + a2*t^2 to smooth noise",
            "children": ["launch_speed_angles"]
        },
        {
            "id": "launch_speed_angles",
            "label": "3. Launch Speed & Angles",
            "description": "Speed v0 = sqrt(vx^2 + vy^2 + vz^2), Elevation theta, Azimuth phi",
            "children": ["reynolds_number", "equations_of_motion"]
        },
        {
            "id": "reynolds_number",
            "label": "4. Reynolds Number",
            "description": "Re = (rho * v_rel * D) / mu to evaluate aerodynamic regime",
            "children": ["aerodynamic_drag"]
        },
        {
            "id": "aerodynamic_drag",
            "label": "5. Aerodynamic Forces",
            "description": "F_drag = -0.5 * rho * Cd * A * |v_rel| * v_rel and Magnus lift",
            "children": ["equations_of_motion"]
        },
        {
            "id": "equations_of_motion",
            "label": "6. Equations of Motion (RK45)",
            "description": "d^2r/dt^2 = g + (F_drag + F_magnus)/m integrated with event detection Z(t) = R",
            "children": ["ground_collision", "apex_carry"]
        },
        {
            "id": "apex_carry",
            "label": "7. Apex & Flight Carry",
            "description": "Maximum altitude Z_max, apex timing t_apex, and carry distance d_1 to first bounce",
            "children": ["fielder_interception", "boundary_outcome"]
        },
        {
            "id": "ground_collision",
            "label": "8. Ground Collision & Spin Coupling",
            "description": "Normal restitution vz+ = -en * vz- and tangential friction torque Delta_omega",
            "children": ["rolling_deceleration"]
        },
        {
            "id": "rolling_deceleration",
            "label": "9. Outfield Grass Rolling",
            "description": "a_roll = -mu_roll * g, minimum speed required, and residual speed at rope",
            "children": ["boundary_outcome"]
        },
        {
            "id": "fielder_interception",
            "label": "10. Fielder Reachability",
            "description": "Sprinting distance D_f = v_max * (t - t_react) vs ball position and height",
            "children": ["boundary_outcome"]
        },
        {
            "id": "boundary_outcome",
            "label": "11. Cricket Match Outcome",
            "description": "Deterministic classification: Six, Four, Out (Catch), Single, Double, Dot",
            "children": []
        }
    ]

