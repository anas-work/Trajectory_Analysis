import React, { useRef, useEffect, useCallback } from 'react';
import { useApp } from '../../context/AppContext';

export default function FieldingRadar({ 
  boundaryRadius = 70.0, 
  format = 'T20',
  selectedFielderIndex = 0,
  onSelectFielder = null,
}) {
  const canvasRef = useRef(null);
  const { fielders, setFielders, trajectory } = useApp();
  const draggingFielderIndex = useRef(-1);

  // Validate fielding compliance
  const validateCompliance = useCallback(() => {
    let deepFielders = 0;
    let behindSquareLeg = 0;

    fielders.forEach((f) => {
      // f.x: downfield distance from batsman (x > 0 is forward, x < 0 is behind crease)
      // f.y: lateral distance (+ is off-side, - is leg-side)
      const distFromBat = Math.hypot(f.x, f.y);
      if (distFromBat > 27.432) {
        deepFielders++;
      }
      if (f.x < 0 && f.y < 0) {
        behindSquareLeg++;
      }
    });

    const is11Valid = fielders.length === 11;
    const isBehindSquareValid = behindSquareLeg <= 2;
    const isPowerplayValid = format === 'Test' || deepFielders <= 2;

    let error = null;
    if (!is11Valid) {
      error = `Invalid player count: ${fielders.length} fielders (must be exactly 11).`;
    } else if (!isBehindSquareValid) {
      error = `⚠️ Law 28.4 Violation: ${behindSquareLeg} fielders behind square on leg-side (max 2 allowed).`;
    } else if (!isPowerplayValid) {
      error = `⚠️ Powerplay Violation: ${deepFielders} fielders outside 30-yard ring (max 2 allowed).`;
    }

    return {
      isValid: is11Valid && isBehindSquareValid && isPowerplayValid,
      error,
      deepFielders,
      behindSquareLeg,
    };
  }, [fielders, format]);

  const compliance = validateCompliance();

  // Canvas drawing
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;

    const bndRadius = boundaryRadius || 70.0;
    const scale = (h * 0.40) / Math.max(70.0, bndRadius + 6.0);

    ctx.clearRect(0, 0, w, h);

    // Striker's popping crease on radar (Z_BAT = 8.84m)
    const batY = cy + 8.84 * scale;

    // Outfield circle
    ctx.beginPath();
    ctx.arc(cx, batY, bndRadius * scale, 0, Math.PI * 2);
    ctx.fillStyle = '#0f2417';
    ctx.fill();
    ctx.strokeStyle = '#34d399';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // 30-yard circle (27.432m)
    ctx.beginPath();
    ctx.arc(cx, batY, 27.432 * scale, 0, Math.PI * 2);
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.45)';
    ctx.stroke();
    ctx.setLineDash([]);

    // Pitch strip (20.12m x 3.05m)
    ctx.fillStyle = '#b59966';
    const pw = 3.05 * scale;
    const pl = 20.12 * scale;
    ctx.fillRect(cx - pw / 2, cy - pl / 2, pw, pl);

    // Creases
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(cx - pw, batY);
    ctx.lineTo(cx + pw, batY);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(cx - pw, cy - 8.84 * scale);
    ctx.lineTo(cx + pw, cy - 8.84 * scale);
    ctx.stroke();

    // Fielders
    fielders.forEach((f, idx) => {
      // In radar: off-side (+y) is left (-px), leg-side (-y) is right (+px)
      const px = cx - f.y * scale;
      const py = batY - f.x * scale;
      const isKeeper = f.role === 'wicketkeeper' || (f.name && f.name.includes('Keeper'));
      const isSelected = idx === selectedFielderIndex;
      const reachRad = f.reach_radius_m || f.catching_radius || 1.8;

      // Intercept Reach Ring
      ctx.beginPath();
      ctx.arc(px, py, reachRad * scale, 0, Math.PI * 2);
      ctx.fillStyle = isSelected
        ? 'rgba(236, 72, 153, 0.35)'
        : isKeeper
        ? 'rgba(245, 166, 35, 0.25)'
        : 'rgba(0, 180, 216, 0.25)';
      ctx.fill();
      if (isSelected) {
        ctx.strokeStyle = '#ec4899';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // Player marker dot
      ctx.beginPath();
      ctx.arc(px, py, isSelected ? 6.5 : 4.5, 0, Math.PI * 2);
      ctx.fillStyle = isSelected ? '#ec4899' : isKeeper ? '#f5a623' : '#00b4d8';
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = isSelected ? 2 : 1;
      ctx.stroke();

      // Label on selected fielder
      if (isSelected) {
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 9px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(f.name || f.role, px, py - 9);
      }
    });

    // Trajectory overlay if available
    if (trajectory && trajectory.length > 1) {
      ctx.beginPath();
      ctx.moveTo(cx - trajectory[0][2] * scale, batY - trajectory[0][1] * scale);
      for (let i = 1; i < trajectory.length; i++) {
        ctx.lineTo(cx - trajectory[i][2] * scale, batY - trajectory[i][1] * scale);
      }
      ctx.strokeStyle = '#00d2ff';
      ctx.lineWidth = 2.0;
      ctx.stroke();

      const last = trajectory[trajectory.length - 1];
      const lx = cx - last[2] * scale;
      const ly = batY - last[1] * scale;
      ctx.beginPath();
      ctx.arc(lx, ly, 4.5, 0, Math.PI * 2);
      ctx.fillStyle = '#ffd700';
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.2;
      ctx.stroke();
    }
  }, [fielders, boundaryRadius, trajectory, selectedFielderIndex]);

  // Handle Dragging Fielders
  const getFielderAtCoords = (clientX, clientY) => {
    const canvas = canvasRef.current;
    if (!canvas) return -1;
    const rect = canvas.getBoundingClientRect();
    const mx = clientX - rect.left;
    const my = clientY - rect.top;

    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const bndRadius = boundaryRadius || 70.0;
    const scale = (h * 0.40) / Math.max(70.0, bndRadius + 6.0);
    const batY = cy + 8.84 * scale;

    for (let i = 0; i < fielders.length; i++) {
      const f = fielders[i];
      const px = cx - f.y * scale;
      const py = batY - f.x * scale;
      if (Math.hypot(mx - px, my - py) <= 10) {
        return i;
      }
    }
    return -1;
  };

  const handleMouseDown = (e) => {
    const idx = getFielderAtCoords(e.clientX, e.clientY);
    if (idx !== -1) {
      draggingFielderIndex.current = idx;
      if (onSelectFielder) {
        onSelectFielder(idx);
      }
    }
  };

  const handleMouseMove = (e) => {
    if (draggingFielderIndex.current === -1) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const bndRadius = boundaryRadius || 70.0;
    const scale = (h * 0.40) / Math.max(70.0, bndRadius + 6.0);
    const batY = cy + 8.84 * scale;

    const newY = (cx - mx) / scale;
    const newX = (batY - my) / scale;

    setFielders((prev) => {
      const copy = [...prev];
      copy[draggingFielderIndex.current] = {
        ...copy[draggingFielderIndex.current],
        x: Math.round(newX * 10) / 10,
        y: Math.round(newY * 10) / 10,
      };
      return copy;
    });
  };

  const handleMouseUp = () => {
    draggingFielderIndex.current = -1;
  };

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
          2D Fielding Cordon Radar
        </span>
        <span
          className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
            compliance.isValid
              ? 'bg-emerald-500/15 text-accent-green border-emerald-500/30'
              : 'bg-rose-500/15 text-accent-red border-rose-500/30'
          }`}
        >
          {compliance.isValid ? '11 Players Valid' : 'Tactical Violation'}
        </span>
      </div>

      {compliance.error && (
        <div className="p-2.5 rounded-md bg-rose-500/15 border border-rose-500/30 text-rose-400 text-xs font-medium">
          {compliance.error}
        </div>
      )}

      <div className="flex justify-center bg-bg-primary p-2.5 rounded-lg border border-border-color">
        <canvas
          ref={canvasRef}
          width={400}
          height={240}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          className="rounded cursor-crosshair max-w-full h-auto"
          title="Drag and drop fielders to test custom placements"
        />
      </div>

      <div className="text-[11px] text-text-muted text-center flex items-center justify-center gap-4">
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-accent-cyan"></span>
          Fielder
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-accent-gold"></span>
          Wicketkeeper
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 border border-dashed border-white/60 rounded-full"></span>
          30-Yard Circle
        </span>
      </div>
    </div>
  );
}

