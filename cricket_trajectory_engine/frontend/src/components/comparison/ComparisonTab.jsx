import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import * as api from '../../services/api';
import { Scale, ArrowRight } from 'lucide-react';
import { getOutcomeClass } from '../../utils/formatters';

export default function ComparisonTab() {
  const { allExperiments } = useApp();
  const canvasRef = useRef(null);

  const [idA, setIdA] = useState('');
  const [idB, setIdB] = useState('');
  const [comparisonData, setComparisonData] = useState(null);
  const [isComparing, setIsComparing] = useState(false);

  // Initialize selection and trigger comparison
  useEffect(() => {
    if (allExperiments.length >= 2) {
      const first = allExperiments[0].id || allExperiments[0].experiment_id;
      const second = allExperiments[1].id || allExperiments[1].experiment_id;
      setIdA(first);
      setIdB(second);
      handleCompare(first, second);
    } else if (allExperiments.length === 1) {
      const first = allExperiments[0].id || allExperiments[0].experiment_id;
      setIdA(first);
      setIdB(first);
      handleCompare(first, first);
    }
  }, [allExperiments]);

  // Execute Comparison
  const handleCompare = async (targetA = idA, targetB = idB) => {
    const a = targetA || idA;
    const b = targetB || idB;
    if (!a || !b) {
      alert('Please select both Baseline (A) and Variant (B) experiments.');
      return;
    }

    setIsComparing(true);
    try {
      const data = await api.fetchComparison(a, b);
      setComparisonData(data);
    } catch (err) {
      console.error('Comparison failed:', err);
      alert(`Comparison error: ${err.message}`);
    } finally {
      setIsComparing(false);
    }
  };

  // Draw 2D Trajectory Comparison Chart
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !comparisonData) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#0c1017';
    ctx.fillRect(0, 0, w, h);

    const experiments = comparisonData.experiments || [];
    if (experiments.length === 0) return;

    let maxDist = 20;
    let maxHeight = 4;

    experiments.forEach((exp) => {
      const traj = exp.trajectory || [];
      traj.forEach((pt) => {
        const dist = Math.hypot(pt[1] - traj[0][1], pt[2] - traj[0][2]);
        const z = pt[3];
        if (dist > maxDist) maxDist = dist;
        if (z > maxHeight) maxHeight = z;
      });
    });

    if (maxDist > 45) {
      maxDist = Math.max(maxDist * 1.12, 75);
    } else {
      maxDist = Math.max(maxDist * 1.25, 15);
    }
    maxHeight = Math.max(maxHeight * 1.25, 3.5);

    const leftMargin = 60;
    const rightMargin = 30;
    const topMargin = 55;
    const bottomMargin = 45;
    const chartW = w - leftMargin - rightMargin;
    const chartH = h - topMargin - bottomMargin;
    const groundY = topMargin + chartH;

    // Gridlines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
    ctx.lineWidth = 1;
    ctx.fillStyle = '#64748b';
    ctx.font = '10px Inter, sans-serif';
    ctx.textAlign = 'right';

    const heightStep = maxHeight <= 8 ? 1 : maxHeight <= 18 ? 2 : maxHeight <= 35 ? 5 : 10;
    for (let hz = 0; hz <= maxHeight; hz += heightStep) {
      const y = groundY - (hz / maxHeight) * chartH;
      ctx.beginPath();
      ctx.moveTo(leftMargin, y);
      ctx.lineTo(w - rightMargin, y);
      ctx.stroke();
      ctx.fillText(`${hz}m`, leftMargin - 8, y + 3);
    }

    ctx.textAlign = 'center';
    const distStep = maxDist <= 20 ? 2 : maxDist <= 40 ? 5 : maxDist <= 80 ? 10 : 15;
    for (let dx = 0; dx <= maxDist; dx += distStep) {
      const x = leftMargin + (dx / maxDist) * chartW;
      ctx.beginPath();
      ctx.moveTo(x, topMargin);
      ctx.lineTo(x, groundY);
      ctx.stroke();
      ctx.fillText(`${dx}m`, x, groundY + 16);
    }

    // Ground line
    ctx.strokeStyle = '#2ecc71';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(leftMargin, groundY);
    ctx.lineTo(w - rightMargin, groundY);
    ctx.stroke();

    // 70m Boundary Rope Marker
    if (maxDist >= 70) {
      const ropeX = leftMargin + (70.0 / maxDist) * chartW;
      ctx.setLineDash([4, 4]);
      ctx.strokeStyle = '#f39c12';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(ropeX, topMargin);
      ctx.lineTo(ropeX, groundY);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = '#f39c12';
      ctx.font = 'bold 10px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Boundary Rope (70m)', ropeX, topMargin - 8);
    }

    // Axis Labels
    ctx.save();
    ctx.translate(16, topMargin + chartH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillStyle = '#94a3b8';
    ctx.font = '11px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Height Above Turf (m)', 0, 0);
    ctx.restore();

    ctx.fillStyle = '#94a3b8';
    ctx.font = '11px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Downfield Flight Distance (m)', leftMargin + chartW / 2, h - 10);

    const colors = ['#00b4d8', '#f5a623', '#9b5de5'];

    // Render Trajectories
    experiments.forEach((exp, idx) => {
      const traj = exp.trajectory || [];
      if (traj.length < 2) return;

      const color = colors[idx % colors.length];
      ctx.strokeStyle = color;
      ctx.lineWidth = 2.8;
      ctx.beginPath();

      let apexPt = traj[0];
      let apexHeight = -1;

      traj.forEach((pt, i) => {
        const dist = Math.hypot(pt[1] - traj[0][1], pt[2] - traj[0][2]);
        const height = Math.max(0, pt[3]);
        if (height > apexHeight) {
          apexHeight = height;
          apexPt = pt;
        }

        const px = leftMargin + (dist / maxDist) * chartW;
        const py = groundY - (height / maxHeight) * chartH;
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      });
      ctx.stroke();

      // Apex Marker
      if (apexPt) {
        const aDist = Math.hypot(apexPt[1] - traj[0][1], apexPt[2] - traj[0][2]);
        const aX = leftMargin + (aDist / maxDist) * chartW;
        const aY = groundY - (apexHeight / maxHeight) * chartH;

        ctx.beginPath();
        ctx.arc(aX, aY, 4.5, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        ctx.fillStyle = color;
        ctx.font = 'bold 10px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(`Apex: ${apexHeight.toFixed(2)}m`, aX, Math.max(topMargin + 12, aY - 7));
      }

      // Legend
      const expOutcome = exp.summary?.outcome || exp.results?.outcome_call || 'IN_PLAY';
      const expTotalDist = exp.summary?.total_distance_m || exp.results?.total_distance_m || 0;
      const legendLabel = `${idx === 0 ? '[A] ' : '[B] '}${exp.name} (${expOutcome}, ${Number(expTotalDist || 0).toFixed(1)}m)`;

      ctx.textAlign = 'left';
      const legX = leftMargin + idx * 340;
      ctx.fillStyle = color;
      ctx.fillRect(legX, 16, 12, 12);
      ctx.fillStyle = '#e2e8f0';
      ctx.font = 'bold 11px Inter, sans-serif';
      ctx.fillText(legendLabel, legX + 18, 26);
    });
  }, [comparisonData]);

  // Delta calculations
  const tableData = comparisonData?.comparison_table || [];
  const base = tableData.find((e) => e.experiment_id === idA) || tableData[0];
  const comp = tableData.find((e) => e.experiment_id === idB) || (tableData.length > 1 ? tableData[1] : base);

  let delta = null;
  if (comparisonData) {
    if (comparisonData.deltas_map && comparisonData.deltas_map[idB]) {
      delta = comparisonData.deltas_map[idB];
    } else if (Array.isArray(comparisonData.deltas_vs_baseline)) {
      delta = comparisonData.deltas_vs_baseline.find((d) => d.experiment_id === idB) || comparisonData.deltas_vs_baseline[1] || comparisonData.deltas_vs_baseline[0];
    }
  }

  const deltaApex = delta?.delta_apex_m !== undefined ? delta.delta_apex_m : (delta?.delta_max_height_m || 0);
  const deltaTime = delta?.delta_flight_time_s !== undefined ? delta.delta_flight_time_s : 0;
  const deltaDist = delta?.delta_total_dist_m !== undefined ? delta.delta_total_dist_m : (delta?.delta_horizontal_distance_m !== undefined ? delta.delta_horizontal_distance_m : (delta?.delta_carry_m || 0));
  const baseOutcome = delta?.baseline_outcome || base?.outcome_call || 'IN_PLAY';
  const compOutcome = delta?.comparison_outcome || comp?.outcome_call || baseOutcome;

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Selector Card */}
      <div className="card p-6 border border-border-color bg-bg-card rounded-xl space-y-4">
        <div className="flex justify-between items-center pb-3 border-b border-border-color">
          <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
            <span>⚖️</span> Multi-Experiment Delta & Sensitivity Analysis
          </h3>
          <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-accent-primary/10 text-accent-primary border border-accent-primary/20">
            Comparative Physics
          </span>
        </div>

        <p className="text-xs text-text-secondary leading-relaxed">
          Select two saved experiments to compare trajectories, physical influence of parameter changes, and outcome deltas:
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 items-end">
          <div>
            <label className="block text-xs font-semibold text-accent-cyan mb-1.5 uppercase tracking-wide">
              Baseline Experiment (A)
            </label>
            <select
              value={idA}
              onChange={(e) => {
                const val = e.target.value;
                setIdA(val);
                handleCompare(val, idB);
              }}
              className="form-control w-full bg-bg-primary text-text-primary border-border-color py-2 px-3 rounded-md text-xs font-medium"
            >
              {allExperiments.map((exp) => (
                <option key={exp.id || exp.experiment_id} value={exp.id || exp.experiment_id}>
                  {exp.name || exp.id} ({exp.outcome_call || 'IN_PLAY'})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-accent-gold mb-1.5 uppercase tracking-wide">
              Variant Experiment (B)
            </label>
            <select
              value={idB}
              onChange={(e) => {
                const val = e.target.value;
                setIdB(val);
                handleCompare(idA, val);
              }}
              className="form-control w-full bg-bg-primary text-text-primary border-border-color py-2 px-3 rounded-md text-xs font-medium"
            >
              {allExperiments.map((exp) => (
                <option key={exp.id || exp.experiment_id} value={exp.id || exp.experiment_id}>
                  {exp.name || exp.id} ({exp.outcome_call || 'IN_PLAY'})
                </option>
              ))}
            </select>
          </div>

          <button
            disabled={isComparing}
            onClick={() => handleCompare(idA, idB)}
            className="btn btn-primary text-xs py-2.5 px-4 flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <Scale className="w-4 h-4" />
            <span>{isComparing ? 'Comparing...' : 'Compare Trajectories'}</span>
          </button>
        </div>
      </div>

      {/* Results Panel */}
      {comparisonData && (
        <div className="space-y-6">
          {/* Summary Delta Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="card p-4 border border-border-color bg-bg-card rounded-xl">
              <div className="text-[11px] font-medium text-text-secondary uppercase tracking-wider">
                Δ Apex Height
              </div>
              <div className={`text-2xl font-extrabold mt-1 font-mono ${
                deltaApex > 0.05 ? 'text-accent-cyan' : deltaApex < -0.05 ? 'text-accent-red' : 'text-accent-gold'
              }`}>
                {deltaApex >= 0 ? '+' : ''}{deltaApex.toFixed(2)} m
              </div>
            </div>

            <div className="card p-4 border border-border-color bg-bg-card rounded-xl">
              <div className="text-[11px] font-medium text-text-secondary uppercase tracking-wider">
                Δ Flight Time
              </div>
              <div className={`text-2xl font-extrabold mt-1 font-mono ${
                deltaTime > 0.05 ? 'text-accent-cyan' : deltaTime < -0.05 ? 'text-accent-red' : 'text-accent-gold'
              }`}>
                {deltaTime >= 0 ? '+' : ''}{deltaTime.toFixed(2)} s
              </div>
            </div>

            <div className="card p-4 border border-border-color bg-bg-card rounded-xl">
              <div className="text-[11px] font-medium text-text-secondary uppercase tracking-wider">
                Δ Total Carry Distance
              </div>
              <div className={`text-2xl font-extrabold mt-1 font-mono ${
                deltaDist > 0.05 ? 'text-accent-green' : deltaDist < -0.05 ? 'text-accent-red' : 'text-accent-gold'
              }`}>
                {deltaDist >= 0 ? '+' : ''}{deltaDist.toFixed(2)} m
              </div>
            </div>

            <div className="card p-4 border border-border-color bg-bg-card rounded-xl">
              <div className="text-[11px] font-medium text-text-secondary uppercase tracking-wider">
                Outcome Shift
              </div>
              <div className="text-sm font-bold mt-2 flex items-center gap-1.5 flex-wrap">
                <span className="text-accent-cyan">{baseOutcome}</span>
                <ArrowRight className="w-3.5 h-3.5 text-text-muted" />
                <span className="text-accent-gold">{compOutcome}</span>
              </div>
            </div>
          </div>

          {/* 2D Trajectory Comparison Canvas */}
          <div className="card p-5 border border-border-color bg-bg-card rounded-xl">
            <div className="flex justify-between items-center pb-3 border-b border-border-color mb-3">
              <h3 className="text-sm font-bold text-text-primary flex items-center gap-2">
                <span>📊</span> 2D Flight Trajectory Comparison (Height vs Distance)
              </h3>
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-sky-500/10 text-accent-cyan border border-sky-500/20">
                Apex & Landing Overlay
              </span>
            </div>
            <div className="overflow-x-auto">
              <canvas
                ref={canvasRef}
                width={900}
                height={340}
                className="w-full h-auto rounded-lg border border-border-color"
              />
            </div>
          </div>

          {/* Side-by-Side Parameter Table */}
          {base && comp && (
            <div className="card p-5 border border-border-color bg-bg-card rounded-xl">
              <div className="flex justify-between items-center pb-3 border-b border-border-color mb-3">
                <h3 className="text-sm font-bold text-text-primary flex items-center gap-2">
                  <span>📋</span> Side-by-Side Parameter & Metric Comparison Table
                </h3>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-accent-green border border-emerald-500/20">
                  Physics Delta Breakdown
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-border-color bg-bg-secondary text-text-muted font-mono uppercase text-[11px]">
                      <th className="py-2.5 px-3 min-w-[180px]">Parameter / Metric</th>
                      <th className="py-2.5 px-3 min-w-[150px] text-accent-cyan">
                        Baseline [A]: {base.name || base.experiment_id}
                      </th>
                      <th className="py-2.5 px-3 min-w-[150px] text-accent-gold">
                        Variant [B]: {comp.name || comp.experiment_id}
                      </th>
                      <th className="py-2.5 px-3 min-w-[120px] text-accent-gold">Delta (B - A)</th>
                      <th className="py-2.5 px-3 min-w-[240px]">Physical Sensitivity / Governing Principle</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-color/40">
                    {[
                      {
                        metric: 'Launch Speed v₀',
                        valA: `${base.launch_speed_kmh.toFixed(1)} km/h`,
                        valB: `${comp.launch_speed_kmh.toFixed(1)} km/h`,
                        delta: `${(comp.launch_speed_kmh - base.launch_speed_kmh) >= 0 ? '+' : ''}${(comp.launch_speed_kmh - base.launch_speed_kmh).toFixed(1)} km/h`,
                        deltaNum: comp.launch_speed_kmh - base.launch_speed_kmh,
                        explanation: 'Initial exit kinetic energy: E_k = 0.5 · m · v₀²',
                      },
                      {
                        metric: 'Launch Elevation θ',
                        valA: `${base.elevation_deg.toFixed(1)}°`,
                        valB: `${comp.elevation_deg.toFixed(1)}°`,
                        delta: `${(comp.elevation_deg - base.elevation_deg) >= 0 ? '+' : ''}${(comp.elevation_deg - base.elevation_deg).toFixed(1)}°`,
                        deltaNum: comp.elevation_deg - base.elevation_deg,
                        explanation: 'Vertical launch angle: higher angle trades horizontal penetration for apex height & hang time',
                      },
                      {
                        metric: 'Launch Azimuth φ',
                        valA: `${base.azimuth_deg.toFixed(1)}°`,
                        valB: `${comp.azimuth_deg.toFixed(1)}°`,
                        delta: `${(comp.azimuth_deg - base.azimuth_deg) >= 0 ? '+' : ''}${(comp.azimuth_deg - base.azimuth_deg).toFixed(1)}°`,
                        deltaNum: comp.azimuth_deg - base.azimuth_deg,
                        explanation: 'Horizontal spray angle: positive is Off-side (+Y), negative is Leg-side (-Y)',
                      },
                      {
                        metric: 'Apex Peak Height',
                        valA: `${base.apex_height_m.toFixed(2)} m`,
                        valB: `${comp.apex_height_m.toFixed(2)} m`,
                        delta: `${(comp.apex_height_m - base.apex_height_m) >= 0 ? '+' : ''}${(comp.apex_height_m - base.apex_height_m).toFixed(2)} m`,
                        deltaNum: comp.apex_height_m - base.apex_height_m,
                        explanation: 'Maximum vertical altitude achieved during flight trajectory',
                      },
                      {
                        metric: 'Flight / Hang Time',
                        valA: `${base.flight_time_s.toFixed(2)} s`,
                        valB: `${comp.flight_time_s.toFixed(2)} s`,
                        delta: `${(comp.flight_time_s - base.flight_time_s) >= 0 ? '+' : ''}${(comp.flight_time_s - base.flight_time_s).toFixed(2)} s`,
                        deltaNum: comp.flight_time_s - base.flight_time_s,
                        explanation: 'Airborne duration from bat contact to initial ground pitch',
                      },
                      {
                        metric: 'Carry Distance (1st Impact)',
                        valA: `${base.carry_distance_m.toFixed(2)} m`,
                        valB: `${comp.carry_distance_m.toFixed(2)} m`,
                        delta: `${(comp.carry_distance_m - base.carry_distance_m) >= 0 ? '+' : ''}${(comp.carry_distance_m - base.carry_distance_m).toFixed(2)} m`,
                        deltaNum: comp.carry_distance_m - base.carry_distance_m,
                        explanation: 'Radial horizontal carry distance to initial pitch collision',
                      },
                      {
                        metric: 'Total Trajectory Distance',
                        valA: `${base.total_distance_m.toFixed(2)} m`,
                        valB: `${comp.total_distance_m.toFixed(2)} m`,
                        delta: `${(comp.total_distance_m - base.total_distance_m) >= 0 ? '+' : ''}${(comp.total_distance_m - base.total_distance_m).toFixed(2)} m`,
                        deltaNum: comp.total_distance_m - base.total_distance_m,
                        explanation: 'Net distance traversed from striker to final rest or boundary rope crossing',
                      },
                      {
                        metric: 'Umpire Outcome Call',
                        valA: base.outcome_call,
                        valB: comp.outcome_call,
                        delta: base.outcome_call === comp.outcome_call ? 'Unchanged' : 'Shifted',
                        deltaNum: 0,
                        explanation: 'Final adjudicated match outcome (SIX, FOUR, CATCH, IN_PLAY)',
                      },
                    ].map((row, idx) => {
                      const deltaColor = row.deltaNum > 0.001
                        ? 'text-accent-green'
                        : row.deltaNum < -0.001
                        ? 'text-accent-red'
                        : 'text-text-secondary';

                      return (
                        <tr key={idx} className="hover:bg-bg-secondary/40 transition-colors">
                          <td className="py-2.5 px-3 font-semibold text-text-primary">{row.metric}</td>
                          <td className="py-2.5 px-3 font-mono text-accent-cyan">{row.valA}</td>
                          <td className="py-2.5 px-3 font-mono text-accent-gold">{row.valB}</td>
                          <td className={`py-2.5 px-3 font-mono font-bold ${deltaColor}`}>{row.delta}</td>
                          <td className="py-2.5 px-3 text-text-muted">{row.explanation}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

