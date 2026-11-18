"""
Cricket outcome evaluation engine.

Strictly adheres to scientific demarcation:
1. Physics-derived results (trajectory, apex, flight time, landing speed).
2. Geometry-derived results (boundary crossing, Six, Four).
3. Conditional player-dependent outcomes (Catch, Single, Double, Dot),
   explicitly flagging missing player tracking data when absent.
4. Rigorous post-bounce boundary rope clearance modeling (Boundary 4 vs Pulled Up Short).
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np

from cricket_trajectory_engine.config.physics_config import FieldConfig
from cricket_trajectory_engine.physics.flight_simulator import TrajectoryResult
from cricket_trajectory_engine.physics.ground_collision import MultiBounceResult
from cricket_trajectory_engine.prediction.field_geometry import CricketField, BoundaryIntersection


@dataclass
class FielderPosition:
    """Configurable fielder position and athletic parameters."""
    fielder_id: str
    role_name: str
    x_m: float
    y_m: float
    max_sprint_speed_m_s: float = 7.0   # Elite cricket fielder max sprint speed (6.5 - 8.0 m/s)
    reaction_time_s: float = 0.35       # Visual-motor reaction time (0.25 - 0.45 s)
    reach_radius_m: float = 1.8         # Arm reach and diving radius (1.5 - 2.2 m)
    min_catch_height_m: float = 0.25    # Shoestring catch limit (m)
    max_catch_height_m: float = 2.30    # Jumping overhead reach limit (m)


@dataclass
class CatchEvaluation:
    """Detailed evaluation of whether a fielder could intercept the ball for a catch."""
    fielder_id: str
    role_name: str
    can_intercept_for_catch: bool
    earliest_intercept_time_s: Optional[float]
    intercept_position_m: Optional[np.ndarray]
    required_sprint_speed_m_s: Optional[float]
    margin_distance_m: Optional[float]


@dataclass
class GroundFieldingEvaluation:
    """Detailed evaluation of whether a fielder can field or cut off the ball along the turf."""
    fielder_id: str
    role_name: str
    can_intercept: bool
    earliest_intercept_time_s: Optional[float]
    intercept_position_m: Optional[np.ndarray]
    required_sprint_speed_m_s: Optional[float]
    distance_from_pitch_m: float


@dataclass
class RopeClearanceAnalysis:
    """Detailed kinematic modeling of whether a ball clears or falls short of the boundary rope post-bounce."""
    first_impact_distance_m: float
    boundary_rope_distance_m: float
    distance_remaining_to_rope_m: float
    post_bounce_distance_travelled_m: float
    clears_rope: bool
    residual_speed_at_rope_m_s: Optional[float]
    rope_crossing_time_s: Optional[float]
    rope_crossing_position_m: Optional[np.ndarray]
    margin_m: float  # Positive = cleared rope by this much; Negative = pulled up short by this much
    minimum_speed_required_m_s: float
    summary: str
    unconstrained_rollout_distance_m: float = 0.0


@dataclass
class CricketOutcome:
    """Complete, structured outcome report."""
    primary_call: str  # "SIX", "FOUR", "POTENTIAL_CATCH", "IN_PLAY_RUNS_EVALUATED", "IN_PLAY_FIELDER_DATA_REQUIRED"
    physics_facts: Dict[str, Any]
    geometry_facts: Dict[str, Any]
    rope_clearance: RopeClearanceAnalysis
    fielder_evaluations: List[CatchEvaluation]
    estimated_runs: Optional[int]
    player_data_missing: bool
    scientific_notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_call": self.primary_call,
            "physics_facts": self.physics_facts,
            "geometry_facts": self.geometry_facts,
            "rope_clearance": {
                "first_impact_distance_m": self.rope_clearance.first_impact_distance_m,
                "boundary_rope_distance_m": self.rope_clearance.boundary_rope_distance_m,
                "distance_remaining_to_rope_m": self.rope_clearance.distance_remaining_to_rope_m,
                "post_bounce_distance_travelled_m": self.rope_clearance.post_bounce_distance_travelled_m,
                "clears_rope": self.rope_clearance.clears_rope,
                "residual_speed_at_rope_m_s": self.rope_clearance.residual_speed_at_rope_m_s,
                "rope_crossing_time_s": self.rope_clearance.rope_crossing_time_s,
                "rope_crossing_position_m": (
                    self.rope_clearance.rope_crossing_position_m.tolist()
                    if self.rope_clearance.rope_crossing_position_m is not None
                    else None
                ),
                "margin_m": self.rope_clearance.margin_m,
                "minimum_speed_required_m_s": self.rope_clearance.minimum_speed_required_m_s,
                "unconstrained_rollout_distance_m": self.rope_clearance.unconstrained_rollout_distance_m,
                "summary": self.rope_clearance.summary,
            },
            "fielder_evaluations": [
                {
                    "fielder_id": f.fielder_id,
                    "role_name": f.role_name,
                    "can_intercept_for_catch": f.can_intercept_for_catch,
                    "earliest_intercept_time_s": f.earliest_intercept_time_s,
                    "intercept_position_m": (
                        f.intercept_position_m.tolist() if f.intercept_position_m is not None else None
                    ),
                    "required_sprint_speed_m_s": f.required_sprint_speed_m_s,
                    "margin_distance_m": f.margin_distance_m,
                }
                for f in self.fielder_evaluations
            ],
            "estimated_runs": self.estimated_runs,
            "player_data_missing": self.player_data_missing,
            "scientific_notes": self.scientific_notes,
        }


def analyze_rope_clearance(
    multi_bounce_result: MultiBounceResult,
    field: CricketField,
) -> RopeClearanceAnalysis:
    """
    Computes exact kinematic analytics for whether a ball pitching inside clears the rope for Four
    or decelerates and pulls up short of the rope.
    """
    first_b = multi_bounce_result.first_bounce
    pos_impact = first_b.position_m if first_b else multi_bounce_result.positions_m[0]
    d_impact = float(np.hypot(pos_impact[0], pos_impact[1]))
    azimuth = float(np.arctan2(pos_impact[1], pos_impact[0]))
    r_rope = field.boundary_radius_at_azimuth(azimuth)

    d_remaining = max(0.0, r_rope - d_impact)
    total_dist = multi_bounce_result.total_horizontal_distance_m
    post_dist = max(0.0, total_dist - d_impact)

    # Effective turf rolling resistance deceleration a_roll = mu_roll * g (0.20 * 9.81 ~ 1.96 m/s^2)
    # Minimum speed required after first bounce to cover d_remaining: v = sqrt(2 * a * d)
    a_roll = 0.20 * 9.80665
    v_req_min = float(np.sqrt(2.0 * a_roll * d_remaining)) if d_remaining > 0 else 0.0

    crossing = field.find_boundary_crossing(
        multi_bounce_result.time_s,
        multi_bounce_result.positions_m,
        first_bounce_time_s=first_b.time_s if first_b else 0.0,
    )

    if crossing.intersects and not crossing.crossed_on_full:
        # Ball cleared the rope after bouncing:
        t_cross = crossing.intersection_time_s
        # Interpolate speed at crossing time:
        idx = np.searchsorted(multi_bounce_result.time_s, t_cross)
        idx = min(idx, len(multi_bounce_result.velocities_m_s) - 1)
        v_at_rope = float(np.linalg.norm(multi_bounce_result.velocities_m_s[idx]))

        margin = total_dist - r_rope
        summary = (
            f"CLEARED ROPE (BOUNDARY FOUR): Pitched {d_impact:.1f}m ({d_remaining:.1f}m inside rope). "
            f"Crossed boundary rope ({r_rope:.1f}m) at t={t_cross:.2f}s with residual speed {v_at_rope:.1f} m/s ({v_at_rope*3.6:.1f} km/h). "
            f"Official match distance: {r_rope:.1f}m (Theoretical uninhibited rollout: {total_dist:.1f}m)."
        )
        return RopeClearanceAnalysis(
            first_impact_distance_m=d_impact,
            boundary_rope_distance_m=r_rope,
            distance_remaining_to_rope_m=d_remaining,
            post_bounce_distance_travelled_m=post_dist,
            clears_rope=True,
            residual_speed_at_rope_m_s=v_at_rope,
            rope_crossing_time_s=t_cross,
            rope_crossing_position_m=crossing.intersection_point_m,
            margin_m=margin,
            minimum_speed_required_m_s=v_req_min,
            summary=summary,
            unconstrained_rollout_distance_m=total_dist,
        )

    elif crossing.intersects and crossing.crossed_on_full:
        # Six on full:
        summary = f"CLEARED ROPE ON FULL (SIX): Carried {d_impact:.1f}m past the {r_rope:.1f}m rope without pitching."
        return RopeClearanceAnalysis(
            first_impact_distance_m=d_impact,
            boundary_rope_distance_m=r_rope,
            distance_remaining_to_rope_m=0.0,
            post_bounce_distance_travelled_m=0.0,
            clears_rope=True,
            residual_speed_at_rope_m_s=crossing.height_at_crossing_m,
            rope_crossing_time_s=crossing.intersection_time_s,
            rope_crossing_position_m=crossing.intersection_point_m,
            margin_m=d_impact - r_rope,
            minimum_speed_required_m_s=0.0,
            summary=summary,
            unconstrained_rollout_distance_m=total_dist,
        )

    else:
        # Pulled up short:
        d_final = float(np.hypot(multi_bounce_result.final_stopping_position_m[0],
                                 multi_bounce_result.final_stopping_position_m[1]))
        shortfall = max(0.0, r_rope - d_final)
        summary = (
            f"PULLED UP SHORT (IN-PLAY): Pitched {d_impact:.1f}m ({d_remaining:.1f}m inside rope). "
            f"Travelled {post_dist:.1f}m post-bounce and came to a stop at {d_final:.1f}m, "
            f"{shortfall:.1f}m short of the boundary rope."
        )
        return RopeClearanceAnalysis(
            first_impact_distance_m=d_impact,
            boundary_rope_distance_m=r_rope,
            distance_remaining_to_rope_m=d_remaining,
            post_bounce_distance_travelled_m=post_dist,
            clears_rope=False,
            residual_speed_at_rope_m_s=0.0,
            rope_crossing_time_s=None,
            rope_crossing_position_m=None,
            margin_m=-shortfall,
            minimum_speed_required_m_s=v_req_min,
            summary=summary,
            unconstrained_rollout_distance_m=total_dist,
        )


def evaluate_fielders_for_catch(
    times_s: np.ndarray,
    positions_m: np.ndarray,
    first_bounce_time_s: Optional[float],
    fielders: List[FielderPosition],
) -> List[CatchEvaluation]:
    """
    Evaluates kinematic reachability for each fielder prior to first ground contact.
    """
    evaluations: List[CatchEvaluation] = []
    
    # Restrict to airborne phase before first bounce:
    valid_mask = np.ones(len(times_s), dtype=bool)
    if first_bounce_time_s is not None:
        valid_mask = times_s <= (first_bounce_time_s + 1e-4)

    air_times = times_s[valid_mask]
    air_positions = positions_m[valid_mask]

    for fielder in fielders:
        can_catch = False
        earliest_time = None
        best_pos = None
        min_req_speed = None
        max_margin = -float("inf")

        fx, fy = fielder.x_m, fielder.y_m

        for t, p in zip(air_times, air_positions):
            z = p[2]
            if not (fielder.min_catch_height_m <= z <= fielder.max_catch_height_m):
                continue

            available_time = t - fielder.reaction_time_s
            if available_time <= 0.05:
                continue

            dist_to_ball = float(np.hypot(p[0] - fx, p[1] - fy))
            max_reachable_dist = fielder.max_sprint_speed_m_s * available_time + fielder.reach_radius_m

            margin = max_reachable_dist - dist_to_ball
            req_speed = max(0.0, (dist_to_ball - fielder.reach_radius_m) / available_time)

            if margin >= 0:
                can_catch = True
                earliest_time = float(t)
                best_pos = p
                min_req_speed = float(req_speed)
                max_margin = float(margin)
                break
            else:
                if margin > max_margin:
                    max_margin = float(margin)
                    min_req_speed = float(req_speed)

        evaluations.append(CatchEvaluation(
            fielder_id=fielder.fielder_id,
            role_name=fielder.role_name,
            can_intercept_for_catch=can_catch,
            earliest_intercept_time_s=earliest_time,
            intercept_position_m=best_pos,
            required_sprint_speed_m_s=min_req_speed,
            margin_distance_m=max_margin if max_margin != -float("inf") else None,
        ))

    return evaluations


def evaluate_fielders_for_ground_stop(
    times_s: np.ndarray,
    positions_m: np.ndarray,
    fielders: List[FielderPosition],
    max_time_s: Optional[float] = None,
) -> Optional[GroundFieldingEvaluation]:
    """
    Evaluates whether any fielder can field/stop the ball along the turf (post-bounce or ground rolling)
    before it crosses the boundary rope or comes to rest.
    """
    best_stop: Optional[GroundFieldingEvaluation] = None

    for fielder in fielders:
        fx, fy = fielder.x_m, fielder.y_m
        for t, p in zip(times_s, positions_m):
            if max_time_s is not None and t >= max_time_s:
                break

            available_time = t - fielder.reaction_time_s
            if available_time <= 0.05:
                continue

            z = p[2]
            # Fielder can field ball on ground or low bounce up to overhead standing reach
            if z > fielder.max_catch_height_m:
                continue

            dist_to_ball = float(np.hypot(p[0] - fx, p[1] - fy))
            max_reachable_dist = fielder.max_sprint_speed_m_s * available_time + fielder.reach_radius_m

            if dist_to_ball <= max_reachable_dist:
                req_speed = max(0.0, (dist_to_ball - fielder.reach_radius_m) / available_time)
                r_stop = float(np.hypot(p[0], p[1]))
                candidate = GroundFieldingEvaluation(
                    fielder_id=fielder.fielder_id,
                    role_name=fielder.role_name,
                    can_intercept=True,
                    earliest_intercept_time_s=float(t),
                    intercept_position_m=p,
                    required_sprint_speed_m_s=float(req_speed),
                    distance_from_pitch_m=r_stop,
                )
                if best_stop is None or candidate.earliest_intercept_time_s < best_stop.earliest_intercept_time_s:
                    best_stop = candidate
                break

    return best_stop


def evaluate_outcome(
    multi_bounce_result: MultiBounceResult,
    field_config: Optional[FieldConfig] = None,
    fielders: Optional[List[FielderPosition]] = None,
) -> CricketOutcome:
    """
    Evaluates cricket match outcome for a simulated ball trajectory.
    """
    field = CricketField(field_config)
    notes: List[str] = []

    # 1. Physics facts:
    first_b = multi_bounce_result.first_bounce
    first_bounce_pos = first_b.position_m if first_b else multi_bounce_result.positions_m[-1]
    first_bounce_time = first_b.time_s if first_b else multi_bounce_result.final_stopping_time_s
    first_bounce_dist = float(np.hypot(first_bounce_pos[0], first_bounce_pos[1]))
    max_height = float(np.max(multi_bounce_result.positions_m[:, 2]))
    total_dist = multi_bounce_result.total_horizontal_distance_m

    physics_facts = {
        "flight_time_to_first_impact_s": first_bounce_time,
        "first_impact_position_m": first_bounce_pos.tolist(),
        "first_impact_distance_m": first_bounce_dist,
        "first_impact_speed_m_s": first_b.pre_speed_m_s if first_b else 0.0,
        "total_horizontal_distance_m": total_dist,
        "max_height_apex_m": max_height,
        "number_of_bounces": len(multi_bounce_result.bounces),
        "final_stopping_position_m": multi_bounce_result.final_stopping_position_m.tolist(),
        "total_duration_s": multi_bounce_result.final_stopping_time_s,
    }

    # 2. Geometry facts & Boundary Crossing:
    crossing = field.find_boundary_crossing(
        multi_bounce_result.time_s,
        multi_bounce_result.positions_m,
        first_bounce_time_s=first_bounce_time,
    )
    first_impact_inside = field.is_inside_boundary(first_bounce_pos[0], first_bounce_pos[1])

    geometry_facts = {
        "first_impact_inside_boundary": first_impact_inside,
        "crossed_boundary": crossing.intersects,
        "crossed_boundary_on_full": crossing.crossed_on_full,
        "crossing_time_s": crossing.intersection_time_s,
        "crossing_position_m": (
            crossing.intersection_point_m.tolist() if crossing.intersection_point_m is not None else None
        ),
        "crossing_height_m": crossing.height_at_crossing_m,
    }

    # 3. Post-Bounce Rope Clearance Analysis:
    rope_analysis = analyze_rope_clearance(multi_bounce_result, field)

    # 4. Fielder / Catch and Ground Cutoff evaluations:
    fielder_evals: List[CatchEvaluation] = []
    ground_stop: Optional[GroundFieldingEvaluation] = None
    player_data_missing = (fielders is None or len(fielders) == 0)

    crossing_time = crossing.intersection_time_s if (crossing.intersects and crossing.intersection_time_s is not None) else float("inf")

    if not player_data_missing and fielders is not None:
        fielder_evals = evaluate_fielders_for_catch(
            multi_bounce_result.time_s,
            multi_bounce_result.positions_m,
            first_bounce_time_s=first_bounce_time,
            fielders=fielders,
        )
        ground_stop = evaluate_fielders_for_ground_stop(
            multi_bounce_result.time_s,
            multi_bounce_result.positions_m,
            fielders=fielders,
            max_time_s=crossing_time,
        )

    # 5. Determine Primary Cricket Call:
    has_catch = not player_data_missing and any(fe.can_intercept_for_catch for fe in fielder_evals)
    earliest_catch_time = None
    if has_catch:
        catch_times = [
            fe.earliest_intercept_time_s
            for fe in fielder_evals
            if fe.can_intercept_for_catch and fe.earliest_intercept_time_s is not None
        ]
        if catch_times:
            earliest_catch_time = min(catch_times)

    # 1. Aerial catch in the field of play before crossing boundary or hitting ground:
    if has_catch and earliest_catch_time is not None and earliest_catch_time <= crossing_time:
        primary_call = "POTENTIAL_CATCH"
        estimated_runs = 0
        catching_fielders = [fe.role_name for fe in fielder_evals if fe.can_intercept_for_catch]
        notes.append(
            f"Potential Catch: Interception window is physically reachable for {', '.join(catching_fielders)} "
            f"at t = {earliest_catch_time:.2f} s prior to first ground contact. Actual wicket depends on catch completion."
        )

    # 2. Six: Ball clears the boundary on the full without touching ground inside
    elif crossing.intersects and crossing.crossed_on_full:
        primary_call = "SIX"
        estimated_runs = 6
        notes.append("Boundary Six: Ball cleared the field boundary on the full without touching the ground.")

    # 3. Ground Cutoff / Fielded before Boundary:
    elif ground_stop is not None and ground_stop.can_intercept and (not crossing.intersects or ground_stop.earliest_intercept_time_s < crossing_time):
        r_field = ground_stop.distance_from_pitch_m
        t_field = ground_stop.earliest_intercept_time_s

        # Override rope_analysis: boundary Four was prevented by ground fielding
        rope_analysis.clears_rope = False
        rope_analysis.summary = (
            f"CUT OFF INSIDE BOUNDARY: Pitched at {first_bounce_dist:.1f}m. "
            f"Fielded cleanly by {ground_stop.role_name} at {r_field:.1f}m (t={t_field:.2f}s), preventing boundary Four."
        )

        if r_field <= 25.0 and t_field <= 2.5:
            primary_call = "DOT"
            estimated_runs = 0
            notes.append(f"Dot Ball: Ball fielded cleanly in the infield by {ground_stop.role_name} at {r_field:.1f}m (t={t_field:.2f}s). Boundary prevented.")
        elif r_field <= 45.0 and t_field <= 4.0:
            primary_call = "SINGLE"
            estimated_runs = 1
            notes.append(f"Single: Ball fielded in the inner ring by {ground_stop.role_name} at {r_field:.1f}m (t={t_field:.2f}s). Boundary prevented.")
        elif r_field <= 65.0:
            primary_call = "DOUBLE"
            estimated_runs = 2
            notes.append(f"Double: Ball cut off in deep outfield by {ground_stop.role_name} at {r_field:.1f}m (t={t_field:.2f}s). Boundary saved.")
        else:
            primary_call = "THREE"
            estimated_runs = 3
            notes.append(f"Three: Ball cut off near boundary rope by {ground_stop.role_name} at {r_field:.1f}m (t={t_field:.2f}s). Boundary saved.")

    # 4. Four: Ball bounces inside, no fielder cutoff, and subsequently clears the boundary rope
    elif crossing.intersects and not crossing.crossed_on_full:
        primary_call = "FOUR"
        estimated_runs = 4
        notes.append(f"Boundary Four: {rope_analysis.summary}")

    # Ball remains inside boundary:
    else:
        notes.append(rope_analysis.summary)
        if player_data_missing:
            primary_call = "IN_PLAY_FIELDER_DATA_REQUIRED"
            estimated_runs = None
            notes.append(
                "In-Play Ball: The ball remains inside the field boundary. Specific match outcome "
                "(Catch, Single, Double, or Dot) requires fielder tracking and batsman running times."
            )
        else:
            stop_time = multi_bounce_result.final_stopping_time_s
            if total_dist < 15.0 or stop_time < 2.0:
                primary_call = "DOT"
                estimated_runs = 0
                notes.append("Dot Ball: Ball fielded quickly in the infield.")
            elif total_dist < 40.0 and stop_time < 4.5:
                primary_call = "SINGLE"
                estimated_runs = 1
                notes.append("Single: Ball fielded in the inner/middle ring; time permits single run.")
            elif total_dist < 60.0:
                primary_call = "DOUBLE"
                estimated_runs = 2
                notes.append("Double: Deep outfield placement allows two runs.")
            else:
                primary_call = "THREE"
                estimated_runs = 3
                notes.append("Three: Cut off just inside boundary with long return throw.")

    return CricketOutcome(
        primary_call=primary_call,
        physics_facts=physics_facts,
        geometry_facts=geometry_facts,
        rope_clearance=rope_analysis,
        fielder_evaluations=fielder_evals,
        estimated_runs=estimated_runs,
        player_data_missing=player_data_missing,
        scientific_notes=notes,
    )
