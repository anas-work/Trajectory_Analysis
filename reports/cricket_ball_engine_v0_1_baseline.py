Created At: 2026-11-05T13:18:48+05:30
Completed At: 2026-11-05T13:18:48+05:30
Showing lines 1-236 of 236
1: 
2: """
3: Cricket Ball Flight Engine - Prototype v0.1
4: ------------------------------------------
5: A research-inspired, deliberately simplified 3D flight simulator.
6: 
7: Coordinate convention:
8:     X = forward/downfield (m)
9:     Y = lateral (m)
10:     Z = vertical (m), positive upwards
11:     Ground plane = Z = 0; ball centre contacts ground at Z = radius.
12: 
13: Included:
14:     - Gravity
15:     - Quadratic aerodynamic drag
16:     - Optional constant wind
17:     - Optional simplified Magnus lift (requires a supplied spin vector and CL)
18:     - Numerical integration with scipy.solve_ivp
19:     - Ground-contact event and landing statistics
20: 
21: Not included yet:
22:     - Seam-resolved swing / reverse swing
23:     - Reynolds-dependent measured coefficient curves
24:     - Bat impact mechanics
25:     - Bounce / friction / rolling after impact
26:     - Fielders, boundary rules, running or outcome classification
27: 
28: This is a prototype, not a validated match-prediction engine.
29: """
30: 
31: from dataclasses import dataclass
32: import csv
33: import numpy as np
34: from scipy.integrate import solve_ivp
35: import matplotlib.pyplot as plt
36: 
37: 
38: @dataclass
39: class Ball:
40:     mass_kg: float = 0.160
41:     diameter_m: float = 0.0725
42: 
43:     @property
44:     def radius_m(self):
45:         return self.diameter_m / 2.0
46: 
47:     @property
48:     def area_m2(self):
49:         return np.pi * self.radius_m ** 2
50: 
51: 
52: @dataclass
53: class Environment:
54:     air_density_kg_m3: float = 1.225
55:     gravity_m_s2: float = 9.80665
56:     wind_m_s: tuple = (0.0, 0.0, 0.0)
57: 
58: 
59: @dataclass
60: class Aero:
61:     cd: float = 0.32
62:     # Set magnus_cl=0 for the baseline. Nonzero values are illustrative
63:     # unless calibrated against measured cricket-ball data.
64:     magnus_cl: float = 0.0
65:     # Angular velocity vector in rad/s, in world coordinates.
66:     spin_rad_s: tuple = (0.0, 0.0, 0.0)
67: 
68: 
69: def rhs(t, state, ball, env, aero):
70:     """State = [x,y,z,vx,vy,vz]."""
71:     pos = state[:3]
72:     vel = state[3:]
73: 
74:     wind = np.asarray(env.wind_m_s, dtype=float)
75:     spin = np.asarray(aero.spin_rad_s, dtype=float)
76:     v_rel = vel - wind
77:     speed_rel = np.linalg.norm(v_rel)
78: 
79:     gravity = np.array([0.0, 0.0, -env.gravity_m_s2])
80: 
81:     if speed_rel > 1e-9:
82:         drag_force = (
83:             -0.5 * env.air_density_kg_m3 * aero.cd * ball.area_m2
84:             * speed_rel * v_rel
85:         )
86:     else:
87:         drag_force = np.zeros(3)
88: 
89:     magnus_force = np.zeros(3)
90:     spin_norm = np.linalg.norm(spin)
91:     if aero.magnus_cl != 0.0 and spin_norm > 1e-9 and speed_rel > 1e-9:
92:         # Direction follows spin x relative-velocity. The coefficient is
93:         # an explicit simplified input, not a universal cricket-ball constant.
94:         lift_direction = np.cross(spin, v_rel)
95:         lift_norm = np.linalg.norm(lift_direction)
96:         if lift_norm > 1e-9:
97:             lift_direction /= lift_norm
98:             magnus_force = (
99:                 0.5 * env.air_density_kg_m3 * ball.area_m2
100:                 * aero.magnus_cl * speed_rel**2 * lift_direction
101:             )
102: 
103:     acceleration = gravity + (drag_force + magnus_force) / ball.mass_kg
104:     return np.concatenate((vel, acceleration))
105: 
106: 
107: def ground_contact(t, state, ball, env, aero):
108:     # Stop when the ball centre reaches one radius above the ground.
109:     return state[2] - ball.radius_m
110: 
111: ground_contact.terminal = True
112: ground_contact.direction = -1
113: 
114: 
115: def simulate(initial_position_m, initial_velocity_m_s,
116:              ball=None, env=None, aero=None, max_time_s=15.0):
117:     ball = ball or Ball()
118:     env = env or Environment()
119:     aero = aero or Aero()
120: 
121:     y0 = np.concatenate((
122:         np.asarray(initial_position_m, dtype=float),
123:         np.asarray(initial_velocity_m_s, dtype=float)
124:     ))
125: 
126:     if y0[2] <= ball.radius_m:
127:         raise ValueError("Initial ball-centre height must be above the ground.")
128: 
129:     sol = solve_ivp(
130:         rhs,
131:         t_span=(0.0, max_time_s),
132:         y0=y0,
133:         args=(ball, env, aero),
134:         events=ground_contact,
135:         dense_output=False,
136:         max_step=0.01,
137:         rtol=1e-8,
138:         atol=1e-10
139:     )
140: 
141:     states = sol.y.T
142:     times = sol.t
143:     positions = states[:, :3]
144:     velocities = states[:, 3:]
145: 
146:     landing = None
147:     if len(sol.t_events[0]) > 0:
148:         landing_state = sol.y_events[0][0]
149:         landing = {
150:             "time_s": float(sol.t_events[0][0]),
151:             "position_m": landing_state[:3].tolist(),
152:             "velocity_m_s": landing_state[3:].tolist(),
153:             "horizontal_range_m": float(np.linalg.norm(landing_state[:2] - y0[:2]))
154:         }
155: 
156:     return {
157:         "time_s": times,
158:         "state": states,
159:         "positions_m": positions,
160:         "velocities_m_s": velocities,
161:         "landing": landing,
162:         "max_height_m": float(np.max(positions[:, 2])),
163:         "initial_speed_m_s": float(np.linalg.norm(y0[3:])),
164:         "initial_position_m": y0[:3].tolist(),
165:         "initial_velocity_m_s": y0[3:].tolist(),
166:         "solver_success": bool(sol.success),
167:         "solver_message": sol.message
168:     }
169: 
170: 
171: def save_csv(result, filename="trajectory_dummy.csv"):
172:     with open(filename, "w", newline="") as f:
173:         writer = csv.writer(f)
174:         writer.writerow(["time_s", "x_m", "y_m", "z_m",
175:                          "vx_m_s", "vy_m_s", "vz_m_s"])
176:         for t, s in zip(result["time_s"], result["state"]):
177:             writer.writerow([t, *s])
178: 
179: 
180: def plot_trajectory(result, filename="trajectory_dummy.png"):
181:     p = result["positions_m"]
182: 
183:     fig = plt.figure(figsize=(12, 5))
184:     ax = fig.add_subplot(1, 2, 1, projection="3d")
185:     ax.plot(p[:, 0], p[:, 1], p[:, 2], linewidth=2)
186:     ax.scatter([p[0, 0]], [p[0, 1]], [p[0, 2]], marker="o", label="Launch")
187:     if result["landing"] is not None:
188:         lp = result["landing"]["position_m"]
189:         ax.scatter([lp[0]], [lp[1]], [lp[2]], marker="x", s=70, label="Ground contact")
190:     ax.set_xlabel("X forward (m)")
191:     ax.set_ylabel("Y lateral (m)")
192:     ax.set_zlabel("Z height (m)")
193:     ax.set_title("3D cricket-ball flight")
194:     ax.legend()
195: 
196:     ax2 = fig.add_subplot(1, 2, 2)
197:     ax2.plot(p[:, 0], p[:, 2], linewidth=2)
198:     ax2.set_xlabel("X forward (m)")
199:     ax2.set_ylabel("Z height (m)")
200:     ax2.set_title("Side-view trajectory")
201:     ax2.grid(True, alpha=0.3)
202: 
203:     fig.tight_layout()
204:     fig.savefig(filename, dpi=160)
205:     plt.close(fig)
206: 
207: 
208: if __name__ == "__main__":
209:     # SIMULATED DUMMY INPUTS ONLY - replace with measured 3D state later.
210:     initial_position = (0.0, 0.0, 1.0)       # metres
211:     initial_velocity = (30.0, 2.0, 15.0)    # m/s: forward, lateral, vertical
212: 
213:     ball = Ball(mass_kg=0.160, diameter_m=0.0725)
214:     env = Environment(
215:         air_density_kg_m3=1.225,
216:         gravity_m_s2=9.80665,
217:         wind_m_s=(0.0, 0.0, 0.0)
218:     )
219:     aero = Aero(cd=0.32, magnus_cl=0.0, spin_rad_s=(0.0, 0.0, 0.0))
220: 
221:     result = simulate(initial_position, initial_velocity, ball, env, aero)
222:     save_csv(result)
223:     plot_trajectory(result)
224: 
225:     print("CRICKET BALL FLIGHT ENGINE - PROTOTYPE v0.1")
226:     print("Solver:", result["solver_success"], result["solver_message"])
227:     print(f"Initial speed: {result['initial_speed_m_s']:.2f} m/s")
228:     print(f"Maximum height: {result['max_height_m']:.2f} m")
229:     if result["landing"]:
230:         print(f"Flight time: {result['landing']['time_s']:.3f} s")
231:         print("Landing position (x,y,z) m:",
232:               tuple(round(v, 3) for v in result["landing"]["position_m"]))
233:         print(f"Horizontal range: {result['landing']['horizontal_range_m']:.2f} m")
234:     else:
235:         print("No ground contact within simulation time.")
236:     print("Wrote trajectory_dummy.csv and trajectory_dummy.png")