import React, { useMemo } from 'react';
import { useApp } from '../../context/AppContext';
import { getOutcomeClass } from '../../utils/formatters';

export default function ViewportHud() {
  const { trajectory, metrics, currentExperiment, playback } = useApp();

  const outcome = metrics?.outcome_call || metrics?.outcome || 'IN_PLAY';
  const totalDist = Number(metrics?.total_distance_m || metrics?.horizontal_distance_m || 0);
  const carryDist = Number(metrics?.carry_distance_m !== undefined && metrics?.carry_distance_m !== null
    ? metrics.carry_distance_m
    : (metrics?.d_pitch || 0));
  const apex = Number(metrics?.max_height_m || 0);

  const cfg = currentExperiment?.config || {};
  const vel0 = cfg.vel0 || (trajectory && trajectory[0] ? [trajectory[0][4], trajectory[0][5], trajectory[0][6]] : [0, 0, 0]);
  const vx0 = Number(vel0[0] || 0);
  const vy0 = Number(vel0[1] || 0);
  const vz0 = Number(vel0[2] || 0);
  const vxy = Math.hypot(vx0, vy0);
  const speed0Kmh = cfg.speed0_kmh || (Math.hypot(vxy, vz0) * 3.6);
  const elevDeg = cfg.elevation_deg !== undefined ? cfg.elevation_deg : (Math.atan2(vz0, Math.max(1e-6, vxy)) * 180 / Math.PI);
  const azimDeg = cfg.azimuth_deg !== undefined ? cfg.azimuth_deg : (Math.atan2(vy0, Math.max(1e-6, vx0)) * 180 / Math.PI);
  const vhKmh = vxy * 3.6;
  const vzKmh = vz0 * 3.6;

  const interception = metrics?.fielder_interception;
  const isCaught = Boolean(interception && interception.can_intercept);

  // Interpolate state at playback.currentTime
  const currentTelemetry = useMemo(() => {
    if (!trajectory || trajectory.length === 0) {
      return {
        time: 0,
        pos: [0, 0, 0.9],
        speed: 0,
        dist: 0,
      };
    }

    const t = playback.currentTime;
    let state = trajectory[0];

    for (let i = 0; i < trajectory.length - 1; i++) {
      if (t >= trajectory[i][0] && t <= trajectory[i + 1][0]) {
        const alpha = (t - trajectory[i][0]) / (trajectory[i + 1][0] - trajectory[i][0]);
        state = [
          t,
          trajectory[i][1] + alpha * (trajectory[i + 1][1] - trajectory[i][1]),
          trajectory[i][2] + alpha * (trajectory[i + 1][2] - trajectory[i][2]),
          trajectory[i][3] + alpha * (trajectory[i + 1][3] - trajectory[i][3]),
          trajectory[i][4] + alpha * (trajectory[i + 1][4] - trajectory[i][4]),
          trajectory[i][5] + alpha * (trajectory[i + 1][5] - trajectory[i][5]),
          trajectory[i][6] + alpha * (trajectory[i + 1][6] - trajectory[i][6]),
        ];
        break;
      }
    }

    const speed = Math.hypot(state[4] || 0, state[5] || 0, state[6] || 0);
    const dist = Math.hypot((state[1] || 0) - trajectory[0][1], (state[2] || 0) - trajectory[0][2]);

    return {
      time: t,
      pos: [state[1] || 0, state[2] || 0, state[3] || 0],
      speed: speed,
      dist: dist,
    };
  }, [trajectory, playback.currentTime]);

  const outcomeBannerText = outcome.includes('SIX')
    ? `SIX (${totalDist.toFixed(1)}m)`
    : outcome.includes('FOUR')
    ? `FOUR (${totalDist.toFixed(1)}m)`
    : outcome;

  return (
    <div className="absolute top-4 left-4 z-10 pointer-events-none select-none flex flex-col gap-2">
      {/* Outcome Banner */}
      <div className={`outcome-banner ${getOutcomeClass(outcome)} text-xs sm:text-sm font-bold px-3 py-1.5 shadow-xl border`}>
        {outcomeBannerText}
      </div>

      {/* Launch Kinematics Card */}
      <div className="bg-slate-950/94 border border-cyan-500/50 p-2.5 rounded-lg shadow-2xl text-slate-100 text-xs w-60">
        <div className="flex justify-between items-center text-[10px] font-mono uppercase tracking-wider text-cyan-400 pb-1 border-b border-slate-800">
          <span>📐 Launch Kinematics</span>
          <span className="font-bold text-amber-400">θ = {elevDeg >= 0 ? '+' : ''}{Number(elevDeg || 0).toFixed(1)}°</span>
        </div>
        <div className="grid grid-cols-2 gap-x-2 gap-y-1 font-mono text-[11px] mt-1.5">
          <div className="flex justify-between">
            <span className="text-slate-400">V₀ Speed:</span>
            <span className="font-bold text-cyan-300">{Number(speed0Kmh || 0).toFixed(1)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Azimuth:</span>
            <span>{Number(azimDeg || 0).toFixed(1)}°</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Vh:</span>
            <span className="text-emerald-400 font-semibold">{vhKmh.toFixed(1)} km/h</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Vz:</span>
            <span className={`font-semibold ${vzKmh >= 0 ? 'text-amber-400' : 'text-red-400'}`}>
              {vzKmh >= 0 ? '+' : ''}{vzKmh.toFixed(1)} km/h
            </span>
          </div>
        </div>
      </div>

      {/* Real-time Telemetry Panel */}
      <div className="bg-slate-950/94 border border-slate-800 p-2.5 rounded-lg shadow-2xl text-slate-100 text-xs w-60">
        <div className="flex justify-between items-center text-[10px] font-mono uppercase tracking-wider text-slate-400 pb-1 border-b border-slate-800">
          <span>Flight Telemetry</span>
          <span className="text-cyan-400 font-bold font-mono">{currentTelemetry.time.toFixed(2)} s</span>
        </div>
        <div className="space-y-1 font-mono text-[11px] mt-1.5">
          <div className="flex justify-between">
            <span className="text-slate-400">Position:</span>
            <span>[{currentTelemetry.pos[0].toFixed(1)}, {currentTelemetry.pos[1].toFixed(1)}, {currentTelemetry.pos[2].toFixed(1)}] m</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Live Speed:</span>
            <span className="font-semibold text-white">{(currentTelemetry.speed * 3.6).toFixed(1)} km/h</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Apex Height:</span>
            <span className="text-amber-400 font-bold">{apex.toFixed(2)} m</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">{isCaught ? 'Hypothetical Pitch:' : '1st Impact:'}</span>
            <span className="text-sky-300 font-bold">{carryDist.toFixed(1)} m</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Distance:</span>
            <span className="font-bold text-emerald-400">{currentTelemetry.dist.toFixed(1)} m</span>
          </div>
        </div>

        {/* Fielder Interception Alert */}
        {isCaught && interception && (
          <div className="mt-2 pt-1.5 border-t border-red-500/40 text-[10.5px] font-mono text-red-300">
            <div className="font-bold flex items-center gap-1 text-red-400">
              <span>🧤</span> Intercepted by {interception.role_name || 'Fielder'}
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">
              Catch at t = {Number(interception.catch_time_s || 0).toFixed(2)}s | Sprint: {Number(interception.required_speed_m_s || 0).toFixed(1)} m/s
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
