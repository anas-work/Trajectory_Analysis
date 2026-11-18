import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import * as api from '../../services/api';
import { Video, Zap, Menu } from 'lucide-react';

export default function Topbar() {
  const { 
    activeTab, 
    setActiveTab, 
    theme, 
    setTheme, 
    activeExperimentId,
    currentExperiment,
    refreshArchive,
    mobileMenuOpen,
    setMobileMenuOpen
  } = useApp();

  const [isRendering, setIsRendering] = useState(false);

  // Tab Headings Mapping
  const getHeadings = () => {
    switch (activeTab) {
      case 'tab-dashboard':
        return {
          title: 'Trajectory Control Center',
          subtitle: 'Scientific Cricket Trajectory Simulation & Explainability Platform',
        };
      case 'tab-new-experiment':
        return {
          title: 'New Experiment Configuration',
          subtitle: 'Ball kinematics, aerodynamics, pitch restitution, turf & fielding restrictions',
        };
      case 'tab-ground-view':
        return {
          title: '3D Stadium Viewport & Forensic Flight Inspector',
          subtitle: 'High-precision WebGL trajectory playback, broadcast cameras & ground truth validation',
        };
      case 'tab-formulas':
        return {
          title: 'Scientific Explainability & Formula Trace',
          subtitle: 'Step-by-step mathematical derivations, LaTeX formulas, variable substitutions & citations',
        };
      case 'tab-history':
        return {
          title: 'Experiment Archive & Database Repository',
          subtitle: 'SQLite-backed repository of real dual-camera match deliveries and custom simulations',
        };
      case 'tab-compare':
        return {
          title: 'Multi-Experiment Delta & Sensitivity Analysis',
          subtitle: 'Side-by-side comparison of launch kinematics, aerodynamic forces & trajectory curves',
        };
      case 'tab-videos':
        return {
          title: 'Analytical Video Gallery & Hawkeye Broadcast Export',
          subtitle: '4-panel multi-angle analytical videos with live telemetry and 3D overlays',
        };
      default:
        return {
          title: 'Trajectory Control Center',
          subtitle: 'Scientific Cricket Trajectory Engine',
        };
    }
  };

  const { title, subtitle } = getHeadings();

  const handleRenderMultiView = async () => {
    const expId = activeExperimentId || currentExperiment?.experiment_id || currentExperiment?.id;
    if (!expId) {
      alert('Please select or run an experiment first before rendering an analytical video.');
      return;
    }

    setIsRendering(true);
    try {
      const res = await api.renderAnalyticalVideo(expId);
      alert(`Analytical broadcast video generated successfully for ${expId}!\nOutput: ${res.video_mp4}`);
      await refreshArchive();
      setActiveTab('tab-videos');
    } catch (err) {
      console.error('Render video failed:', err);
      alert(`Render video failed: ${err.message}`);
    } finally {
      setIsRendering(false);
    }
  };

  return (
    <header className="h-[72px] bg-bg-secondary border-b border-border-color px-3 sm:px-6 flex items-center justify-between flex-shrink-0 z-10 transition-colors duration-300">
      <div className="flex items-center min-w-0 flex-1 mr-2">
        {/* Mobile Hamburger Menu Toggle */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="lg:hidden p-1.5 text-text-secondary hover:text-white rounded-lg hover:bg-white/10 transition-colors mr-2 flex-shrink-0"
          aria-label="Toggle navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="min-w-0 overflow-hidden">
          <h1 className="text-base sm:text-lg font-bold text-text-primary tracking-tight truncate">
            {title}
          </h1>
          <div className="hidden md:block text-[12px] text-text-secondary mt-0.5 truncate">
            {subtitle}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-1.5 sm:gap-3 flex-shrink-0">
        {/* Live Theme Switcher */}
        <select
          value={theme}
          onChange={(e) => setTheme(e.target.value)}
          className="bg-bg-card border border-border-color text-text-primary text-[11px] sm:text-[11.5px] px-2 py-1.5 rounded-md cursor-pointer font-medium hover:border-accent-primary/50 transition-colors focus:outline-none focus:ring-1 focus:ring-accent-primary"
          title="Select UI Visual Theme"
        >
          <option value="emerald">🌿 Obsidian Emerald</option>
          <option value="titanium">🌌 Midnight Titanium</option>
          <option value="carbon">⚡ OLED Carbon</option>
        </select>

        {/* Active Experiment Badge */}
        {activeExperimentId && (
          <span className="hidden xl:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono font-semibold bg-emerald-500/15 text-accent-green border border-emerald-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            {activeExperimentId}
          </span>
        )}

        {/* Render Analytical Multi-View */}
        <button
          onClick={handleRenderMultiView}
          disabled={isRendering}
          className="btn btn-secondary text-[11px] sm:text-[12px] py-1.5 px-2.5 sm:px-3 flex items-center gap-1.5 disabled:opacity-50"
          title="Generate 4-Angle Analytical Video"
        >
          <Video className="w-3.5 h-3.5 text-accent-cyan" />
          <span className="hidden sm:inline">{isRendering ? 'Rendering...' : 'Render Multi-View'}</span>
        </button>

        {/* Quick Launch / Run */}
        <button
          onClick={() => setActiveTab('tab-new-experiment')}
          className="btn btn-primary text-[11px] sm:text-[12px] py-1.5 px-2.5 sm:px-3.5 flex items-center gap-1.5"
        >
          <Zap className="w-3.5 h-3.5 fill-current" />
          <span className="hidden xs:inline">New Simulation</span>
        </button>
      </div>
    </header>
  );
}

