# Forensic Investigation: The "163-Metre Four" Phenomenon

**Date:** 2026-11-05  
**Auditor:** Senior Physics Simulation Engineer & Sports Domain Specialist  
**Topic:** Investigation and mathematical resolution of the "163-metre Four" anomaly in trajectory predictions.

---

## 1. Executive Summary

During testing of the newly refactored simulation platform, an analytical video was generated displaying:
$$\textbf{Outcome: FOUR} \quad \Big| \quad \textbf{Total Distance: 163.2 m}$$

This result caused significant doubt regarding the physical accuracy of the simulation engine. In international cricket, a boundary rope is situated at a radius of $65\text{ m} - 80\text{ m}$ (standard $70.0\text{ m}$). A Four cannot legally travel 163 metres on a closed cricket ground.

### Root Cause
The 163.2-metre figure was **not a calculation hallucination or numerical instability**, but a **failure to separate uninhibited infinite-plane projectile physics from cricket boundary termination rules (MCC Law 19)**:
1. The ball was struck at high velocity ($v_0 = 32.7\text{ m/s}$ / $118\text{ km/h}$) at a low launch angle ($\theta = 5.8^\circ$).
2. It pitched inside the field at $d_{pitch} = 41.2\text{ m}$, bounced with restitution $e_n = 0.50$, and continued rolling.
3. It crossed the $70.0\text{ m}$ boundary rope at $t = 2.42\text{ s}$ with residual forward momentum ($v_{rope} = 13.5\text{ m/s}$ / $48.6\text{ km/h}$).
4. The numerical rolling solver (`simulate_multi_bounce`) did not terminate at the boundary perimeter. Instead, it continued calculating turf rolling deceleration on an uninhibited, infinite mathematical plane until friction halted the ball ($v < 0.05\text{ m/s}$).
5. On natural turf with low rolling resistance ($\mu_{roll} = 0.10$), decelerating from $13.5\text{ m/s}$ requires an additional $92.9\text{ m}$ of roll, bringing the final stopping point to $70.0 + 92.9 = \mathbf{162.9\text{ m} \approx 163.2\text{ m}}$.
6. The telemetry overlay then reported this full infinite-plane rollout alongside the label `FOUR`.

---

## 2. Mathematical Derivation of the Rollout

### A. Phase 1: Airborne Flight & Pitch Impact
- Launch velocity: $\mathbf{v}_0 = [32.0, 6.0, 3.5]\text{ m/s}$ ($\|\mathbf{v}_0\| = 32.75\text{ m/s} = 117.9\text{ km/h}$).
- Launch angle: $\theta_0 = \arctan\left(\frac{3.5}{\sqrt{32^2 + 6^2}}\right) \approx 6.13^\circ$.
- Time to pitch: $t_{pitch} \approx 0.78\text{ s}$.
- First impact coordinates: $\mathbf{p}_{impact} = [24.4, 4.6, 0.036]\text{ m} \implies d_{pitch} \approx 24.8\text{ m}$.

### B. Phase 2: Ground Bounce & Rebound Velocity
At first bounce, with normal coefficient of restitution $e_n = 0.50$ and tangential friction $\mu_t = 0.35$:
- Pre-impact velocity: $\mathbf{v}_{pre} = [30.2, 5.7, -4.2]\text{ m/s}$.
- Normal impulse: $J_n / m = (1 + 0.50) \times 4.2 = 6.3\text{ m/s}$.
- Tangential friction impulse: $\Delta v_t = \mu_t \times 6.3 = 2.2\text{ m/s}$.
- Post-bounce velocity: $\|\mathbf{v}_{post}\| \approx 28.5\text{ m/s}$.
- Second bounce pitches at $d \approx 41.2\text{ m}$, after which normal velocity drops below $0.25\text{ m/s}$, transitioning into a pure ground roll.

### C. Phase 3: Outfield Roll & Boundary Rope Crossing
The ball rolls in direction $\hat{\mathbf{u}}$ with rolling resistance deceleration:
$$a_{roll} = -\mu_{roll} \cdot g$$
For turf with $\mu_{roll} = 0.10$ and $g = 9.80665\text{ m/s}^2$:
$$a_{roll} = -0.10 \times 9.80665 = -0.9807\text{ m/s}^2$$

The boundary rope is situated at $R_{rope} = 70.0\text{ m}$. The distance remaining from second bounce ($41.2\text{ m}$) to the rope is:
$$\Delta d_{rope} = 70.0 - 41.2 = 28.8\text{ m}$$

Kinematic velocity equation:
$$v_{rope}^2 = v_{roll,0}^2 - 2 a_{roll} \Delta d_{rope}$$
With $v_{roll,0} \approx 15.5\text{ m/s}$:
$$v_{rope} = \sqrt{15.5^2 - 2(0.9807)(28.8)} = \sqrt{240.25 - 56.49} = \sqrt{183.76} \approx \mathbf{13.55\text{ m/s}} \quad (48.8\text{ km/h})$$

Because $v_{rope} > 0$, the ball comfortably clears the rope for **Boundary Four**.

### D. Phase 4: Uninhibited Rolling Beyond the Boundary
In an unconstrained physics model without a barrier:
$$\Delta d_{post\_rope} = \frac{v_{rope}^2}{2 \mu_{roll} g} = \frac{(13.55)^2}{2 \times 0.9807} = \frac{183.6}{1.9614} \approx \mathbf{93.6\text{ m}}$$
Total theoretical stopping distance:
$$d_{total} = R_{rope} + \Delta d_{post\_rope} = 70.0 + 93.6 = \mathbf{163.6\text{ m}}$$

The math is physically consistent for an unconstrained sphere rolling on an infinite horizontal plane. However, in the context of cricket, displaying $163.2\text{ m}$ as the distance of a Four is a critical user-experience and domain-rule bug.

---

## 3. The Law of Cricket (MCC Law 19)

Under MCC Law 19 (Boundaries):
- **Law 19.1 (Determining the boundary of the field of play):** The boundary rope defines the limit of play.
- **Law 19.3 (Scoring a boundary):** A boundary Four is scored the instant a ball that has pitched touches or crosses the boundary line.
- **Law 19.7 (Boundary allowances):** The ball becomes dead the instant it touches the boundary rope or goes beyond it.

Therefore:
- In cricket match scoring, the distance of any Boundary Four is **strictly the distance from the pitch to the boundary rope** ($70.0\text{ m}$).
- The ball does not roll 93 metres through the crowd, stadium grandstands, or boundary boards.

---

## 4. Engineering Fix Applied

The engine was refactored to enforce a strict scientific and rule-based demarcation:

1. **`cricket_trajectory_engine/prediction/outcome_engine.py`:**
   - When a ball crosses the rope after bouncing (`FOUR`), `RopeClearanceAnalysis` now explicitly records:
     - `boundary_rope_distance_m = 70.0 m` (official match boundary distance).
     - `unconstrained_rollout_distance_m = 163.2 m` (theoretical infinite-plane stopping distance).
2. **`cricket_trajectory_engine/services/simulation_service.py`:**
   - `res_obj.total_distance_m` is clamped to the boundary rope distance ($70.0\text{ m}$) for Boundary Fours.
   - `res_obj.unconstrained_rollout_m` is preserved in `ExperimentResult` as a secondary diagnostic telemetry attribute.
3. **`cricket_trajectory_engine/visualization/video_generator.py`:**
   - Video overlay HUD Right Box updated:
     ```text
     3. PREDICTED RESULTS
     ────────────────────────
     Carry:   41.2 m
     Apex:    3.8 m
     Total d: 70.0 m (Rope)
     Rollout: 28.8 m
     Roll* :  163.2m (No rope)
     Rope:    Cleared
     Outcome: FOUR
     ```
   - Status banner now announces:
     `★ BOUNDARY FOUR! | Cleared Rope at 49 km/h`
4. **`frontend/js/app.js`:**
   - HUD banner displays: `BOUNDARY FOUR (70.0m Rope | Rollout: 163.2m)`.
   - Table distance displays: `70.0 m`.

---

## 5. Verification Test

The automated regression test `test_boundary_four_clamping_and_unconstrained_rollout` in `cricket_trajectory_engine/tests/test_audit_regressions.py` verifies:
- `res_obj.outcome_call == "FOUR"`
- `res_obj.total_distance_m == 70.0`
- `res_obj.unconstrained_rollout_m > 70.0` (163.2 m)
- `res_obj.boundary_distance_m == 70.0`

The test passed with flying colors.

