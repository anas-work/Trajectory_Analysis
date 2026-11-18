import React, { useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { Play, Pause, RotateCcw } from 'lucide-react';

export default function PlaybackControls() {
  const { playback, setPlayback, cameraView, setCameraView, trajectory } = useApp();
  const lastTimeRef = useRef(performance.now());
  const speedRef = useRef(playback.speed);

  const SPEED_OPTIONS = [0.25, 0.5, 1.0, 1.5, 2.0];

  useEffect(() => {
    speedRef.current = playback.speed;
  }, [playback.speed]);

  // Animation Playback Loop
  useEffect(() => {
    let animId;

    const tick = (now) => {
      const dt = (now - lastTimeRef.current) / 1000;
      lastTimeRef.current = now;

      if (playback.isPlaying) {
        setPlayback((prev) => {
          const spd = speedRef.current ?? prev.speed ?? 1.0;
          const nextTime = prev.currentTime + dt * spd;
          if (nextTime >= prev.duration) {
            return {
              ...prev,
              isPlaying: false,
              currentTime: prev.duration,
            };
          }
          return {
            ...prev,
            currentTime: nextTime,
          };
        });
      }

      animId = requestAnimationFrame(tick);
    };

    lastTimeRef.current = performance.now();
    animId = requestAnimationFrame(tick);

    return () => cancelAnimationFrame(animId);
  }, [playback.isPlaying, setPlayback]);

  const togglePlay = () => {
    lastTimeRef.current = performance.now();
    setPlayback((prev) => {
      // If at end, loop back to 0
      const isAtEnd = prev.currentTime >= prev.duration && prev.duration > 0;
      return {
        ...prev,
        isPlaying: !prev.isPlaying,
        currentTime: isAtEnd ? 0 : prev.currentTime,
      };
    });
  };

  const handleReset = () => {
    setPlayback((prev) => ({
      ...prev,
      isPlaying: false,
      currentTime: 0,
    }));
  };

  const handleScrubberChange = (e) => {
    const pct = parseFloat(e.target.value) || 0;
    const dur = playback.duration || (trajectory.length > 0 ? trajectory[trajectory.length - 1][0] : 0);
    const newTime = (pct / 100.0) * dur;
    setPlayback((prev) => ({
      ...prev,
      currentTime: newTime,
    }));
  };

  const handleSpeedChange = (e) => {
    const spd = parseFloat(e.target.value) || 1.0;
    setPlayback((prev) => ({
      ...prev,
      speed: spd,
    }));
  };

  const scrubberPct = playback.duration > 0
    ? (playback.currentTime / playback.duration) * 100.0
    : 0;

  return (
    <>
      {/* Top-Right Camera View Overlay Buttons */}
      <div className="absolute top-4 right-4 z-10 flex gap-1.5 flex-wrap justify-end">
        {[
          { id: 'isometric', label: 'Isometric 3D' },
          { id: 'side', label: 'Side Elevation' },
          { id: 'top', label: 'Top-Down Ground' },
          { id: 'rear', label: 'Batsman View' },
          { id: 'bowler', label: 'Bowler TV Cam' },
        ].map((view) => (
          <button
            key={view.id}
            type="button"
            onClick={() => setCameraView(view.id)}
            className={`text-xs px-2.5 py-1.5 rounded font-medium transition-all ${
              cameraView === view.id
                ? 'bg-accent-primary text-white shadow-md'
                : 'bg-bg-secondary/80 backdrop-blur-md text-text-secondary hover:text-text-primary border border-border-color'
            }`}
          >
            {view.label}
          </button>
        ))}
      </div>

      {/* Bottom Timeline Scrubber Overlay */}
      <div className="absolute bottom-4 left-4 right-4 z-10 bg-bg-secondary/90 backdrop-blur-md border border-border-color/80 p-3 rounded-lg shadow-xl flex items-center gap-3">
        {/* Play/Pause */}
        <button
          type="button"
          onClick={togglePlay}
          className="btn btn-primary text-xs py-1.5 px-3 flex items-center gap-1.5 min-w-[75px] justify-center"
        >
          {playback.isPlaying ? (
            <>
              <Pause className="w-3.5 h-3.5 fill-current" />
              <span>Pause</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Play</span>
            </>
          )}
        </button>

        {/* Reset */}
        <button
          type="button"
          onClick={handleReset}
          className="btn btn-secondary text-xs py-1.5 px-2.5 flex items-center gap-1"
          title="Reset to Release Crease"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset</span>
        </button>

        {/* Range Scrubber */}
        <input
          type="range"
          min="0"
          max="100"
          step="0.1"
          value={scrubberPct}
          onChange={handleScrubberChange}
          className="flex-1 accent-accent-primary h-1.5 bg-bg-card rounded-lg appearance-none cursor-pointer"
        />

        {/* Time Label */}
        <span className="font-mono text-xs text-text-secondary min-w-[55px] text-right font-medium">
          {playback.currentTime.toFixed(2)} s
        </span>

        {/* Playback Speed Pill Buttons */}
        <div className="hidden sm:flex items-center gap-1 bg-bg-card p-0.5 rounded border border-border-color">
          {SPEED_OPTIONS.map((spd) => {
            const isSelected = Math.abs(playback.speed - spd) < 0.05;
            return (
              <button
                key={spd}
                type="button"
                onClick={() => setPlayback((prev) => ({ ...prev, speed: spd }))}
                className={`px-1.5 py-0.5 text-[10px] font-mono rounded transition-colors ${
                  isSelected
                    ? 'bg-accent-primary text-white font-bold'
                    : 'text-text-muted hover:text-text-primary'
                }`}
                title={`Set playback speed to ${spd}x`}
              >
                {spd}x
              </button>
            );
          })}
        </div>

        {/* Playback Speed Select */}
        <select
          value={String(SPEED_OPTIONS.find((s) => Math.abs(s - playback.speed) < 0.05) ?? (playback.speed === 1 ? '1' : playback.speed === 2 ? '2' : playback.speed))}
          onChange={handleSpeedChange}
          className="bg-bg-card border border-border-color text-text-primary text-xs px-2 py-1 rounded font-mono cursor-pointer focus:outline-none"
        >
          <option value="0.25">0.25x</option>
          <option value="0.5">0.50x</option>
          <option value="1">1.00x</option>
          <option value="1.5">1.50x</option>
          <option value="2">2.00x</option>
        </select>
      </div>
    </>
  );
}

