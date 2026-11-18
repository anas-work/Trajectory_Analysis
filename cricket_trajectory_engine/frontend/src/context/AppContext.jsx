import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import * as api from '../services/api';
import { normalizeTrajectory, anglesToCartesian } from '../utils/math';
import { fieldingPresetsData, quickScenarios } from '../services/presets';
import { isDeliveryRecord } from '../utils/formatters';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  // Navigation
  const [activeTab, setActiveTab] = useState('tab-dashboard');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Theme
  const [theme, setThemeState] = useState(() => {
    return localStorage.getItem('cricket_app_theme') || 'emerald';
  });

  // Active Experiment & Trajectory
  const [currentExperiment, setCurrentExperiment] = useState(null);
  const [activeExperimentId, setActiveExperimentId] = useState(null);
  const [trajectory, setTrajectory] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [trace, setTrace] = useState(null);

  // Fielders & Presets
  const [fielders, setFielders] = useState(fieldingPresetsData.powerplay);
  const [fieldingPreset, setFieldingPreset] = useState('powerplay');
  const [matchFormat, setMatchFormat] = useState('T20');
  const [turfPreset, setTurfPreset] = useState('natural_grass');

  // Archive
  const [allExperiments, setAllExperiments] = useState([]);
  const [historyFilter, setHistoryFilter] = useState('all');
  const [historySearchQuery, setHistorySearchQuery] = useState('');

  // 3D Playback State
  const [playback, setPlayback] = useState({
    isPlaying: false,
    currentTime: 0,
    duration: 0,
    speed: 1.0,
  });

  // 3D Camera View
  const [cameraView, setCameraView] = useState('isometric');

  // Apply Theme to documentElement
  const setTheme = useCallback((newTheme) => {
    const valid = ['emerald', 'titanium', 'carbon'];
    const chosen = valid.includes(newTheme) ? newTheme : 'emerald';
    setThemeState(chosen);
    document.documentElement.setAttribute('data-theme', chosen);
    localStorage.setItem('cricket_app_theme', chosen);
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Load Archive from SQLite
  const refreshArchive = useCallback(async () => {
    try {
      const list = await api.fetchExperiments();
      setAllExperiments(list);
      return list;
    } catch (err) {
      console.error('Failed to load experiments archive:', err);
      return [];
    }
  }, []);

  // Handle Simulation / Experiment Data Loaded
  const applySimulationData = useCallback((data) => {
    setCurrentExperiment(data);
    const rawTraj = data.trajectory_downsampled || data.trajectory_samples || data.trajectory || [];
    const norm = normalizeTrajectory(rawTraj);
    setTrajectory(norm);
    setMetrics(data.results || {});
    setTrace(data.calculation_trace || null);

    const dur = norm.length > 0 ? norm[norm.length - 1][0] : 0;
    setPlayback(prev => ({
      ...prev,
      isPlaying: false,
      currentTime: 0,
      duration: dur,
    }));
  }, []);

  // Load an experiment by ID
  const loadExperiment = useCallback(async (id, switchTabFlag = true, scrollToDetails = false) => {
    if (!id) return;
    try {
      const exp = await api.fetchExperimentById(id);
      setActiveExperimentId(id);

      const simData = {
        experiment_id: exp.id || exp.experiment_id || id,
        name: exp.name || id,
        created_at: exp.created_at || exp.timestamp,
        fingerprint: exp.fingerprint,
        from_cache: true,
        config: exp.config,
        results: exp.results,
        trajectory_downsampled: exp.trajectory || [],
        calculation_trace: exp.calculation_trace,
        has_ground_truth_clip: exp.has_ground_truth_clip,
        ground_truth_clip_url: exp.ground_truth_clip_url,
      };

      applySimulationData(simData);

      if (switchTabFlag) {
        setActiveTab('tab-ground-view');
      }

      if (scrollToDetails) {
        setTimeout(() => {
          const inspector = document.getElementById('experiment-inspector-suite');
          if (inspector) {
            inspector.scrollIntoView({ behavior: 'smooth', block: 'start' });
            inspector.classList.remove('inspector-highlight-pulse');
            void inspector.offsetWidth;
            inspector.classList.add('inspector-highlight-pulse');
            setTimeout(() => inspector.classList.remove('inspector-highlight-pulse'), 2500);
          }
        }, 120);
      } else if (switchTabFlag) {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    } catch (err) {
      console.error('Failed to load experiment:', err);
      if (switchTabFlag) {
        alert(`Failed to load experiment: ${err.message}`);
      }
    }
  }, [applySimulationData]);

  // Load delivery details specifically
  const loadDeliveryDetails = useCallback(async (id) => {
    await loadExperiment(id, true, true);
  }, [loadExperiment]);

  // Delete an experiment
  const deleteRecord = useCallback(async (expId) => {
    if (!expId) return;

    const exp = allExperiments.find(e => (e.id === expId || e.experiment_id === expId));
    const expName = exp ? (exp.name || expId) : expId;
    const isDeliv = exp ? isDeliveryRecord(exp) : expId.startsWith('DELIVERY_');

    const promptMsg = isDeliv
      ? `Are you sure you want to delete match delivery "${expName}" (${expId})?\n\nThis will remove the delivery permanently from SQLite database storage.`
      : `Are you sure you want to delete simulation record "${expName}" (${expId})?\n\nThis will remove the record permanently from SQLite database storage.`;

    if (!window.confirm(promptMsg)) return;

    try {
      await api.deleteExperiment(expId);
      const updated = await refreshArchive();

      if (activeExperimentId === expId) {
        if (updated.length > 0) {
          const nextId = updated[0].id || updated[0].experiment_id;
          await loadExperiment(nextId, false, false);
        } else {
          setActiveExperimentId(null);
          setCurrentExperiment(null);
          setTrajectory([]);
          setMetrics(null);
          setTrace(null);
        }
      }
    } catch (err) {
      console.error('Delete failed:', err);
      alert(`Could not delete record: ${err.message}`);
    }
  }, [allExperiments, activeExperimentId, loadExperiment, refreshArchive]);

  // Initial load
  useEffect(() => {
    async function init() {
      const list = await refreshArchive();
      if (list && list.length > 0) {
        const first = list[0].id || list[0].experiment_id;
        loadExperiment(first, false, false);
      } else {
        // Fallback to straight six scenario
        const sc = quickScenarios.straight_six;
        try {
          const c = anglesToCartesian(sc.speed, sc.elev, sc.azim);
          const runRes = await api.runSimulation({
            name: sc.name,
            speed: sc.speed,
            speed_m_s: sc.speed,
            speed0_kmh: sc.speed * 3.6,
            elevation: sc.elev,
            elevation_deg: sc.elev,
            azimuth: sc.azim,
            azimuth_deg: sc.azim,
            vel0: [c.vx, c.vy, c.vz],
            initial_velocity: [c.vx, c.vy, c.vz],
            pos0: [0.0, 0.0, 0.9],
            initial_position: [0.0, 0.0, 0.9],
            ball: { mass_kg: 0.156, diameter_m: 0.072 },
            environment: {
              surface_preset: sc.turf,
              restitution_normal: 0.45,
              friction_tangential: 0.38,
              rolling_resistance_coeff: 0.12,
              wind_vector: sc.wind,
              constant_cd: sc.cd,
              drag_model: 'reynolds_dependent',
              enable_magnus: true,
              spin_rad_s: sc.spin,
            },
            aerodynamics: {
              drag_model: 'reynolds_dependent',
              cd_base: sc.cd,
              enable_magnus: true,
              spin_vector: sc.spin,
            },
            stadium: { shape: 'circle', boundary_radius: 70.0 },
            fielders: fieldingPresetsData.powerplay,
          });
          applySimulationData(runRes);
          refreshArchive();
        } catch (e) {
          console.warn('Initial simulation fallback failed:', e);
        }
      }
    }
    init();
  }, [refreshArchive, loadExperiment, applySimulationData]);

  const value = {
    activeTab,
    setActiveTab,
    mobileMenuOpen,
    setMobileMenuOpen,
    theme,
    setTheme,
    currentExperiment,
    activeExperimentId,
    trajectory,
    metrics,
    trace,
    fielders,
    setFielders,
    fieldingPreset,
    setFieldingPreset,
    matchFormat,
    setMatchFormat,
    turfPreset,
    setTurfPreset,
    allExperiments,
    historyFilter,
    setHistoryFilter,
    historySearchQuery,
    setHistorySearchQuery,
    playback,
    setPlayback,
    cameraView,
    setCameraView,
    refreshArchive,
    applySimulationData,
    loadExperiment,
    loadDeliveryDetails,
    deleteRecord,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}

