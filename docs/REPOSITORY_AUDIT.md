# Repository Audit and Architecture Refactoring Plan

**Project:** Interactive 3D Cricket Ball Trajectory Prediction and Experimentation Platform  
**Date:** November 2026  
**Auditor:** Senior Python, Physics Simulation & Graphics Engineer

---

## 1. Existing Repository Overview & Architecture

The existing repository consists of:
- `cricket_trajectory_engine/`:
  - `config/physics_config.py`: Configuration dataclasses for Ball, Environment, Aerodynamics, GroundCollision, Field, and Simulation.
  - `physics/`:
    - `constants.py`: Physical constants (air density, viscosity, ball mass, turf restitution).
    - `gravity.py`: Gravitational acceleration vector.
    - `drag.py`: Quadratic drag formula and Reynolds number calculation.
    - `magnus.py`: Magnus lift/dip cross-product formulation and spin parameter.
    - `aerodynamics.py`: Acceleration combining gravity, drag, Magnus force, and seam stub.
    - `flight_simulator.py`: SciPy `solve_ivp` RK45 numerical flight solver with zero-crossing ground contact event.
    - `ground_collision.py`: Restitution, tangential friction impulse, torque-spin coupling, multi-bounce and rolling.
  - `estimation/`:
    - `coordinate_loader.py`: CSV loader, coordinate validator, `ObservationSet`.
    - `velocity_estimator.py`: Finite difference and 2nd-order polynomial least-squares velocity estimation.
    - `trajectory_fitting.py`: Least-squares trajectory optimization against observed coordinates with identifiability guardrail.
    - `real_delivery_loader.py`: Coordinate adapter mapping stereo camera tracking data into the simulator ground frame.
  - `prediction/`:
    - `field_geometry.py`: Boundary distance $R_{bnd}(\phi)$, 30-yard circle, boundary crossing detection.
    - `outcome_engine.py`: Outcome classification (Six, Four, Catch, Single, Double, Dot) and `RopeClearanceAnalysis`.
    - `uncertainty.py`: Monte Carlo ensemble simulation.
  - `visualization/`:
    - `cricket_ground_renderer.py`: Matplotlib-based 3D cricket stadium visualizer.
    - `video_generator.py`: Video encoding (MP4 via libx264 and animated GIF) with live telemetry HUD and metadata overlay.
    - `interactive_stadium.html`: Prototype WebGL/Canvas viewer.
    - `trajectory_plots.py`: Comparative physics overlays and 2D/3D static diagnostic plots.
  - `tests/`: 23 passing unit tests in `test_physics.py`, `test_collision.py`, `test_estimation.py`, `test_prediction.py`.
- `3d_hits_10_deliveries/`: 10 real tracked match delivery datasets with `summary.csv`.
- `main.py`, `analyze_real_deliveries.py`, `generate_10_delivery_videos.py`: Top-level demonstration and video generation scripts.
- Legacy files in root: `cricket_ball_engine_v0_1.py`, `trajectory_dummy.csv`, `trajectory_dummy.png`.

---

## 2. Files to Retain, Refactor, and Remove

### Retained with Enhancements:
1. `cricket_trajectory_engine/physics/`: Core physics equations (`constants.py`, `gravity.py`, `drag.py`, `magnus.py`, `flight_simulator.py`, `ground_collision.py`) are mathematically sound and verified by 23 passing tests. They will be retained and augmented with structured **Calculation Trace** logging.
2. `cricket_trajectory_engine/estimation/`: Polynomial fitting, coordinate loading, and real delivery stereo adapters are functional and retained.
3. `cricket_trajectory_engine/prediction/`: Outcome classification and rope clearance calculations are retained and extended with proper 11-player fielding domain rules and competition format restrictions.
4. `cricket_trajectory_engine/tests/`: All 23 tests will be retained and expanded to cover persistence, caching, fielding rules, and API endpoints.

### Files to Remove / Clean Up:
1. `cricket_ball_engine_v0_1.py`: Obsolete prototype file superseded by the modular engine.
2. `trajectory_dummy.csv` and `trajectory_dummy.png` in root: Temporary test artifacts.
3. Duplicated script logic between `analyze_real_deliveries.py` and `generate_10_delivery_videos.py`.

### Architectural Deficiencies to Resolve:
1. **Lack of Structured Calculation Trace**: The engine currently calculates numbers but does not log a first-class mathematical derivation trace (formula, plain explanation, substituted values, calculated result, units, downstream dependencies) for the Formula Explorer.
2. **Missing Persistent Storage & Caching Layer**: No dedicated experiment database/storage service with deterministic SHA-256 simulation fingerprinting to avoid re-running identical simulations.
3. **Fielding Domain Model Limitations**: The existing model places fielders but does not enforce the 11-player constraint (1 keeper, 1 bowler, 9 fielders), does not provide standard tactical presets (Powerplay, Attacking, Death-overs), and does not check format restrictions (T20/ODI 30-yard circle limits).
4. **Single-Angle Video Without Measurement Lines**: Current video generator draws an animated camera angle but lacks the required multi-angle analytical sequence (isometric, side, top-down, rear view) with horizontal ($d_1, d_{total}$) and vertical ($Z_{max}$) measurement guides.
5. **No Full Interactive Web Application**: Only standalone HTML files exist; no interactive dashboard where users can toggle input modes (velocity vs speed/angles), modify turf presets, edit fielding positions, run simulations, inspect the formula explorer, and compare experiments.

---

## 3. Recommended Modular Architecture

```text
cricket_trajectory_engine/
├── core/                           # Pure physics, mathematics, and domain logic
│   ├── constants.py                # Official MCC Law 4, ISA, and turf constants
│   ├── calculation_trace.py        # Structured mathematical explainability engine
│   ├── aerodynamics.py             # Drag, Reynolds number, and Magnus forces
│   ├── flight_dynamics.py          # Equations of motion and RK45 solver
│   ├── collision_model.py          # Ground restitution, friction, and torque-spin coupling
│   ├── rolling_model.py            # Outfield rolling deceleration and rope clearance
│   ├── state_estimation.py         # 2nd-order polynomial fit & launch angle calculation
│   ├── ground_geometry.py          # Pitch, creases, stumps, 30-yard circle, boundary polygons
│   ├── fielding_model.py           # 11-player tactical formations, presets, format rules
│   ├── outcome_engine.py           # Six, Four, Catch, and In-Play classification
│   └── uncertainty.py              # Monte Carlo dispersion analysis
│
├── models/                         # Typed Pydantic & Dataclass domain models
│   ├── experiment.py               # Experiment metadata, configuration, results, trace
│   ├── ball.py                     # Ball properties & auto-derived values (A, R, I)
│   ├── environment.py              # Atmospheric and turf presets
│   ├── stadium.py                  # Ground geometry & boundary definitions
│   └── fielder.py                  # Fielder definitions, formations, rules
│
├── services/                       # Business logic and persistence
│   ├── experiment_service.py       # Experiment CRUD, SHA-256 fingerprint caching
│   ├── simulation_service.py       # Simulation orchestration, execution, trace capture
│   └── comparison_service.py       # Multi-experiment comparative analytics & RMSE
│
├── visualization/                  # Rendering and video generation
│   ├── multi_angle_video.py        # Broadcast MP4/GIF with multi-angle analytical sequence
│   ├── measurement_guides.py       # Horizontal and vertical analytical dimension lines
│   ├── ground_renderer.py          # 3D matplotlib stadium visualization
│   └── telemetry.py                # Telemetry HUD cards
│
├── backend/                        # FastAPI REST API
│   ├── main.py                     # FastAPI application entrypoint
│   ├── api/
│   │   ├── simulation_api.py       # Run simulation, preview trajectory, trace
│   │   ├── experiments_api.py      # Experiment CRUD, load, duplicate, history
│   │   ├── fielding_api.py         # Fielding presets and validation
│   │   └── comparison_api.py       # Multi-experiment comparison
│   └── static/                     # Web app static assets (Three.js WebGL frontend)
│
├── frontend/                       # Interactive WebGL & Three.js platform
│   ├── index.html                  # Comprehensive Dashboard & Experimentation UI
│   ├── js/
│   │   ├── app.js                  # Frontend application state & API client
│   │   ├── stadium_3d.js           # Three.js 3D cricket stadium & trajectory playback
│   │   ├── fielding_editor.js      # Interactive 11-player fielding placement editor
│   │   └── formula_explorer.js     # Live calculation trace & formula dependency viewer
│   └── css/
│       └── styles.css              # Broadcast-grade dark theme styling
│
├── experiments/                    # Persistent storage for saved experiments
│   └── EXP_.../                    # JSON configs, results, traces, CSVs, and videos
│
└── tests/                          # Automated test suite (Physics, Geometry, API, Persistence)
```

---

## 4. Implementation Phasing Strategy

1. **Step 1: Cleanup & Core Physics Refactoring**:
   - Remove legacy prototypes (`cricket_ball_engine_v0_1.py`, temporary root files).
   - Implement `calculation_trace.py` with first-class step recording.
   - Refactor `physics/` to integrate seamlessly with the calculation trace.
2. **Step 2: Domain Models & Centralized Configuration**:
   - Implement `models/` (Ball, Environment, Stadium, Fielding, Experiment).
   - Add auto-derived physical quantities ($A = \pi D^2/4$, $R = D/2$, $I = \frac{2}{3}mR^2$).
   - Implement turf presets (Natural Grass, Dry Outfield, Wet Outfield, Hard Surface).
3. **Step 3: Fielding Domain Model & Format Rules**:
   - Implement 11-player fielding model with tactical presets (Attacking, Defensive, Powerplay, Middle, Death).
   - Add ICC format restrictions (Test, ODI, T20) with live rule warnings.
4. **Step 4: Persistence, Fingerprinting & Caching Service**:
   - Implement `experiment_service.py` with deterministic SHA-256 fingerprinting.
   - Save complete experiment packages (`experiment.json`, `results.json`, `trajectory.csv`, `calculation_trace.json`).
   - Implement instant cache retrieval without rerunning physics.
5. **Step 5: Multi-Angle Video Generator with Analytical Measurement Guides**:
   - Extend video generator to render the final multi-angle analytical sequence:
     - Side View (vertical arc, initial height, apex height $Z_{max}$, carry $d_1$)
     - Top-Down View (azimuth direction, lateral deflection, boundary rope, fielders)
     - Batsman / Bowler Perspective
     - Isometric Overview
   - Draw explicit horizontal ($d_1, d_{total}$, rope clearance) and vertical ($Z_{max}$) measurement lines.
6. **Step 6: FastAPI Backend & REST Endpoints**:
   - Build REST API (`simulation_api`, `experiments_api`, `fielding_api`, `comparison_api`).
7. **Step 7: Interactive Three.js WebGL Frontend**:
   - Build responsive web dashboard with 3D stadium, trajectory playback timeline, interactive 11-player fielding editor, manual input panel (velocity vs speed/angles), Formula Explorer, Experiment History, and Comparison view.
8. **Step 8: Automated Verification & Sample Demonstration**:
   - Run complete test suite and execute end-to-end sample experiment.

