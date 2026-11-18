import React from 'react';
import { useApp } from '../../context/AppContext';
import { isDeliveryRecord } from '../../utils/formatters';
import StadiumCanvas from './StadiumCanvas';
import ViewportHud from './ViewportHud';
import PlaybackControls from './PlaybackControls';
import ExperimentInspector from './ExperimentInspector';

export default function GroundViewTab() {
  const { 
    allExperiments, 
    activeExperimentId, 
    loadExperiment, 
    loadDeliveryDetails, 
    setActiveTab, 
    setHistoryFilter 
  } = useApp();

  const deliveries = allExperiments.filter((e) => isDeliveryRecord(e));
  deliveries.sort((a, b) => (a.id || '').localeCompare(b.id || ''));

  const handleDeliverySelect = (e) => {
    const id = e.target.value;
    if (id) {
      loadExperiment(id, false, false);
    }
  };

  const scrollToDetails = () => {
    const el = document.getElementById('experiment-inspector-suite');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Quick Delivery Switcher Bar */}
      <div className="flex justify-between items-center bg-sky-500/10 border border-sky-500/25 p-3 px-4 rounded-xl flex-wrap gap-3">
        <div className="flex items-center gap-3 flex-wrap flex-1 min-w-[280px]">
          <span className="text-xs font-semibold text-accent-cyan flex items-center gap-1.5 whitespace-nowrap">
            <span>🏏</span> Real Match Delivery:
          </span>
          <select
            value={activeExperimentId || ''}
            onChange={handleDeliverySelect}
            className="form-control text-xs flex-1 max-w-md bg-bg-card text-text-primary border-border-color py-1.5 px-3 rounded-md"
          >
            <option value="">-- Switch to Real Match Delivery (CAM1 / CAM2) --</option>
            {deliveries.map((d) => {
              const speed = Number(d.launch_speed_kmh || 0).toFixed(1);
              const dist = Number(d.total_distance_m || 0).toFixed(1);
              return (
                <option key={d.id} value={d.id}>
                  {d.id}: {d.name} — [{d.outcome_call || 'IN_PLAY'}] ({speed} km/h, {dist}m)
                </option>
              );
            })}
          </select>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={scrollToDetails}
            className="btn btn-primary text-xs py-1.5 px-3 flex items-center gap-1"
            title="Scroll down to delivery inspection details, video clip and parameters"
          >
            <span>📋 View Delivery Details & Video ⬇️</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab('tab-history');
              setHistoryFilter('deliveries');
            }}
            className="btn btn-secondary text-xs py-1.5 px-3 flex items-center gap-1"
          >
            <span>📁 Archive Table</span>
          </button>
        </div>
      </div>

      {/* 3D WebGL Viewport Container */}
      <div className="relative w-full h-[540px] rounded-xl overflow-hidden border border-border-color bg-black shadow-2xl">
        <StadiumCanvas />
        <ViewportHud />
        <PlaybackControls />
      </div>

      {/* Forensic Inspector Suite */}
      <ExperimentInspector />
    </div>
  );
}

