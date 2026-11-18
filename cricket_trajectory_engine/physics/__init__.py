"""Physics package for 3D cricket ball trajectory simulation."""

# Import constants first:
from cricket_trajectory_engine.physics.constants import (
    DEFAULT_BALL_MASS_KG,
    DEFAULT_BALL_DIAMETER_M,
    DEFAULT_AIR_DENSITY_KG_M3,
    STANDARD_GRAVITY_M_S2,
    DEFAULT_DRAG_COEFFICIENT_CD,
)

def __getattr__(name: str):
    """Lazy imports to prevent circular dependencies during module initialization."""
    if name in (
        "compute_gravity_acceleration",
        "compute_drag_force",
        "compute_reynolds_number",
        "compute_relative_velocity",
        "evaluate_drag_coefficient",
        "compute_magnus_force",
        "compute_spin_parameter",
        "evaluate_lift_coefficient",
        "compute_total_acceleration",
        "compute_aerodynamic_breakdown",
        "compute_seam_force",
        "simulate_flight",
        "TrajectoryResult",
        "simulate_multi_bounce",
        "resolve_ground_impact",
        "MultiBounceResult",
        "BounceEvent",
    ):
        from cricket_trajectory_engine.physics import (
            gravity,
            drag,
            magnus,
            aerodynamics,
            flight_simulator,
            ground_collision,
        )
        mapping = {
            "compute_gravity_acceleration": gravity.compute_gravity_acceleration,
            "compute_drag_force": drag.compute_drag_force,
            "compute_reynolds_number": drag.compute_reynolds_number,
            "compute_relative_velocity": drag.compute_relative_velocity,
            "evaluate_drag_coefficient": drag.evaluate_drag_coefficient,
            "compute_magnus_force": magnus.compute_magnus_force,
            "compute_spin_parameter": magnus.compute_spin_parameter,
            "evaluate_lift_coefficient": magnus.evaluate_lift_coefficient,
            "compute_total_acceleration": aerodynamics.compute_total_acceleration,
            "compute_aerodynamic_breakdown": aerodynamics.compute_aerodynamic_breakdown,
            "compute_seam_force": aerodynamics.compute_seam_force,
            "simulate_flight": flight_simulator.simulate_flight,
            "TrajectoryResult": flight_simulator.TrajectoryResult,
            "simulate_multi_bounce": ground_collision.simulate_multi_bounce,
            "resolve_ground_impact": ground_collision.resolve_ground_impact,
            "MultiBounceResult": ground_collision.MultiBounceResult,
            "BounceEvent": ground_collision.BounceEvent,
        }
        return mapping[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "DEFAULT_BALL_MASS_KG",
    "DEFAULT_BALL_DIAMETER_M",
    "DEFAULT_AIR_DENSITY_KG_M3",
    "STANDARD_GRAVITY_M_S2",
    "DEFAULT_DRAG_COEFFICIENT_CD",
    "compute_gravity_acceleration",
    "compute_drag_force",
    "compute_reynolds_number",
    "compute_relative_velocity",
    "evaluate_drag_coefficient",
    "compute_magnus_force",
    "compute_spin_parameter",
    "evaluate_lift_coefficient",
    "compute_total_acceleration",
    "compute_aerodynamic_breakdown",
    "compute_seam_force",
    "simulate_flight",
    "TrajectoryResult",
    "simulate_multi_bounce",
    "resolve_ground_impact",
    "MultiBounceResult",
    "BounceEvent",
]
