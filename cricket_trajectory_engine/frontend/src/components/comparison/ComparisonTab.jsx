import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import * as api from '../../services/api';
import { Scale, ArrowRight, ZoomIn, Layers, AlertCircle, Compass } from 'lucide-react';
import { getOutcomeClass } from '../../utils/formatters';

const TRAJ_COLORS = [
  { stroke: '#00e5ff', bg: 'rgba(0, 229, 255, 0.15)', name: 'Electric Cyan' },
  { stroke: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', name: 'Radiant Amber' },
  { stroke: '#ec4899', bg: 'rgba(236, 72, 153, 0.15)', name: 'Hot Pink' },
  { stroke: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', name: 'Emerald Green' },
];

export default function ComparisonTab() {
  const { allExperiments } = useApp();
  const canvasRef = useRef(null);

  const [idA, setIdA] = useState('');
  const [idB, setIdB] = useState('');
  const [idC, setIdC] = useState('');
  const [comparisonData, setComparisonData] = useState(null);
  const [isComparing, setIsComparing] = useState(false);
  const [zoomMode, setZoomMode] = useState('full'); // 'full' | 'launch' | 'impact'

  // Initialize selection
  useEffect(() => {
    if (allExperiments.length >= 2) {
      const first = allExperiments[0].id || allExperiments[0].experiment_id;
      const second = allExperiments[1].id || allExperiments[1].experiment_id;
      setIdA(first);
      setIdB(second);
      handleCompare([first, second]);
    } else if (allExperiments.length === 1) {
      const first = allExperiments[0].id || allExperiments[0].experiment_id;
      setIdA(first);
      setIdB(first);
      handleCompare([first, first]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allExperiments]);

  // Execute Comparison
  const handleCompare = async (idsToCompare = null) => {
    let ids = idsToCompare;
    if (!ids) {
      ids = [idA, idB];
      if (idC && idC !== 'none') ids.push(idC);
    }
    const cleanIds = ids.filter((x) => Boolean(x) && x !== 'none');
    if (cleanIds.length < 2) {
      alert('Please select at least Baseline (A) and Variant (B) experiments.');
      return;
    }

    setIsComparing(true);
    try {
      const data = await api.fetchComparison(cleanIds, cleanIds[0]);
      setComparisonData(data);
    } catch (err) {
      console.error('Comparison failed:', err);
      alert(`Comparison error: ${err.message}`);
    } finally {
      setIsComparing(false);
    }
  };

  // ── Render High-Precision 2D Trajectory Comparison Chart ───────────────────
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !comparisonData) return;
    const ctx = canvas.getContext('2d');

    const dpr = window.devicePixelRatio || 1;
    const clientW = canvas.parentElement?.clientWidth || 900;
    const clientH = 460;
    canvas.width = clientW * dpr;
    canvas.height = clientH * dpr;
    canvas.style.width = `${clientW}px`;
    canvas.style.height = `${clientH}px`;
    ctx.scale(dpr, dpr);

    const w = clientW;
    const h = clientH;

    // Dark technical backdrop
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#06090e';
    ctx.fillRect(0, 0, w, h);

    const experiments = comparisonData.experiments || [];
    if (experiments.length === 0) return;

    // Determine Unified Scale Boundaries (DO NOT RESCALE INDEPENDENTLY)
    let domainDistMin = 0;
    let domainDistMax = 85;
    let domainHeightMax = 25;

    // Calculate maximums across all compared experiments to ensure unified scale
    let maxFlightDist = 20;
    let maxFlightHeight = 5;

    experiments.forEach((exp) => {
      const traj = exp.trajectory || [];
      traj.forEach((pt) => {
        const dist = Math.hypot(pt[1] - traj[0][1], pt[2] - traj[0][2]);
        const z = pt[3] || 0;
        if (dist > maxFlightDist) maxFlightDist = dist;
        if (z > maxFlightHeight) maxFlightHeight = z;
      });
    });

    if (zoomMode === 'launch') {
      domainDistMin = 0;
      domainDistMax = 16;
      domainHeightMax = Math.max(8, maxFlightHeight * 0.55);
    } else if (zoomMode === 'impact') {
      domainDistMin = Math.max(0, maxFlightDist - 30);
      domainDistMax = maxFlightDist + 15;
      domainHeightMax = Math.max(10, maxFlightHeight * 0.65);
    } else {
      domainDistMin = 0;
      domainDistMax = Math.max(75, maxFlightDist * 1.12);
      domainHeightMax = Math.max(15, maxFlightHeight * 1.25);
    }

    const leftMargin = 65;
    const rightMargin = 40;
    const topMargin = 60;
    const bottomMargin = 50;
    const chartW = w - leftMargin - rightMargin;
    const chartH = h - topMargin - bottomMargin;
    const groundY = topMargin + chartH;

    const toCanvasX = (dist) => leftMargin + ((dist - domainDistMin) / (domainDistMax - domainDistMin)) * chartW;
    const toCanvasY = (height) => groundY - (height / domainHeightMax) * chartH;

    // ── Metric Gridlines ─────────────────────────────────────────────────────
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.07)';
    ctx.lineWidth = 1;
    ctx.fillStyle = '#64748b';
    ctx.font = '10px "JetBrains Mono", Inter, sans-serif';

    // Vertical Height Grid (Horizontal lines)
    const hStep = domainHeightMax <= 10 ? 1 : domainHeightMax <= 20 ? 2 : 5;
    ctx.textAlign = 'right';
    for (let hz = 0; hz <= domainHeightMax; hz += hStep) {
      const y = toCanvasY(hz);
      ctx.beginPath();
      ctx.moveTo(leftMargin, y);
      ctx.lineTo(w - rightMargin, y);
      ctx.stroke();
      ctx.fillText(`${hz}m`, leftMargin - 10, y + 3.5);
    }

    // Horizontal Distance Grid (Vertical lines)
    const dSpan = domainDistMax - domainDistMin;
    const dStep = dSpan <= 20 ? 2 : dSpan <= 50 ? 5 : 10;
    ctx.textAlign = 'center';
    for (let dx = Math.ceil(domainDistMin / dStep) * dStep; dx <= domainDistMax; dx += dStep) {
      const x = toCanvasX(dx);
      ctx.beginPath();
      ctx.moveTo(x, topMargin);
      ctx.lineTo(x, groundY);
      ctx.stroke();
      ctx.fillText(`${dx}m`, x, groundY + 18);
    }

    // ── Solid Pitch Ground Line ──────────────────────────────────────────────
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(leftMargin, groundY);
    ctx.lineTo(w - rightMargin, groundY);
    ctx.stroke();

    // ── Boundary Rope at 70m Marker ──────────────────────────────────────────
    if (domainDistMin <= 70 && domainDistMax >= 70) {
      const ropeX = toCanvasX(70.0);
      ctx.setLineDash([5, 4]);
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 1.8;
      ctx.beginPath();
      ctx.moveTo(ropeX, topMargin);
      ctx.lineTo(ropeX, groundY);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = '#f59e0b';
      ctx.font = 'bold 10px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Boundary Rope (70m)', ropeX, topMargin - 8);
    }

    // ── Axis Titles ──────────────────────────────────────────────────────────
    ctx.save();
    ctx.translate(20, topMargin + chartH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillStyle = '#94a3b8';
    ctx.font = 'bold 11px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Altitude / Height Above Turf (m)', 0, 0);
    ctx.restore();

    ctx.fillStyle = '#94a3b8';
    ctx.font = 'bold 11px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Downfield Flight Distance From Crease (m)', leftMargin + chartW / 2, h - 14);

    // ── Detect Divergence Point (Between Exp 0 and Exp 1) ─────────────────────
    let divergencePoint = null;
    if (experiments.length >= 2) {
      const trajA = experiments[0].trajectory || [];
      const trajB = experiments[1].trajectory || [];
      const minLen = Math.min(trajA.length, trajB.length);

      for (let i = 0; i < minLen; i++) {
        const ptA = trajA[i];
        const ptB = trajB[i];
        const distA = Math.hypot(ptA[1] - trajA[0][1], ptA[2] - trajA[0][2]);
        const distB = Math.hypot(ptB[1] - trajB[0][1], ptB[2] - trajB[0][2]);
        const dz = Math.abs((ptA[3] || 0) - (ptB[3] || 0));
        const dHoriz = Math.abs(distA - distB);

        // Divergence threshold: 0.15m separation
        if (dz > 0.15 || dHoriz > 0.25) {
          divergencePoint = {
            dist: (distA + distB) / 2,
            height: ((ptA[3] || 0) + (ptB[3] || 0)) / 2,
            dz: dz,
          };
          break;
        }
      }
    }

    // ── Render Trajectory Curves & Analytical Milestones ─────────────────────
    experiments.forEach((exp, idx) => {
      const traj = exp.trajectory || [];
      if (traj.length < 2) return;

      const col = TRAJ_COLORS[idx % TRAJ_COLORS.length];
      const color = col.stroke;

      // Extract launch kinematics
      const pt0 = traj[0];
      const vx0 = pt0[4] || 0, vy0 = pt0[5] || 0, vz0 = pt0[6] || 0;
      const vxy = Math.hypot(vx0, vy0);
      const elevDeg = Math.atan2(vz0, Math.max(1e-6, vxy)) * (180 / Math.PI);
      const speedKmh = Math.hypot(vxy, vz0) * 3.6;

      ctx.strokeStyle = color;
      ctx.lineWidth = 3.0;
      ctx.beginPath();

      let apexPt = traj[0];
      let apexHeight = -1;
      let firstImpactDist = null;

      traj.forEach((pt, i) => {
        const dist = Math.hypot(pt[1] - pt0[1], pt[2] - pt0[2]);
        const height = Math.max(0, pt[3] || 0);

        if (height > apexHeight) {
          apexHeight = height;
          apexPt = pt;
        }

        // Check first impact landing
        if (firstImpactDist === null && i > 0 && (pt[7] === 2 || (height <= 0.05 && i > 5))) {
          firstImpactDist = dist;
        }

        const px = toCanvasX(dist);
        const py = toCanvasY(height);

        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      });
      ctx.stroke();

      // Fallback first impact distance from metrics
      if (firstImpactDist === null) {
        firstImpactDist = Number(exp.summary?.carry_distance_m || exp.results?.carry_distance_m || 0);
      }

      // Launch Angle Ray (First 5m)
      if (zoomMode === 'launch' || zoomMode === 'full') {
        const rayLen = zoomMode === 'launch' ? 6 : 4;
        const rad = (elevDeg * Math.PI) / 180;
        const rx = toCanvasX(rayLen * Math.cos(rad));
        const ry = toCanvasY(0.9 + rayLen * Math.sin(rad));

        ctx.strokeStyle = color;
        ctx.setLineDash([3, 3]);
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(toCanvasX(0), toCanvasY(0.9));
        ctx.lineTo(rx, ry);
        ctx.stroke();
        ctx.setLineDash([]);

        // Elevation angle label
        ctx.fillStyle = color;
        ctx.font = 'bold 10px "JetBrains Mono", sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText(`θ=${elevDeg.toFixed(1)}° (${speedKmh.toFixed(0)} km/h)`, rx + 4, ry - 3);
      }

      // Apex Marker
      if (apexPt) {
        const aDist = Math.hypot(apexPt[1] - pt0[1], apexPt[2] - pt0[2]);
        if (aDist >= domainDistMin && aDist <= domainDistMax) {
          const aX = toCanvasX(aDist);
          const aY = toCanvasY(apexHeight);

          ctx.beginPath();
          ctx.arc(aX, aY, 5, 0, Math.PI * 2);
          ctx.fillStyle = color;
          ctx.fill();
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 1.5;
          ctx.stroke();

          ctx.fillStyle = color;
          ctx.font = 'bold 10px "JetBrains Mono", sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText(`Apex: ${apexHeight.toFixed(2)}m`, aX, Math.max(topMargin + 12, aY - 9));
        }
      }

      // Impact Reticle Marker on Ground Line
      if (firstImpactDist && firstImpactDist >= domainDistMin && firstImpactDist <= domainDistMax) {
        const impX = toCanvasX(firstImpactDist);

        ctx.beginPath();
        ctx.arc(impX, groundY, 4, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        ctx.fillStyle = color;
        ctx.font = 'bold 10px "JetBrains Mono", sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(`Impact: ${firstImpactDist.toFixed(1)}m`, impX, groundY + 32 + (idx * 13));
      }
    });

    // ── Render Divergence Point Indicator ────────────────────────────────────
    if (divergencePoint && divergencePoint.dist >= domainDistMin && divergencePoint.dist <= domainDistMax) {
      const divX = toCanvasX(divergencePoint.dist);
      const divY = toCanvasY(divergencePoint.height);

      ctx.strokeStyle = '#ec4899';
      ctx.setLineDash([4, 3]);
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(divX, topMargin + 10);
      ctx.lineTo(divX, groundY);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = '#ec4899';
      ctx.beginPath();
      ctx.arc(divX, divY, 6, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 9.5px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(`⚡ Divergence @ ${divergencePoint.dist.toFixed(1)}m`, divX, topMargin + 24);
    }
  }, [comparisonData, zoomMode]);

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
  const deltaCarry = delta?.delta_carry_m !== undefined ? delta.delta_carry_m : 0;
  const deltaSpeed = delta?.delta_speed_kmh !== undefined ? delta.delta_speed_kmh : 0;
  const deltaElev = delta?.delta_elevation_deg !== undefined ? delta.delta_elevation_deg : 0;
  const deltaDist = delta?.delta_total_dist_m !== undefined ? delta.delta_total_dist_m : 0;

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Selector & Multi-Experiment Configuration Card */}
      <div className="card p-5 border border-border-color bg-bg-card rounded-xl space-y-4 shadow-lg">
        <div className="flex justify-between items-center pb-3 border-b border-border-color flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Scale className="w-5 h-5 text-accent-cyan" />
            <h3 className="text-base font-bold text-text-primary">
              Multi-Experiment Trajectory & Kinematic Delta Suite
            </h3>
          </div>
          <span className="text-[10px] uppercase font-mono px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-accent-cyan border border-cyan-500/30">
            Unified Physical Scale (100% Metric Preserved)
          </span>
        </div>

        <p className="text-xs text-text-secondary leading-relaxed">
          Select up to 3 experiments to overlay on identical physical scales, detect points of trajectory divergence, and evaluate kinematic sensitivities:
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 items-end">
          {/* Baseline A */}
          <div>
            <label className="block text-[11px] font-semibold text-cyan-400 mb-1 uppercase tracking-wide flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
              Baseline [A]
            </label>
            <select
              value={idA}
              onChange={(e) => {
                const val = e.target.value;
                setIdA(val);
                handleCompare([val, idB, idC]);
              }}
              className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-3 rounded-md text-xs font-mono font-medium"
            >
              {allExperiments.map((exp) => (
                <option key={exp.id || exp.experiment_id} value={exp.id || exp.experiment_id}>
                  {exp.name || exp.id} ({exp.outcome_call || 'IN_PLAY'})
                </option>
              ))}
            </select>
          </div>

          {/* Variant B */}
          <div>
            <label className="block text-[11px] font-semibold text-amber-400 mb-1 uppercase tracking-wide flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
              Variant [B]
            </label>
            <select
              value={idB}
              onChange={(e) => {
                const val = e.target.value;
                setIdB(val);
                handleCompare([idA, val, idC]);
              }}
              className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-3 rounded-md text-xs font-mono font-medium"
            >
              {allExperiments.map((exp) => (
                <option key={exp.id || exp.experiment_id} value={exp.id || exp.experiment_id}>
                  {exp.name || exp.id} ({exp.outcome_call || 'IN_PLAY'})
                </option>
              ))}
            </select>
          </div>

          {/* Optional Variant C */}
          <div>
            <label className="block text-[11px] font-semibold text-pink-400 mb-1 uppercase tracking-wide flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-pink-400"></span>
              Variant [C] (Optional)
            </label>
            <select
              value={idC}
              onChange={(e) => {
                const val = e.target.value;
                setIdC(val);
                handleCompare([idA, idB, val]);
              }}
              className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-3 rounded-md text-xs font-mono font-medium"
            >
              <option value="none">-- None (Compare A vs B) --</option>
              {allExperiments.map((exp) => (
                <option key={exp.id || exp.experiment_id} value={exp.id || exp.experiment_id}>
                  {exp.name || exp.id} ({exp.outcome_call || 'IN_PLAY'})
                </option>
              ))}
            </select>
          </div>

          <button
            disabled={isComparing}
            onClick={() => handleCompare()}
            className="btn btn-primary text-xs py-2 px-4 flex items-center justify-center gap-2 disabled:opacity-50 h-[34px]"
          >
            <Scale className="w-4 h-4" />
            <span>{isComparing ? 'Solving...' : 'Execute Comparison'}</span>
          </button>
        </div>
      </div>

      {/* Trajectory Overlay Canvas with Magnification Controls */}
      <div className="card p-4 border border-border-color bg-bg-card rounded-xl space-y-3 shadow-xl">
        <div className="flex justify-between items-center flex-wrap gap-2 pb-2 border-b border-border-color/60">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-accent-cyan" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-text-primary">
              2D Metric Elevation & Flight Profile Overlay
            </h4>
          </div>

          {/* Magnification Controls */}
          <div className="flex items-center gap-1.5 bg-bg-primary p-1 rounded-lg border border-border-color">
            <span className="text-[10px] text-text-muted px-2 font-medium flex items-center gap-1">
              <ZoomIn className="w-3 h-3" /> Zoom:
            </span>
            <button
              onClick={() => setZoomMode('full')}
              className={`text-[11px] px-2.5 py-1 rounded font-medium transition-colors ${
                zoomMode === 'full' ? 'bg-accent-primary text-white font-bold' : 'text-text-secondary hover:text-white'
              }`}
            >
              Full Field (0–85m)
            </button>
            <button
              onClick={() => setZoomMode('launch')}
              className={`text-[11px] px-2.5 py-1 rounded font-medium transition-colors ${
                zoomMode === 'launch' ? 'bg-accent-primary text-white font-bold' : 'text-text-secondary hover:text-white'
              }`}
            >
              Launch Zone (0–16m)
            </button>
            <button
              onClick={() => setZoomMode('impact')}
              className={`text-[11px] px-2.5 py-1 rounded font-medium transition-colors ${
                zoomMode === 'impact' ? 'bg-accent-primary text-white font-bold' : 'text-text-secondary hover:text-white'
              }`}
            >
              Impact Zone (35–80m)
            </button>
          </div>
        </div>

        {/* Canvas Display */}
        <div className="relative w-full rounded-lg overflow-hidden border border-border-color/70 bg-[#06090e]">
          <canvas ref={canvasRef} className="w-full block" />
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 flex-wrap pt-1 text-xs">
          {tableData.map((td, idx) => {
            const col = TRAJ_COLORS[idx % TRAJ_COLORS.length];
            return (
              <div key={td.experiment_id} className="flex items-center gap-2 font-mono">
                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: col.stroke }}></span>
                <span className="font-bold text-text-primary">
                  [{String.fromCharCode(65 + idx)}] {td.name}
                </span>
                <span className="text-text-muted">
                  ({td.launch_speed_kmh} km/h @ θ={td.elevation_deg}°)
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Comparative Delta Cards */}
      {comparisonData && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 font-mono">
          <div className="card p-3 border border-border-color bg-bg-card rounded-xl">
            <div className="text-[10px] text-text-muted uppercase">Δ Launch Speed</div>
            <div className={`text-lg font-bold mt-1 ${deltaSpeed !== 0 ? 'text-accent-cyan' : 'text-text-secondary'}`}>
              {deltaSpeed >= 0 ? '+' : ''}{deltaSpeed.toFixed(1)} km/h
            </div>
          </div>

          <div className="card p-3 border border-border-color bg-bg-card rounded-xl">
            <div className="text-[10px] text-text-muted uppercase">Δ Elevation Angle</div>
            <div className={`text-lg font-bold mt-1 ${deltaElev !== 0 ? 'text-accent-gold' : 'text-text-secondary'}`}>
              {deltaElev >= 0 ? '+' : ''}{deltaElev.toFixed(1)}°
            </div>
          </div>

          <div className="card p-3 border border-border-color bg-bg-card rounded-xl">
            <div className="text-[10px] text-text-muted uppercase">Δ Apex Height</div>
            <div className={`text-lg font-bold mt-1 ${deltaApex > 0.05 ? 'text-accent-cyan' : deltaApex < -0.05 ? 'text-accent-red' : 'text-text-secondary'}`}>
              {deltaApex >= 0 ? '+' : ''}{deltaApex.toFixed(2)} m
            </div>
          </div>

          <div className="card p-3 border border-border-color bg-bg-card rounded-xl">
            <div className="text-[10px] text-text-muted uppercase">Δ Carry Distance</div>
            <div className={`text-lg font-bold mt-1 ${deltaCarry > 0.1 ? 'text-accent-cyan' : deltaCarry < -0.1 ? 'text-accent-red' : 'text-text-secondary'}`}>
              {deltaCarry >= 0 ? '+' : ''}{deltaCarry.toFixed(1)} m
            </div>
          </div>

          <div className="card p-3 border border-border-color bg-bg-card rounded-xl">
            <div className="text-[10px] text-text-muted uppercase">Δ Flight Time</div>
            <div className={`text-lg font-bold mt-1 ${deltaTime !== 0 ? 'text-accent-cyan' : 'text-text-secondary'}`}>
              {deltaTime >= 0 ? '+' : ''}{deltaTime.toFixed(2)} s
            </div>
          </div>

          <div className="card p-3 border border-border-color bg-bg-card rounded-xl">
            <div className="text-[10px] text-text-muted uppercase">Δ Total Distance</div>
            <div className={`text-lg font-bold mt-1 ${deltaDist !== 0 ? 'text-accent-primary' : 'text-text-secondary'}`}>
              {deltaDist >= 0 ? '+' : ''}{deltaDist.toFixed(1)} m
            </div>
          </div>
        </div>
      )}

      {/* Side-by-Side Comprehensive Analytical Table */}
      {comparisonData && (
        <div className="card p-5 border border-border-color bg-bg-card rounded-xl shadow-lg space-y-4">
          <div className="flex justify-between items-center pb-2 border-b border-border-color">
            <h4 className="text-sm font-bold text-text-primary flex items-center gap-2">
              <span>📊</span> Side-by-Side Numerical Parameter & Outcome Breakdown
            </h4>
            <span className="text-xs text-text-muted font-mono">
              Delta Ref: [B] relative to Baseline [A]
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-border-color text-text-muted uppercase font-mono text-[10.5px]">
                  <th className="py-2 px-3">Physical Metric</th>
                  <th className="py-2 px-3 text-cyan-400">Baseline [A]: {base?.name || 'A'}</th>
                  <th className="py-2 px-3 text-amber-400">Variant [B]: {comp?.name || 'B'}</th>
                  <th className="py-2 px-3 text-accent-primary font-bold">Delta (Δ B - A)</th>
                  {tableData[2] && (
                    <th className="py-2 px-3 text-pink-400">Variant [C]: {tableData[2].name}</th>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-border-color/50 font-mono text-[11.5px]">
                <tr>
                  <td className="py-2.5 px-3 text-text-secondary font-sans font-medium">Launch Speed (v₀)</td>
                  <td className="py-2.5 px-3">{base?.launch_speed_kmh} km/h</td>
                  <td className="py-2.5 px-3">{comp?.launch_speed_kmh} km/h</td>
                  <td className="py-2.5 px-3 font-bold text-cyan-300">
                    {deltaSpeed >= 0 ? '+' : ''}{deltaSpeed.toFixed(1)} km/h
                  </td>
                  {tableData[2] && <td className="py-2.5 px-3">{tableData[2].launch_speed_kmh} km/h</td>}
                </tr>

                <tr>
                  <td className="py-2.5 px-3 text-text-secondary font-sans font-medium">Elevation Angle (θ)</td>
                  <td className="py-2.5 px-3">{base?.elevation_deg}°</td>
                  <td className="py-2.5 px-3">{comp?.elevation_deg}°</td>
                  <td className="py-2.5 px-3 font-bold text-amber-300">
                    {deltaElev >= 0 ? '+' : ''}{deltaElev.toFixed(1)}°
                  </td>
                  {tableData[2] && <td className="py-2.5 px-3">{tableData[2].elevation_deg}°</td>}
                </tr>

                <tr>
                  <td className="py-2.5 px-3 text-text-secondary font-sans font-medium">Azimuth Angle (ϕ)</td>
                  <td className="py-2.5 px-3">{base?.azimuth_deg}°</td>
                  <td className="py-2.5 px-3">{comp?.azimuth_deg}°</td>
                  <td className="py-2.5 px-3 text-text-primary">
                    {((comp?.azimuth_deg || 0) - (base?.azimuth_deg || 0)).toFixed(1)}°
                  </td>
                  {tableData[2] && <td className="py-2.5 px-3">{tableData[2].azimuth_deg}°</td>}
                </tr>

                <tr>
                  <td className="py-2.5 px-3 text-text-secondary font-sans font-medium">Peak Apex Altitude (Z_max)</td>
                  <td className="py-2.5 px-3">{base?.apex_height_m} m</td>
                  <td className="py-2.5 px-3">{comp?.apex_height_m} m</td>
                  <td className="py-2.5 px-3 font-bold text-cyan-300">
                    {deltaApex >= 0 ? '+' : ''}{deltaApex.toFixed(2)} m
                  </td>
                  {tableData[2] && <td className="py-2.5 px-3">{tableData[2].apex_height_m} m</td>}
                </tr>

                <tr>
                  <td className="py-2.5 px-3 text-text-secondary font-sans font-medium">Flight Duration (t_flight)</td>
                  <td className="py-2.5 px-3">{base?.flight_time_s} s</td>
                  <td className="py-2.5 px-3">{comp?.flight_time_s} s</td>
                  <td className="py-2.5 px-3 text-text-primary">
                    {deltaTime >= 0 ? '+' : ''}{deltaTime.toFixed(2)} s
                  </td>
                  {tableData[2] && <td className="py-2.5 px-3">{tableData[2].flight_time_s} s</td>}
                </tr>

                <tr>
                  <td className="py-2.5 px-3 text-text-secondary font-sans font-medium">Carry Distance (1st Turf Impact)</td>
                  <td className="py-2.5 px-3 font-bold">{base?.carry_distance_m} m</td>
                  <td className="py-2.5 px-3 font-bold">{comp?.carry_distance_m} m</td>
                  <td className="py-2.5 px-3 font-bold text-sky-300">
                    {deltaCarry >= 0 ? '+' : ''}{deltaCarry.toFixed(1)} m
                  </td>
                  {tableData[2] && <td className="py-2.5 px-3 font-bold">{tableData[2].carry_distance_m} m</td>}
                </tr>

                <tr>
                  <td className="py-2.5 px-3 text-text-secondary font-sans font-medium">Total Match Distance</td>
                  <td className="py-2.5 px-3 font-bold">{base?.total_distance_m} m</td>
                  <td className="py-2.5 px-3 font-bold">{comp?.total_distance_m} m</td>
                  <td className="py-2.5 px-3 font-bold text-accent-primary">
                    {deltaDist >= 0 ? '+' : ''}{deltaDist.toFixed(1)} m
                  </td>
                  {tableData[2] && <td className="py-2.5 px-3 font-bold">{tableData[2].total_distance_m} m</td>}
                </tr>

                <tr className="bg-bg-primary/40 font-sans">
                  <td className="py-2.5 px-3 font-bold text-text-primary">Official Outcome Call</td>
                  <td className="py-2.5 px-3">
                    <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${getOutcomeClass(base?.outcome_call)}`}>
                      {base?.outcome_call}
                    </span>
                  </td>
                  <td className="py-2.5 px-3">
                    <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${getOutcomeClass(comp?.outcome_call)}`}>
                      {comp?.outcome_call}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-bold">
                    {base?.outcome_call === comp?.outcome_call ? (
                      <span className="text-emerald-400">Match Call Unchanged</span>
                    ) : (
                      <span className="text-amber-400">Outcome Shift Triggered</span>
                    )}
                  </td>
                  {tableData[2] && (
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${getOutcomeClass(tableData[2].outcome_call)}`}>
                        {tableData[2].outcome_call}
                      </span>
                    </td>
                  )}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
