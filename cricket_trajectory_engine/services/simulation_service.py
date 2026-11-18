"""
Simulation Service: Orchestrates trajectory solving, event detection,
and structured mathematical calculation trace generation.
"""

import math
import numpy as np
from typing import Dict, Any, Tuple, Optional, List

from cricket_trajectory_engine.config.physics_config import (
    BallConfig,
    EnvironmentConfig,
    AerodynamicsConfig,
    GroundCollisionConfig,
    FieldConfig,
    SimulationConfig,
)
from cricket_trajectory_engine.core.calculation_trace import CalculationTrace
from cricket_trajectory_engine.models.experiment import (
    ExperimentConfig,
    ExperimentResult,
    compute_simulation_fingerprint,
)
from cricket_trajectory_engine.physics.flight_simulator import simulate_flight
from cricket_trajectory_engine.physics.ground_collision import simulate_multi_bounce, MultiBounceResult
from cricket_trajectory_engine.prediction.field_geometry import CricketField
from cricket_trajectory_engine.prediction.outcome_engine import (
    evaluate_outcome,
    FielderPosition,
    CricketOutcome,
)


class SimulationService:
    """Orchestrates physics simulation and populates the structured CalculationTrace."""

    def run_simulation(
        self, config: ExperimentConfig
    ) -> Tuple[ExperimentResult, CalculationTrace, MultiBounceResult, CricketOutcome]:
        trace = CalculationTrace()

        # 1. Parse Ball properties:
        ball_dict = config.ball or {}
        m_ball = float(ball_dict.get("mass_kg", 0.160))
        d_ball = float(ball_dict.get("diameter_m", 0.0725))
        r_ball = d_ball / 2.0
        area_ball = math.pi * (d_ball ** 2) / 4.0
        inertia_ball = (2.0 / 3.0) * m_ball * (r_ball ** 2)
        ball_cfg = BallConfig(mass_kg=m_ball, diameter_m=d_ball)

        # 2. Parse Environment & Aerodynamics:
        env_dict = config.environment or {}
        rho_air = float(env_dict.get("air_density_kg_m3", 1.225))
        mu_air = float(env_dict.get("dynamic_viscosity_pa_s", 1.81e-5))
        g_val = float(env_dict.get("gravity_m_s2", 9.80665))
        w_vec = tuple(float(x) for x in env_dict.get("wind_vector_m_s", [0.0, 0.0, 0.0]))
        env_cfg = EnvironmentConfig(
            air_density_kg_m3=rho_air,
            dynamic_viscosity_pa_s=mu_air,
            gravity_m_s2=g_val,
            wind_vector_m_s=w_vec,
        )

        cd_val = float(env_dict.get("constant_cd", 0.32))
        raw_drag = str(env_dict.get("drag_model", "constant")).lower()
        drag_model = "reynolds_dependent" if ("reynolds" in raw_drag or "morrison" in raw_drag) else "constant"
        enable_magnus = bool(env_dict.get("enable_magnus", False))
        cl_val = float(env_dict.get("constant_cl", 0.15))
        spin_vec = tuple(float(s) for s in env_dict.get("spin_rad_s", [0.0, 0.0, 0.0]))
        aero_cfg = AerodynamicsConfig(
            drag_model=drag_model,
            constant_cd=cd_val,
            enable_magnus=enable_magnus,
            constant_cl=cl_val,
            spin_rad_s=spin_vec,
        )

        # 3. Parse Ground Collision & Turf:
        e_n = float(env_dict.get("restitution_normal", 0.55))
        mu_t = float(env_dict.get("friction_tangential", 0.38))
        mu_roll = float(env_dict.get("rolling_resistance_coeff", 0.20))
        collision_cfg = GroundCollisionConfig(
            restitution_normal=e_n,
            friction_tangential=mu_t,
            rolling_resistance_coeff=mu_roll,
        )

        # 4. Parse Stadium & Fielders:
        stadium_dict = config.stadium or {}
        bnd_r = float(stadium_dict.get("boundary_radius_m", 70.0))
        field_cfg = FieldConfig(boundary_radius_m=bnd_r)
        field_obj = CricketField(field_cfg)

        fielding_dict = config.fielding or {}
        global_sprint = float(fielding_dict.get("sprint_speed_m_s", fielding_dict.get("max_sprint_speed_m_s", 7.0)))
        global_react = float(fielding_dict.get("reaction_time_s", 0.35))
        global_reach = float(fielding_dict.get("reach_radius_m", fielding_dict.get("catching_radius", 1.8)))
        global_min_z = float(fielding_dict.get("min_catch_height_m", 0.25))
        global_max_z = float(fielding_dict.get("max_catch_height_m", 2.30))

        raw_fielders = fielding_dict.get("fielders", [])
        fielders_list = [
            FielderPosition(
                fielder_id=f.get("id", f"fielder_{i}"),
                role_name=f.get("name", f.get("role", "Fielder")),
                x_m=float(f.get("x_m", f.get("x", 0.0))),
                y_m=float(f.get("y_m", f.get("y", 0.0))),
                reaction_time_s=float(f.get("reaction_time_s", global_react)),
                max_sprint_speed_m_s=float(f.get("max_sprint_speed_m_s", f.get("sprint_speed_m_s", f.get("max_speed_m_s", global_sprint)))),
                reach_radius_m=float(f.get("reach_radius_m", f.get("catching_radius", global_reach))),
                min_catch_height_m=float(f.get("min_catch_height_m", global_min_z)),
                max_catch_height_m=float(f.get("max_catch_height_m", global_max_z)),
            )
            for i, f in enumerate(raw_fielders)
        ]

        # 5. Initial State:
        p0 = np.array(config.pos0, dtype=float)
        v0 = np.array(config.vel0, dtype=float)
        speed0 = float(np.linalg.norm(v0))
        elev0_deg = math.degrees(math.atan2(v0[2], math.hypot(v0[0], v0[1])))
        azim0_deg = math.degrees(math.atan2(v0[1], v0[0]))

        # Trace Step 1: Launch Kinematics
        trace.add_step(
            step_id="step_launch_state",
            stage_name="Initial State Estimation",
            formula_latex=r"v_0 = \sqrt{V_{x0}^2 + V_{y0}^2 + V_{z0}^2}, \quad \theta_0 = \arctan\left(\frac{V_{z0}}{\sqrt{V_{x0}^2 + V_{y0}^2}}\right)",
            formula_text="v0 = sqrt(Vx0^2 + Vy0^2 + Vz0^2), theta0 = arctan(Vz0 / sqrt(Vx0^2 + Vy0^2))",
            description="Converts the initial velocity Cartesian vector into scalar launch speed and launch angles.",
            inputs={"Vx0": v0[0], "Vy0": v0[1], "Vz0": v0[2]},
            substitution_text=f"v0 = sqrt(({v0[0]:.2f})^2 + ({v0[1]:.2f})^2 + ({v0[2]:.2f})^2)",
            result_value={"speed_m_s": speed0, "speed_kmh": speed0 * 3.6, "elevation_deg": elev0_deg, "azimuth_deg": azim0_deg},
            result_formatted=f"{speed0 * 3.6:.1f} km/h ({speed0:.2f} m/s) at {elev0_deg:+.1f}° elevation, {azim0_deg:+.1f}° azimuth",
            units="km/h and degrees",
            why_necessary="Establishes initial conditions for numerical integration of Newton's equations of motion.",
            downstream_dependents=["step_reynolds_number", "step_equations_of_motion"],
        )

        # Trace Step 2: Reynolds Number
        re_val = (rho_air * speed0 * d_ball) / mu_air
        trace.add_step(
            step_id="step_reynolds_number",
            stage_name="Aerodynamics",
            formula_latex=r"Re = \frac{\rho \cdot \|\mathbf{v}_{rel}\| \cdot D}{\mu}",
            formula_text="Re = (rho * |v_rel| * D) / mu",
            description="Non-dimensional ratio of inertial forces to viscous forces in surrounding airflow.",
            inputs={"rho": rho_air, "v_rel": speed0, "D": d_ball, "mu": mu_air},
            substitution_text=f"Re = ({rho_air:.3f} * {speed0:.2f} * {d_ball:.4f}) / {mu_air:.2e}",
            result_value=re_val,
            result_formatted=f"{re_val:.1e} ({int(re_val)})",
            units="dimensionless",
            why_necessary="Identifies the boundary-layer flow regime around the cricket ball to calibrate drag coefficient Cd.",
            downstream_dependents=["step_aerodynamic_drag"],
        )

        # Trace Step 3: Aerodynamic Drag
        f_drag_mag = 0.5 * rho_air * cd_val * area_ball * (speed0 ** 2)
        v_hat = v0 / speed0 if speed0 > 1e-6 else np.array([1.0, 0.0, 0.0])
        f_drag_vec = -f_drag_mag * v_hat
        trace.add_step(
            step_id="step_aerodynamic_drag",
            stage_name="Aerodynamics",
            formula_latex=r"\mathbf{F}_{drag} = -\frac{1}{2} \rho C_d A \|\mathbf{v}_{rel}\| \mathbf{v}_{rel}",
            formula_text="F_drag = -0.5 * rho * Cd * A * |v_rel| * v_rel",
            description="Aerodynamic drag opposing the cricket ball's motion relative to ambient air.",
            inputs={"rho": rho_air, "Cd": cd_val, "A": area_ball, "v_rel": speed0, "D": d_ball},
            substitution_text=f"F_drag = -0.5 * {rho_air:.3f} * {cd_val:.2f} * {area_ball:.6f} * ({speed0:.2f})^2",
            result_value=f_drag_vec.tolist(),
            result_formatted=f"Magnitude = {f_drag_mag:.2f} N | Vector = [{f_drag_vec[0]:.2f}, {f_drag_vec[1]:.2f}, {f_drag_vec[2]:.2f}] N",
            units="Newtons (N)",
            why_necessary="Retards forward velocity and alters the trajectory arc away from a theoretical vacuum parabola.",
            downstream_dependents=["step_equations_of_motion"],
        )

        # Trace Step 4: Net Acceleration at Launch
        a_drag = f_drag_vec / m_ball
        a_net = np.array([a_drag[0], a_drag[1], -g_val + a_drag[2]])
        trace.add_step(
            step_id="step_equations_of_motion",
            stage_name="Flight Dynamics",
            formula_latex=r"\mathbf{a} = \mathbf{g} + \frac{1}{m}(\mathbf{F}_{drag} + \mathbf{F}_{magnus})",
            formula_text="a = g + (F_drag + F_magnus) / m",
            description="Total acceleration acting on the cricket ball center of mass.",
            inputs={"g": [0.0, 0.0, -g_val], "F_drag": f_drag_vec.tolist(), "m": m_ball},
            substitution_text=f"a = [0, 0, -{g_val:.2f}] + [{f_drag_vec[0]:.2f}, {f_drag_vec[1]:.2f}, {f_drag_vec[2]:.2f}] / {m_ball:.3f}",
            result_value=a_net.tolist(),
            result_formatted=f"[{a_net[0]:.2f}, {a_net[1]:.2f}, {a_net[2]:.2f}] m/s² (Magnitude = {np.linalg.norm(a_net):.2f} m/s²)",
            units="m/s²",
            why_necessary="Integrated via SciPy's adaptive RK45 algorithm to compute position and velocity time-series.",
            downstream_dependents=["step_apex_carry", "step_ground_impact"],
        )

        # 6. Execute Multi-Bounce Simulation:
        res_flight = simulate_flight(p0, v0, ball_cfg, env_cfg, aero_cfg)
        res_multibounce = simulate_multi_bounce(p0, v0, ball_cfg, env_cfg, aero_cfg, collision_cfg)
        outcome = evaluate_outcome(res_multibounce, field_config=field_cfg, fielders=fielders_list)

        # Extract flight facts:
        apex_h = float(res_flight.max_height_m)
        apex_idx = int(np.argmax(res_flight.positions_m[:, 2])) if len(res_flight.positions_m) > 0 else 0
        t_apex = float(res_flight.time_s[apex_idx]) if len(res_flight.time_s) > 0 else 0.0
        d_carry = float(res_flight.horizontal_range_m)
        t_flight = float(res_flight.flight_time_s)
        landing_pos = list(res_flight.landing["position_m"]) if res_flight.landing else list(res_flight.positions_m[-1])

        # Trace Step 5: Apex & Carry
        trace.add_step(
            step_id="step_apex_carry",
            stage_name="Flight Dynamics",
            formula_latex=r"Z_{max} = \max_t Z(t), \quad d_{carry} = \sqrt{X(t_{pitch})^2 + Y(t_{pitch})^2}",
            formula_text="Z_max = max(Z(t)), d_carry = sqrt(X(t_pitch)^2 + Y(t_pitch)^2)",
            description="Peak flight altitude and horizontal carry distance to first turf pitch impact.",
            inputs={"Z0": p0[2], "Vz0": v0[2], "t_flight": t_flight},
            substitution_text=f"Apex reached at t = {t_apex:.2f} s; Impact at t = {t_flight:.2f} s",
            result_value={"apex_m": apex_h, "t_apex_s": t_apex, "carry_m": d_carry, "landing_pos": landing_pos},
            result_formatted=f"Apex = {apex_h:.2f} m at t={t_apex:.2f}s | Carry Distance = {d_carry:.1f} m",
            units="metres (m) and seconds (s)",
            why_necessary="Determines whether the ball clears the boundary rope on the full (SIX) or pitches in-field.",
            downstream_dependents=["step_ground_impact", "step_boundary_outcome"],
        )

        # Trace Step 6: Ground Collision Restitution
        first_b = res_multibounce.first_bounce
        if first_b:
            vz_in = abs(float(first_b.pre_velocity_m_s[2]))
            vz_out = float(first_b.post_velocity_m_s[2])
            energy_loss = float(first_b.energy_loss_ratio * 100.0)
            trace.add_step(
                step_id="step_ground_impact",
                stage_name="Turf Contact Mechanics",
                formula_latex=r"v_{z}^+ = -e_n \cdot v_{z}^-, \quad \Delta E_z = 1 - e_n^2",
                formula_text="vz+ = -e_n * vz-, Delta_Ez = 1 - e_n^2",
                description="Normal velocity rebound with energy dissipation based on Banerjee & McPhee (2012).",
                inputs={"en": e_n, "vz_before": vz_in},
                substitution_text=f"vz+ = -{e_n:.2f} * {vz_in:.2f} m/s | Energy Loss = 1 - ({e_n:.2f})^2",
                result_value={"vz_after": vz_out, "energy_loss_pct": energy_loss},
                result_formatted=f"Rebound Vz = {vz_out:.2f} m/s | Kinetic Energy Loss = {energy_loss:.1f}%",
                units="m/s and %",
                why_necessary="Accurately models post-pitch rebound height and forward speed attenuation.",
                downstream_dependents=["step_rolling_clearance"],
            )

        # Trace Step 7: Outfield Grass Rolling & Rope Clearance
        rc = outcome.rope_clearance
        a_roll = mu_roll * g_val
        trace.add_step(
            step_id="step_rolling_clearance",
            stage_name="Outfield Rolling & Rope Clearance",
            formula_latex=r"a_{roll} = -\mu_{roll} \cdot g, \quad v_{req\_min} = \sqrt{2 \mu_{roll} g \Delta d_{rope}}",
            formula_text="a_roll = -mu_roll * g, v_req_min = sqrt(2 * mu_roll * g * Delta_d_rope)",
            description="Deceleration across outfield grass to predict whether post-bounce momentum clears the boundary rope.",
            inputs={
                "mu_roll": mu_roll,
                "g": g_val,
                "Delta_d_rope": rc.distance_remaining_to_rope_m,
                "post_bounce_distance": rc.post_bounce_distance_travelled_m,
            },
            substitution_text=f"a_roll = -{mu_roll:.2f} * {g_val:.2f} = -{a_roll:.2f} m/s² | v_req = sqrt(2 * {a_roll:.2f} * {rc.distance_remaining_to_rope_m:.1f})",
            result_value={
                "a_roll_m_s2": -a_roll,
                "min_speed_req_m_s": rc.minimum_speed_required_m_s,
                "residual_at_rope_kmh": (rc.residual_speed_at_rope_m_s or 0.0) * 3.6,
                "clears_rope": rc.clears_rope,
                "margin_m": rc.margin_m,
            },
            result_formatted=f"Decel = -{a_roll:.2f} m/s² | Min Speed Req = {rc.minimum_speed_required_m_s*3.6:.1f} km/h | Status = {rc.summary}",
            units="m/s² and km/h",
            why_necessary="Differentiates between a Boundary Four and an in-play Single/Double that pulls up short.",
            downstream_dependents=["step_boundary_outcome"],
        )

        # Trace Step 8: Fielder Catchability
        catches = [ce for ce in outcome.fielder_evaluations if ce.can_intercept_for_catch]
        best_catch_dict = None
        if catches:
            fc = catches[0]
            is_direct = (fc.required_sprint_speed_m_s is not None and fc.required_sprint_speed_m_s <= 0.1)
            fc_obj = next((f for f in fielders_list if f.fielder_id == fc.fielder_id), None)
            t_react_val = fc_obj.reaction_time_s if fc_obj else 0.35
            v_max_val = fc.required_sprint_speed_m_s if fc.required_sprint_speed_m_s is not None else (fc_obj.max_sprint_speed_m_s if fc_obj else 7.0)
            r_reach_val = fc_obj.reach_radius_m if fc_obj else 1.8
            best_catch_dict = {
                "fielder_id": fc.fielder_id,
                "role_name": fc.role_name,
                "fielder_name": fc.role_name,
                "catch_time_s": fc.earliest_intercept_time_s,
                "intercept_time_s": fc.earliest_intercept_time_s,
                "required_speed_m_s": fc.required_sprint_speed_m_s,
                "margin_distance_m": fc.margin_distance_m,
                "catch_type": "Direct Catch (In Hands / Stationary Zone)" if is_direct else "Sprint Interception",
                "can_intercept": True,
            }
            trace.add_step(
                step_id="step_fielder_catch",
                stage_name="Fielding Analysis",
                formula_latex=r"D_{run} = v_{max} \cdot \max(0, t - t_{react}), \quad \text{Valid if } D_{ball} \le D_{run} + r_{reach}",
                formula_text="D_run = v_max * max(0, t - t_react), Catch Valid if D_ball <= D_run + r_reach",
                description="Kinematic reachability calculation for fielders attempting to intercept the airborne ball.",
                inputs={
                    "fielder": fc.role_name,
                    "t_reach": fc.earliest_intercept_time_s,
                    "t_react": t_react_val,
                    "v_max": v_max_val,
                    "r_reach": r_reach_val,
                },
                substitution_text=f"Intercept at t = {fc.earliest_intercept_time_s or 0.0:.2f} s by {fc.role_name}",
                result_value=best_catch_dict,
                result_formatted=f"{fc.role_name} intercepts at t={fc.earliest_intercept_time_s or 0.0:.2f}s ({best_catch_dict['catch_type']})",
                units="metres and seconds",
                why_necessary="Evaluates whether an airborne shot will result in a Wicket (Catch/Out).",
                downstream_dependents=["step_boundary_outcome"],
            )

        # Compute nearest fielder spatial relationship to first landing point
        if fielders_list:
            lx, ly = landing_pos[0], landing_pos[1]
            closest_f = min(fielders_list, key=lambda f: math.hypot(lx - f.x_m, ly - f.y_m))
            dist_to_fielder = math.hypot(lx - closest_f.x_m, ly - closest_f.y_m)
            r_ball = math.hypot(lx, ly)
            r_fielder = math.hypot(closest_f.x_m, closest_f.y_m)
            f_reach = closest_f.reach_radius_m

            if dist_to_fielder <= f_reach:
                spatial_rel = f"Directly in Catching Zone ({dist_to_fielder:.2f}m from fielder, within {f_reach:.1f}m reach)"
            elif r_ball < r_fielder - f_reach:
                spatial_rel = f"Falls Short of Fielder by {r_fielder - r_ball:.1f} m"
            else:
                spatial_rel = f"Travels Beyond Fielder by {r_ball - r_fielder:.1f} m"

            nearest_info = {
                "fielder_id": closest_f.fielder_id,
                "role_name": closest_f.role_name,
                "distance_to_landing_m": round(dist_to_fielder, 2),
                "fielder_coords": [closest_f.x_m, closest_f.y_m],
                "spatial_relationship": spatial_rel,
                "reach_radius_m": f_reach,
                "max_sprint_speed_m_s": closest_f.max_sprint_speed_m_s,
                "reaction_time_s": closest_f.reaction_time_s,
                "min_catch_height_m": closest_f.min_catch_height_m,
                "max_catch_height_m": closest_f.max_catch_height_m,
            }
            if best_catch_dict is None:
                best_catch_dict = {
                    "can_intercept": False,
                    "nearest_fielder": nearest_info,
                    "role_name": closest_f.role_name,
                    "fielder_name": closest_f.role_name,
                }
            else:
                best_catch_dict["nearest_fielder"] = nearest_info
                # Refine catch_type if landing is within standing reach radius
                if dist_to_fielder <= f_reach or (best_catch_dict.get("required_speed_m_s") is not None and best_catch_dict["required_speed_m_s"] <= 0.25):
                    best_catch_dict["catch_type"] = "Direct Catch (In Hands / Stationary Zone)"

        # Trace Step 9: Final Cricket Outcome Classification
        trace.add_step(
            step_id="step_boundary_outcome",
            stage_name="Cricket Outcome Engine",
            formula_latex=r"\text{Decision: } \text{SIX} \mid \text{FOUR} \mid \text{OUT (CATCH)} \mid \text{IN-PLAY (RUNS)}",
            formula_text="Outcome based on boundary crossing, bounce history, and fielder reachability",
            description="MCC Laws of Cricket outcome determination combining flight, contact, and tactical rules.",
            inputs={"primary_call": outcome.primary_call, "runs": outcome.estimated_runs},
            substitution_text=f"Call: {outcome.primary_call} | Estimated Runs: {outcome.estimated_runs}",
            result_value={"call": outcome.primary_call, "runs": outcome.estimated_runs},
            result_formatted=f"FINAL CALL: [{outcome.primary_call}] — {outcome.estimated_runs} Runs",
            units="Cricket Runs / Wicket",
            why_necessary="Final match decision presented on broadcast telemetry.",
            downstream_dependents=[],
        )

        # 7. Formulate ExperimentResult:
        fingerprint = compute_simulation_fingerprint(
            pos0=config.pos0,
            vel0=config.vel0,
            ball_dict=ball_dict,
            env_dict=env_dict,
            stadium_dict=stadium_dict,
            solver_dict=config.solver,
            fielding_dict=fielding_dict,
        )

        unconstrained_rollout = float(res_multibounce.total_horizontal_distance_m)
        if outcome.primary_call == "FOUR":
            # MCC Law 19: Ball is dead upon contacting boundary rope
            match_total_dist = float(rc.boundary_rope_distance_m)
            boundary_dist = float(rc.boundary_rope_distance_m)
        elif outcome.primary_call == "SIX":
            match_total_dist = float(d_carry)
            boundary_dist = float(rc.boundary_rope_distance_m)
        elif not rc.clears_rope and fielders_list:
            closest_f = min(fielders_list, key=lambda f: math.hypot(landing_pos[0] - f.x_m, landing_pos[1] - f.y_m))
            r_f = math.hypot(closest_f.x_m, closest_f.y_m)
            match_total_dist = min(unconstrained_rollout, max(float(d_carry), float(r_f)))
            boundary_dist = None
        else:
            match_total_dist = unconstrained_rollout
            boundary_dist = None

        # Refine primary outcome call to distinguish between Direct In-Hands catch,
        # Sprint Interception, Diving Catch, Overhead Clearance, balls falling short, and balls traveling beyond
        refined_call = outcome.primary_call
        if outcome.primary_call == "POTENTIAL_CATCH" and best_catch_dict:
            c_type = best_catch_dict.get("catch_type", "")
            nf = best_catch_dict.get("nearest_fielder", {})
            f_name = best_catch_dict.get("role_name", "Fielder")
            req_spd = best_catch_dict.get("required_speed_m_s")
            f_max_spd = nf.get("max_sprint_speed_m_s", 7.0) if nf else 7.0

            if "Direct Catch" in c_type or (req_spd is not None and req_spd <= 0.10):
                refined_call = f"CAUGHT (IN HANDS — {f_name})"
            elif req_spd is not None and req_spd >= (f_max_spd - 0.35):
                refined_call = f"CAUGHT (DIVING — {f_name} @ {req_spd:.1f} m/s)"
            elif req_spd is not None and req_spd > 0.10:
                refined_call = f"CAUGHT (SPRINT INTERCEPTION — {f_name} @ {req_spd:.1f} m/s)"
            else:
                refined_call = f"CAUGHT ({f_name})"
        elif outcome.primary_call in ("DOT", "SINGLE", "DOUBLE", "THREE", "IN_PLAY_RUNS_EVALUATED", "IN_PLAY_FIELDER_DATA_REQUIRED") and best_catch_dict:
            nf = best_catch_dict.get("nearest_fielder", {})
            f_name = best_catch_dict.get("role_name", "Fielder")
            if fielders_list:
                closest_f = min(fielders_list, key=lambda f: math.hypot(landing_pos[0] - f.x_m, landing_pos[1] - f.y_m))
                r_f = math.hypot(closest_f.x_m, closest_f.y_m)
                r_series = np.hypot(res_multibounce.positions_m[:, 0], res_multibounce.positions_m[:, 1])
                idx_plane = np.searchsorted(r_series, r_f)
                z_plane = float(res_multibounce.positions_m[idx_plane, 2]) if idx_plane < len(r_series) else None
                if z_plane is not None and z_plane > closest_f.max_catch_height_m and d_carry > r_f:
                    refined_call = f"OVERHEAD CLEARANCE (CLEARS {f_name})"
                elif nf and "Falls Short" in nf.get("spatial_relationship", ""):
                    margin_str = nf["spatial_relationship"].split("by ")[-1]
                    refined_call = f"FALLS SHORT ({margin_str} in front)"
                elif nf and "Travels Beyond" in nf.get("spatial_relationship", ""):
                    margin_str = nf["spatial_relationship"].split("by ")[-1]
                    refined_call = f"TRAVELS BEYOND ({margin_str} over)"
            elif nf and "Falls Short" in nf.get("spatial_relationship", ""):
                margin_str = nf["spatial_relationship"].split("by ")[-1]
                refined_call = f"FALLS SHORT ({margin_str} in front)"
            elif nf and "Travels Beyond" in nf.get("spatial_relationship", ""):
                margin_str = nf["spatial_relationship"].split("by ")[-1]
                refined_call = f"TRAVELS BEYOND ({margin_str} over)"

        is_boundary = outcome.primary_call in ("FOUR", "SIX")
        clears_rope_flag = rc.clears_rope if is_boundary else False

        if outcome.primary_call == "POTENTIAL_CATCH":
            match_total_dist = float(d_carry)

        res_obj = ExperimentResult(
            fingerprint=fingerprint,
            flight_time_s=t_flight,
            carry_distance_m=d_carry,
            max_height_m=apex_h,
            time_to_apex_s=t_apex,
            first_landing_pos_m=landing_pos,
            total_bounces=len(res_multibounce.bounces),
            post_bounce_roll_m=float(rc.post_bounce_distance_travelled_m),
            total_distance_m=match_total_dist,
            final_stopping_pos_m=res_multibounce.final_stopping_position_m.tolist(),
            clears_rope=clears_rope_flag,
            residual_speed_at_rope_kmh=(rc.residual_speed_at_rope_m_s * 3.6) if rc.residual_speed_at_rope_m_s else None,
            margin_to_rope_m=float(rc.margin_m),
            outcome_call=refined_call,
            estimated_runs=outcome.estimated_runs,
            fielder_interception=best_catch_dict,
            unconstrained_rollout_m=unconstrained_rollout,
            boundary_distance_m=boundary_dist,
            warnings=outcome.scientific_notes,
        )

        return res_obj, trace, res_multibounce, outcome
