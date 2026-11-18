# 3D Cricket Ball Trajectory Prediction Engine

A research-informed, modular Python flight simulator and prediction engine for cricket balls. The system estimates physical state from early 3D video coordinate observations, simulates 3D flight trajectories under gravity and aerodynamics, models pitch impact and multi-bounce rolling, evaluates cricket match outcomes (Six, Four, Catch, In-play), and quantifies prediction uncertainty via Monte Carlo ensemble analysis.

---

## 1. Scientific Foundations & References

This engine is grounded in peer-reviewed sports aerodynamics and dynamics literature:

1. **C. J. Baker (2010)**  
   *"A Calculation of Cricket Ball Trajectories"*, *Proc. IMechE Part C: Journal of Mechanical Engineering Science*, 224:1947–1958.  
   - Established numerical Runge-Kutta integration of cricket ball trajectories.
   - Demonstrated that integrating with instantaneous velocity vs. time-averaged velocity yields identical trajectories when drag coefficient $C_d$ and side force coefficient $C_s$ remain relatively constant.
   - Subcritical cricket ball drag coefficient baseline: $C_d \approx 0.30 - 0.35$ (default baseline: $0.32$).
   - Formulated relative air velocity accounting for crosswinds: $\vec{v}_{rel} = \vec{v} - \vec{w}$.

2. **C. J. Baker (2013)**  
   *"A unified framework for the prediction of cricket ball trajectories in spin and swing bowling"*, *Proc. IMechE Part P: Journal of Sports Engineering and Technology*, 227(3):197–209.  
   - Formulated 3D coupled equations of motion separating auto-rotational Magnus forces ($\vec{\omega} \times \vec{v}_{rel}$) from boundary-layer asymmetry forces (conventional/reverse swing).
   - Parameterized Magnus lift coefficient $C_L$ as a function of the non-dimensional spin ratio $S_p = \frac{\omega r}{|\vec{v}_{rel}|}$.

3. **J. M. Banerjee & J. J. McPhee (2012)**  
   *"Simulation of the Three-Dimensional Motion of a Cricket Ball Using a Volumetric Contact Model"*, *Procedia Engineering*, 34:148–153.  
   - Modeled 3D cricket ball impact and bounce mechanics.
   - Ground reaction parameterized by normal coefficient of restitution ($e_n \approx 0.45 - 0.65$ on turf pitches) and tangential Coulomb friction ($\mu_t \approx 0.25 - 0.45$).
   - Ground contact friction torque updates angular velocity $\Delta \vec{\omega} = \frac{\vec{r}_{cp} \times \Delta \vec{p}}{I}$.

4. **S. D. Grimshaw, A. Briggs, & N. R. Atkins (2024)**  
   *"A review and reassessment of the aerodynamics of cricket ball swing"*, *Flow*, Cambridge University Press, 4:E15.  
   - Comprehensive re-evaluation of 70 years of wind tunnel data against Hawkeye match tracking.
   - Identified that the ball seam acts as a discrete vortex generator producing a laminar separation bubble, rather than a simplistic 2D "trip wire".
   - Demonstrated that ambient temperature and air density strongly influence Reynolds number ($Re$), whereas humidity has negligible effect.
   - **Crucial Limitation Highlighted:** Unless seam orientation angle to flow ($\theta_{seam}$) and surface wear condition on both hemispheres are directly measured by high-speed cameras, inventing an arbitrary swing force without measurement is scientifically invalid. Consequently, seam swing forces are encapsulated in a modular interface and **disabled in the baseline engine**.

---

## 2. Coordinate System Convention

The engine uses a right-handed Cartesian coordinate system:
- **$X$-axis**: Longitudinal / Forward downfield towards the bowler or long-off (metres).
- **$Y$-axis**: Lateral across the pitch (metres, positive towards off-side or leg-side depending on orientation).
- **$Z$-axis**: Vertical height above the pitch plane (metres, positive pointing upwards).
- **Ground plane**: At $Z = 0$. Because the ball is a sphere of radius $R = 0.03625$ m, ground contact occurs when the ball centre reaches $Z = R$.

---

## 3. Architecture & Project Structure

```text
cricket_trajectory_engine/
│
├── backend/
│   ├── main.py                # FastAPI server entrypoint (CORS, static mount, API routers)
│   └── api/
│       ├── simulation_api.py  # POST /api/simulation/run
│       ├── experiments_api.py # CRUD, persistent export, video render
│       ├── fielding_api.py    # Presets, format validation rules (T20, ODI, Law 28.4)
│       └── comparison_api.py  # Multi-experiment delta & sensitivity analysis
│
├── core/
│   └── calculation_trace.py   # 9-step structured mathematical explainability trace
│
├── models/
│   ├── ball.py                # BallModel (mass, diameter, R, A, moment of inertia I)
│   ├── environment.py         # EnvironmentModel & turf presets (grass, dry, wet, synthetic)
│   ├── stadium.py             # StadiumModel (circular, elliptical, arbitrary polygon boundary)
│   ├── fielder.py             # FielderModel, FieldingSetupModel, 11-player rule checks
│   └── experiment.py          # ExperimentConfig, ExperimentResult, SHA-256 fingerprinting
│
├── services/
│   ├── simulation_service.py  # Trajectory solver & calculation trace orchestrator
│   ├── experiment_service.py  # Persistent disk storage under experiments/ & cache indexing
│   └── comparison_service.py  # Comparative analysis, baseline deltas & RMSE metrics
│
├── frontend/
│   ├── index.html             # Broadcast-grade interactive web application dashboard
│   ├── css/
│   │   └── styles.css         # Broadcast dark theme styling
│   ├── src/                   # Modern React + Tailwind CSS modular architecture
│   │   ├── components/        # Reusable UI, Layout, Dashboard, 3D Stadium, Inspector, History, Compare
│   │   ├── context/           # Centralized AppContext state management
│   │   ├── services/          # REST API client & tactical presets
│   │   ├── utils/             # Kinematics math, formatters, and trajectory normalizers
│   │   └── styles/            # Tailwind CSS directives, design tokens & KaTeX styles
│   ├── tests/                 # Automated frontend unit tests (Node test runner)
│   ├── package.json           # React 18, Vite 5, Tailwind CSS 3, Three.js, KaTeX
│   └── vite.config.js         # Vite configuration with proxy and production asset pipeline
│
├── physics/                   # Numerical integration (solve_ivp RK45), drag, Magnus, collisions
├── estimation/                # Polynomial trajectory fitting & state estimation
├── prediction/                # Boundary intersection, rope clearance, fielder catching
├── visualization/             # 4-panel analytical multi-view video exporter with dimension guides
└── tests/                     # 37 automated unit and integration tests (100% passing)
```

---

## 4. Setup and Installation

### Prerequisites
- Python 3.9+
- A virtual environment is recommended:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Launching the Interactive 3D Platform

Start the FastAPI application and Three.js WebGL dashboard:

```bash
uvicorn cricket_trajectory_engine.backend.main:app --reload --port 8000
```

Open your browser to:
**`http://127.0.0.1:8000/`** (serves the production React + Tailwind build directly).

### Frontend Development (Vite HMR)

To run the React development server with hot module reloading (HMR) and API proxying:

```bash
cd cricket_trajectory_engine/frontend
npm run dev
```

Open your browser to:
**`http://localhost:5173/`**

To build for production or run frontend tests:

```bash
cd cricket_trajectory_engine/frontend
npm run build   # Compiles production assets into dist/ and bundles index.html
npm test        # Runs frontend math & formatters unit tests
```

---

## 5. Running Tests

Run the full pytest suite (37 tests covering physics, collision, estimation, outcomes, fielding, persistence, and API):

```bash
pytest cricket_trajectory_engine/tests
```

Run the automated pytest suite (23 comprehensive tests):

```bash
pytest -v cricket_trajectory_engine/tests
```

The test suite covers:
1. Exact analytical verification of numerical trajectory against parabolic motion in vacuum ($< 0.05\%$ error).
2. Aerodynamic drag range and apex reduction.
3. Wind relative velocity influence (headwind, tailwind, crosswind).
4. Magnus force directionality (topspin dip, backspin lift, sidespin drift).
5. Numerical integration invariance across step sizes and tolerance thresholds.
6. Coordinate loader boundary and monotonicity checks.
7. Polynomial vs. finite-difference velocity estimation under noise.
8. Trajectory fitting and identifiability warning guards.
9. Ground impact restitution, friction energy dissipation, and angular momentum updates.
10. Cricket outcome rules (Six, Four, Catch interception windows, Missing player data).
11. Monte Carlo reproducibility with fixed random seeds.

---

## 6. Running Demonstrations

To run all phases (Scenarios, Aerodynamic Comparison, Trajectory Fitting, and Monte Carlo Uncertainty):

```bash
python3 main.py --all
```

Or run individual modules:

```bash
# Run the 3 dummy shot scenarios (Low drive, High lofted shot, Lateral cut)
python3 main.py --scenarios

# Run aerodynamic comparison (Vacuum vs Drag vs Magnus Topspin/Backspin)
python3 main.py --compare-aero

# Run initial state estimation and trajectory fitting on dummy observations
python3 main.py --fit

# Run Monte Carlo uncertainty simulation (150 perturbed trajectory runs)
python3 main.py --monte-carlo
```

All generated trajectory CSV files and high-resolution plots are automatically saved in:
`cricket_trajectory_engine/data/generated_trajectories/`

---

## 7. Parameter Identifiability Guardrail

A fundamental scientific principle implemented in this engine:

> **With only a short observation window ($\Delta t < 0.35$ s / 5–10 camera frames), aerodynamic drag and spin coefficients cannot be reliably identified simultaneously.**

Over an interval of $0.1$ s, gravitational acceleration ($g = 9.81$ m/s²) dominates the vertical axis, while aerodynamic deceleration causes velocity changes of only $\Delta v \approx 0.3 - 0.7$ m/s, which is on the same order as tracking coordinate noise ($\sim 1 - 3$ cm). Jointly optimizing initial velocity and $C_d$ on short windows results in severe parameter unidentifiability and overfitting.

Therefore, the engine:
- Defaults to estimating initial velocity $\vec{v}_0$ while holding aerodynamic parameters to validated literature baselines ($C_d = 0.32$).
- Issues an explicit `parameter_identifiability_warning` if joint $C_d$ optimization is attempted on observation windows shorter than $0.35$ s.

---

## 8. Calibration Roadmap for Real Footage

To transition from synthetic dummy data to production match footage:
1. **Camera Calibration:** Perform intrinsic and extrinsic stereo/multiview calibration to establish millimetre-level 3D world coordinates.
2. **Impact Timestamp Synchronization:** Accurately identify the bat-ball separation frame ($t_0$) using audio or contact deformation.
3. **High-Speed Spin Extraction:** Integrate a 250+ fps camera or ball-seam optical flow algorithm to directly estimate $\vec{\omega}$ and seam angle $\theta$.
4. **Trajectory Inversion:** Use observed uninhibited shots with known landing spots to calibrate pitch-specific turf restitution $e_n$ and friction $\mu_t$.

---

## 9. Turnkey Docker Compose Deployment

The complete application, backend solver, 3D WebGL frontend, automated delivery seeding, and test suites are packaged into a single turnkey Docker container.

### Single-Command Build & Run:
```bash
# 1. Build the image with all dependencies and FFmpeg video tools:
docker compose build

# 2. Activate, auto-feed deliveries, verify physics tests, and launch:
docker compose up
```

### Accessing the Web Application:
- Open your browser at **`http://localhost:8000`** (or `http://127.0.0.1:8000`).

### Interactive CLI and Testing via Docker:
```bash
# Run the complete test suite inside the container:
docker compose run app pytest cricket_trajectory_engine/tests/

# Re-seed or verify the 20 real match deliveries inside Docker:
docker compose run app python -m cricket_trajectory_engine.import_real_deliveries

# Open an interactive shell inside the container:
docker compose run app bash
```


