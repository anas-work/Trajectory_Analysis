import React, { useMemo } from 'react';
import { useApp } from '../../context/AppContext';
import { getOutcomeClass } from '../../utils/formatters';

export default function ViewportHud() {
  const { trajectory, metrics, playback } = useApp();

  const outcome = metrics?.outcome_call || metrics?.outcome || 'IN_PLAY';
  const totalDist = Number(metrics?.total_distance_m || metrics?.horizontal_distance_m || 0);
  const carryDist = Number(metrics?.carry_distance_m !== undefined && metrics?.carry_distance_m !== null
    ? metrics.carry_distance_m
    : (metrics?.d_pitch || 0));
  const apex = Number(metrics?.max_height_m || 0);

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
      <div className={`outcome-banner ${getOutcomeClass(outcome)} text-sm font-bold px-3 py-1.5 shadow-lg`}>
        {outcomeBannerText}
      </div>

      {/* Real-time Telemetry Panel */}
      <div className="bg-bg-secondary/90 backdrop-blur-md border border-border-color/80 p-3.5 rounded-lg shadow-xl text-text-primary text-xs w-60">
        <div className="text-[10px] font-mono uppercase tracking-wider text-text-muted mb-2 pb-1 border-b border-border-color/50">
          Real-time Telemetry
        </div>
        <div className="space-y-1.5 font-mono text-[11.5px]">
          <div className="flex justify-between">
            <span className="text-text-muted">Time:</span>
            <span className="text-accent-cyan font-bold">{currentTelemetry.time.toFixed(2)} s</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Pos:</span>
            <span>
              [{currentTelemetry.pos[0].toFixed(1)}, {currentTelemetry.pos[1].toFixed(1)}, {currentTelemetry.pos[2].toFixed(1)}] m
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Speed:</span>
            <span>
              {(currentTelemetry.speed * 3.6).toFixed(1)} km/h
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Apex:</span>
            <span className="text-accent-gold font-bold">{apex.toFixed(2)} m</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">1st Impact:</span>
            <span className="text-sky-400 font-bold">{carryDist.toFixed(1)} m</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Total Dist:</span>
            <span className="font-bold">{currentTelemetry.dist.toFixed(1)} m</span>
          </div>
        </div>
      </div>
    </div>
  );
}

