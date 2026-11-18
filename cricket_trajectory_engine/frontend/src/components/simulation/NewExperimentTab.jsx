import React, { useState, useMemo } from 'react';
import { useApp } from '../../context/AppContext';
import { anglesToCartesian, cartesianToAngles, calculateDerivedBallProperties } from '../../utils/math';
import { turfPresets, fieldingPresetsData } from '../../services/presets';
import * as api from '../../services/api';
import FieldingRadar from './FieldingRadar';
import { Zap, RotateCcw, User, Users, Shield, Sliders, CheckCircle2 } from 'lucide-react';

export default function NewExperimentTab() {
  const { 
    fielders, 
    setFielders, 
    fieldingPreset, 
    setFieldingPreset, 
    matchFormat, 
    setMatchFormat,
    turfPreset,
    setTurfPreset,
    applySimulationData,
    refreshArchive,
    setActiveTab
  } = useApp();

  // Mode: 'angles' | 'cartesian'
  const [velocityMode, setVelocityMode] = useState('angles');
  const [speedUnit, setSpeedUnit] = useState('kmh'); // 'kmh' or 'ms'

  // Launch Inputs
  const [name, setName] = useState('Lofted Straight Drive (115 km/h)');
  const [speed, setSpeed] = useState('115.2');
  const [elevation, setElevation] = useState(30.0);
  const [azimuth, setAzimuth] = useState(0.0);

  const [vx, setVx] = useState(() => (32.0 * Math.cos(30.0 * Math.PI / 180.0) * Math.cos(0.0)).toFixed(2));
  const [vy, setVy] = useState('0.00');
  const [vz, setVz] = useState(() => (32.0 * Math.sin(30.0 * Math.PI / 180.0)).toFixed(2));

  // Impact coords
  const [x0, setX0] = useState(0.0);
  const [y0, setY0] = useState(0.0);
  const [z0, setZ0] = useState(0.9);

  // Ball properties (Authoritative Match Ball Standard)
  const [mass, setMass] = useState(0.160);
  const [diameter, setDiameter] = useState(0.0725);

  // Aerodynamics & Environment (Pure Ballistic Benchmark Standard: Cd=0.32, Spin=0)
  const [dragModel, setDragModel] = useState('constant');
  const [cd, setCd] = useState(0.32);
  const [spinX, setSpinX] = useState(0.0);
  const [spinY, setSpinY] = useState(0.0);
  const [spinZ, setSpinZ] = useState(0.0);

  const [windX, setWindX] = useState(0.0);
  const [windY, setWindY] = useState(0.0);
  const [windZ, setWindZ] = useState(0.0);

  // Turf & Stadium (Authoritative Grass Collision Parameters)
  const [restitution, setRestitution] = useState(0.55);
  const [friction, setFriction] = useState(0.38);
  const [rollingCoeff, setRollingCoeff] = useState(0.20);
  const [boundaryShape, setBoundaryShape] = useState('circle');
  const [boundaryRadius, setBoundaryRadius] = useState(70.0);

  // Fielder Athletic Attributes & Mobility Configuration
  const [globalSprintSpeed, setGlobalSprintSpeed] = useState(7.0);
  const [globalReactionTime, setGlobalReactionTime] = useState(0.35);
  const [globalReachRadius, setGlobalReachRadius] = useState(1.8);
  const [globalMinCatchHeight, setGlobalMinCatchHeight] = useState(0.25);
  const [globalMaxCatchHeight, setGlobalMaxCatchHeight] = useState(2.30);
  const [selectedFielderIndex, setSelectedFielderIndex] = useState(8);
  const [mobilityPreset, setMobilityPreset] = useState('elite'); // 'stationary' | 'club' | 'elite' | 'custom'

  const [isSubmitting, setIsSubmitting] = useState(false);

  // Mobility Presets Handler
  const handleSetMobilityPreset = (preset) => {
    setMobilityPreset(preset);
    let sprint = globalSprintSpeed;
    let react = globalReactionTime;
    let reach = globalReachRadius;
    let minZ = globalMinCatchHeight;
    let maxZ = globalMaxCatchHeight;

    if (preset === 'stationary') {
      sprint = 0.0;
      react = 0.35;
      reach = 1.8;
      minZ = 0.25;
      maxZ = 2.30;
    } else if (preset === 'club') {
      sprint = 5.0;
      react = 0.45;
      reach = 1.5;
      minZ = 0.30;
      maxZ = 2.15;
    } else if (preset === 'elite') {
      sprint = 7.0;
      react = 0.35;
      reach = 1.8;
      minZ = 0.25;
      maxZ = 2.30;
    }

    setGlobalSprintSpeed(sprint);
    setGlobalReactionTime(react);
    setGlobalReachRadius(reach);
    setGlobalMinCatchHeight(minZ);
    setGlobalMaxCatchHeight(maxZ);

    setFielders((prev) =>
      prev.map((f) => ({
        ...f,
        max_sprint_speed_m_s: sprint,
        reaction_time_s: react,
        reach_radius_m: reach,
        catching_radius: reach,
        min_catch_height_m: minZ,
        max_catch_height_m: maxZ,
      }))
    );
  };

  // Apply Global Athletic Profile to all 11 fielders
  const handleApplyGlobalToAll = () => {
    setFielders((prev) =>
      prev.map((f) => ({
        ...f,
        max_sprint_speed_m_s: globalSprintSpeed,
        reaction_time_s: globalReactionTime,
        reach_radius_m: globalReachRadius,
        catching_radius: globalReachRadius,
        min_catch_height_m: globalMinCatchHeight,
        max_catch_height_m: globalMaxCatchHeight,
      }))
    );
  };

  // Update selected fielder attribute
  const updateSelectedFielder = (field, value) => {
    setFielders((prev) => {
      const copy = [...prev];
      if (!copy[selectedFielderIndex]) return prev;
      copy[selectedFielderIndex] = {
        ...copy[selectedFielderIndex],
        [field]: value,
      };
      return copy;
    });
  };

  // Calculate ball derived properties
  const ballProps = useMemo(() => {
    return calculateDerivedBallProperties(mass, diameter);
  }, [mass, diameter]);

  // Handle Mode Switch
  const handleModeSwitch = (mode) => {
    if (mode === velocityMode) return;
    if (mode === 'cartesian') {
      const curSpeedMs = speedUnit === 'kmh' ? (parseFloat(speed) || 0) / 3.6 : (parseFloat(speed) || 0);
      const c = anglesToCartesian(curSpeedMs, parseFloat(elevation) || 0, parseFloat(azimuth) || 0);
      setVx(c.vx.toFixed(2));
      setVy(c.vy.toFixed(2));
      setVz(c.vz.toFixed(2));
    } else {
      const a = cartesianToAngles(parseFloat(vx) || 0, parseFloat(vy) || 0, parseFloat(vz) || 0);
      const val = speedUnit === 'kmh' ? (a.speed * 3.6).toFixed(1) : a.speed.toFixed(1);
      setSpeed(val);
      setElevation(parseFloat(a.elevation.toFixed(1)));
      setAzimuth(parseFloat(a.azimuth.toFixed(1)));
    }
    setVelocityMode(mode);
  };

  // Handle Speed Unit Toggle (km/h vs m/s)
  const handleSpeedUnitToggle = (newUnit) => {
    if (newUnit === speedUnit) return;
    const curVal = parseFloat(speed) || 0;
    if (newUnit === 'kmh') {
      setSpeed((curVal * 3.6).toFixed(1));
    } else {
      setSpeed((curVal / 3.6).toFixed(1));
    }
    setSpeedUnit(newUnit);
  };

  // Quick Study Presets for Square Leg & Deep Square Leg Analysis
  const handleLoadStudyTarget = (target, customElev = 45.0) => {
    setSpinX(0.0);
    setSpinY(0.0);
    setSpinZ(0.0);
    setWindX(0.0);
    setWindY(0.0);
    setWindZ(0.0);
    setMass(0.160);
    setDiameter(0.0725);
    setDragModel('constant');
    setCd(0.32);
    setRestitution(0.55);
    setFriction(0.38);
    setRollingCoeff(0.20);
    setBoundaryRadius(70.0);

    if (target === 'square_leg') {
      setName('Square Leg Trajectory Test (52.0 km/h @ 45°, -81.5°)');
      setSpeed(speedUnit === 'kmh' ? '52.0' : '14.4');
      setElevation(45.0);
      setAzimuth(-81.5);
      handleFieldingPresetChange('square_leg_study');
      setSelectedFielderIndex(8);
      setVelocityMode('angles');
    } else if (target === 'deep_square_leg') {
      setName('Deep Square Leg Trajectory Test (102.0 km/h @ 45°, -80.8°)');
      setSpeed(speedUnit === 'kmh' ? '102.0' : '28.3');
      setElevation(45.0);
      setAzimuth(-80.8);
      handleFieldingPresetChange('square_leg_study');
      setSelectedFielderIndex(9);
      setVelocityMode('angles');
    } else if (target === 'square_leg_120') {
      setName('Square Leg 120 km/h Elevation Benchmark (-81.5°)');
      setSpeed(speedUnit === 'kmh' ? '120.0' : '33.3');
      setElevation(customElev !== undefined ? customElev : 40.0);
      setAzimuth(-81.5);
      handleFieldingPresetChange('square_leg_study');
      setSelectedFielderIndex(8);
      setVelocityMode('angles');
    } else if (target === 'deep_square_leg_120') {
      setName('Deep Square Leg 120 km/h Elevation Benchmark (-80.8°)');
      setSpeed(speedUnit === 'kmh' ? '120.0' : '33.3');
      setElevation(customElev !== undefined ? customElev : 40.0);
      setAzimuth(-80.8);
      handleFieldingPresetChange('square_leg_study');
      setSelectedFielderIndex(9);
      setVelocityMode('angles');
    }
  };

  // Handle Turf Preset Change
  const handleTurfChange = (key) => {
    setTurfPreset(key);
    const p = turfPresets[key];
    if (p) {
      setRestitution(p.en);
      setFriction(p.mut);
      setRollingCoeff(p.muRoll);
    }
  };

  // Handle Fielding Preset Change
  const handleFieldingPresetChange = (key) => {
    setFieldingPreset(key);
    if (fieldingPresetsData[key]) {
      setFielders(fieldingPresetsData[key]);
      if (key === 'square_leg_study') {
        setSelectedFielderIndex(8);
      } else {
        setSelectedFielderIndex(0);
      }
    }
  };

  // Reset to Defaults (Pure Ballistic Benchmark Standard)
  const handleReset = () => {
    setName('Lofted Straight Drive (120 km/h)');
    setSpeed(speedUnit === 'kmh' ? '120.0' : '33.3');
    setElevation(30.0);
    setAzimuth(0.0);
    const c = anglesToCartesian(33.33, 30.0, 0.0);
    setVx(c.vx.toFixed(2));
    setVy(c.vy.toFixed(2));
    setVz(c.vz.toFixed(2));
    setX0(0.0);
    setY0(0.0);
    setZ0(0.9);
    setMass(0.160);
    setDiameter(0.0725);
    setDragModel('constant');
    setCd(0.32);
    setSpinX(0.0);
    setSpinY(0.0);
    setSpinZ(0.0);
    setWindX(0.0);
    setWindY(0.0);
    setWindZ(0.0);
    setRestitution(0.55);
    setFriction(0.38);
    setRollingCoeff(0.20);
    setBoundaryShape('circle');
    setBoundaryRadius(70.0);
    handleFieldingPresetChange('square_leg_study');
    setMatchFormat('T20');
    setVelocityMode('angles');
    setGlobalSprintSpeed(7.0);
    setGlobalReactionTime(0.35);
    setGlobalReachRadius(1.8);
    setGlobalMinCatchHeight(0.25);
    setGlobalMaxCatchHeight(2.30);
    setMobilityPreset('elite');
    setSelectedFielderIndex(8);
  };

  // Run Simulation
  const handleSubmit = async () => {
    let finalSpeed;
    let finalElev = parseFloat(elevation) || 0;
    let finalAzim = parseFloat(azimuth) || 0;
    let calcVx, calcVy, calcVz;

    if (velocityMode === 'cartesian') {
      calcVx = parseFloat(vx) || 0;
      calcVy = parseFloat(vy) || 0;
      calcVz = parseFloat(vz) || 0;
      const a = cartesianToAngles(calcVx, calcVy, calcVz);
      finalSpeed = a.speed;
      finalElev = a.elevation;
      finalAzim = a.azimuth;
    } else {
      const rawSpeed = parseFloat(speed) || 0;
      finalSpeed = speedUnit === 'kmh' ? rawSpeed / 3.6 : rawSpeed;
      const c = anglesToCartesian(finalSpeed, finalElev, finalAzim);
      calcVx = c.vx;
      calcVy = c.vy;
      calcVz = c.vz;
      setVx(calcVx.toFixed(2));
      setVy(calcVy.toFixed(2));
      setVz(calcVz.toFixed(2));
    }

    const enrichedFielders = fielders.map((f) => {
      const spd = f.max_sprint_speed_m_s !== undefined ? parseFloat(f.max_sprint_speed_m_s) : globalSprintSpeed;
      const rct = f.reaction_time_s !== undefined ? parseFloat(f.reaction_time_s) : globalReactionTime;
      const rch = f.reach_radius_m !== undefined ? parseFloat(f.reach_radius_m) : (parseFloat(f.catching_radius) || globalReachRadius);
      const minZ = f.min_catch_height_m !== undefined ? parseFloat(f.min_catch_height_m) : globalMinCatchHeight;
      const maxZ = f.max_catch_height_m !== undefined ? parseFloat(f.max_catch_height_m) : globalMaxCatchHeight;
      return {
        ...f,
        max_sprint_speed_m_s: spd,
        sprint_speed_m_s: spd,
        reaction_time_s: rct,
        reach_radius_m: rch,
        catching_radius: rch,
        min_catch_height_m: minZ,
        max_catch_height_m: maxZ,
      };
    });

    const payload = {
      name: name || `Simulation-${Date.now().toString().slice(-4)}`,
      speed: finalSpeed,
      speed_m_s: finalSpeed,
      speed0_kmh: finalSpeed * 3.6,
      elevation: finalElev,
      elevation_deg: finalElev,
      azimuth: finalAzim,
      azimuth_deg: finalAzim,
      vel0: [calcVx, calcVy, calcVz],
      initial_velocity: [calcVx, calcVy, calcVz],
      pos0: [parseFloat(x0) || 0, parseFloat(y0) || 0, parseFloat(z0) || 0.9],
      initial_position: [parseFloat(x0) || 0, parseFloat(y0) || 0, parseFloat(z0) || 0.9],
      ball: {
        mass_kg: parseFloat(mass) || 0.156,
        diameter_m: parseFloat(diameter) || 0.072,
      },
      environment: {
        surface_preset: turfPreset,
        restitution_normal: parseFloat(restitution) || 0.45,
        friction_tangential: parseFloat(friction) || 0.38,
        rolling_resistance_coeff: parseFloat(rollingCoeff) || 0.12,
        wind_vector: [parseFloat(windX) || 0, parseFloat(windY) || 0, parseFloat(windZ) || 0],
        constant_cd: parseFloat(cd) || 0.32,
        drag_model: dragModel,
        enable_magnus: true,
        spin_rad_s: [parseFloat(spinX) || 0, parseFloat(spinY) || 0, parseFloat(spinZ) || 0],
      },
      aerodynamics: {
        drag_model: dragModel,
        cd_base: parseFloat(cd) || 0.32,
        enable_magnus: true,
        spin_vector: [parseFloat(spinX) || 0, parseFloat(spinY) || 0, parseFloat(spinZ) || 0],
      },
      stadium: {
        shape: boundaryShape,
        boundary_radius: parseFloat(boundaryRadius) || 70.0,
      },
      fielders: enrichedFielders,
      fielding: {
        sprint_speed_m_s: globalSprintSpeed,
        max_sprint_speed_m_s: globalSprintSpeed,
        reaction_time_s: globalReactionTime,
        reach_radius_m: globalReachRadius,
        catching_radius: globalReachRadius,
        min_catch_height_m: globalMinCatchHeight,
        max_catch_height_m: globalMaxCatchHeight,
        fielders: enrichedFielders,
      },
    };

    setIsSubmitting(true);
    try {
      const result = await api.runSimulation(payload);
      applySimulationData(result);
      await refreshArchive();
      setActiveTab('tab-ground-view');
    } catch (err) {
      console.error('Simulation execution failed:', err);
      alert(`Simulation failed: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Velocity, Ball, Aerodynamics */}
        <div className="space-y-6">
          {/* Initial Velocity & Launch State */}
          <div className="card p-6 border border-border-color bg-bg-card rounded-xl">
            <div className="flex justify-between items-center pb-3 border-b border-border-color mb-4">
              <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
                <span>🚀</span> Initial Velocity & Launch State
              </h3>

              {/* Mode Toggle */}
              <div className="inline-flex rounded-lg border border-border-color p-0.5 bg-bg-secondary text-xs">
                <button
                  type="button"
                  onClick={() => handleModeSwitch('angles')}
                  className={`px-3 py-1 rounded-md font-medium transition-colors ${
                    velocityMode === 'angles'
                      ? 'bg-accent-primary text-white shadow-sm'
                      : 'text-text-secondary hover:text-text-primary'
                  }`}
                >
                  Speed & Angles
                </button>
                <button
                  type="button"
                  onClick={() => handleModeSwitch('cartesian')}
                  className={`px-3 py-1 rounded-md font-medium transition-colors ${
                    velocityMode === 'cartesian'
                      ? 'bg-accent-primary text-white shadow-sm'
                      : 'text-text-secondary hover:text-text-primary'
                  }`}
                >
                  Cartesian [Vx, Vy, Vz]
                </button>
              </div>
            </div>

            {/* Experiment Name */}
            <div className="mb-4">
              <label className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wide">
                Experiment / Shot Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Lofted Straight Drive (115 km/h) or Cover Boundary"
                className="form-control w-full bg-bg-primary text-text-primary border-border-color py-2 px-3 rounded-md text-sm"
              />
            </div>

            {/* Quick Fielder Study Preset Shortcuts */}
            <div className="mb-4 p-3 bg-bg-secondary rounded-lg border border-border-color/60">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-bold text-accent-cyan flex items-center gap-1.5">
                  <span>🎯</span> Fielder Trajectory Study Shortcuts:
                </span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-sky-500/10 text-accent-cyan border border-sky-500/20">
                  Exact Calibrated Formations
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => handleLoadStudyTarget('square_leg')}
                  className="btn btn-secondary text-xs py-1 px-2.5 flex items-center gap-1.5 hover:border-accent-cyan"
                >
                  <span>🛡️</span>
                  <span>Square Leg Catch (52 km/h @ 45°)</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleLoadStudyTarget('deep_square_leg')}
                  className="btn btn-secondary text-xs py-1 px-2.5 flex items-center gap-1.5 hover:border-accent-cyan"
                >
                  <span>🛡️</span>
                  <span>Deep Sq Leg Catch (102 km/h @ 45°)</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleLoadStudyTarget('square_leg_120', 40.0)}
                  className="btn btn-secondary text-xs py-1 px-2.5 flex items-center gap-1.5 border-accent-cyan/60 text-accent-cyan hover:bg-accent-cyan/10"
                >
                  <span>⚡</span>
                  <span>120 km/h Sq Leg (0 Spin Benchmark)</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleLoadStudyTarget('deep_square_leg_120', 40.0)}
                  className="btn btn-secondary text-xs py-1 px-2.5 flex items-center gap-1.5 border-accent-cyan/60 text-accent-cyan hover:bg-accent-cyan/10"
                >
                  <span>⚡</span>
                  <span>120 km/h Deep Sq Leg (0 Spin Benchmark)</span>
                </button>
              </div>
            </div>

            {/* Input Mode 1: Speed & Angles */}
            {velocityMode === 'angles' ? (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="text-xs font-semibold text-text-secondary">
                      Launch Speed
                    </label>
                    <div className="inline-flex rounded border border-border-color p-0.5 bg-bg-secondary text-[10px]">
                      <button
                        type="button"
                        onClick={() => handleSpeedUnitToggle('kmh')}
                        className={`px-1.5 py-0.5 rounded font-mono font-bold transition-colors ${
                          speedUnit === 'kmh' ? 'bg-accent-primary text-white' : 'text-text-muted hover:text-text-primary'
                        }`}
                      >
                        km/h
                      </button>
                      <button
                        type="button"
                        onClick={() => handleSpeedUnitToggle('ms')}
                        className={`px-1.5 py-0.5 rounded font-mono font-bold transition-colors ${
                          speedUnit === 'ms' ? 'bg-accent-primary text-white' : 'text-text-muted hover:text-text-primary'
                        }`}
                      >
                        m/s
                      </button>
                    </div>
                  </div>
                  <input
                    type="number"
                    step="0.1"
                    value={speed}
                    onChange={(e) => setSpeed(e.target.value)}
                    className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-3 rounded-md text-sm font-mono"
                  />
                  <div className="text-[11px] text-accent-cyan font-mono mt-1">
                    {speedUnit === 'kmh'
                      ? `${((parseFloat(speed) || 0) / 3.6).toFixed(2)} m/s`
                      : `${((parseFloat(speed) || 0) * 3.6).toFixed(1)} km/h`}
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">
                    Elevation θ (deg)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="-10"
                    max="89"
                    value={elevation}
                    onChange={(e) => setElevation(e.target.value)}
                    className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-3 rounded-md text-sm font-mono"
                  />
                  <div className="text-[11px] text-text-muted mt-1">
                    Above horizontal
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">
                    Azimuth φ (deg)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="-180"
                    max="360"
                    value={azimuth}
                    onChange={(e) => setAzimuth(e.target.value)}
                    className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-3 rounded-md text-sm font-mono"
                  />
                  <div className="text-[11px] text-text-muted mt-1">
                    0°=Straight, +45°=Cover
                  </div>
                </div>
              </div>
            ) : (
              /* Input Mode 2: Cartesian Components */
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">
                    Vx (m/s) [Downfield]
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={vx}
                    onChange={(e) => setVx(e.target.value)}
                    className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-3 rounded-md text-sm font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">
                    Vy (m/s) [Lateral (+Off/-Leg)]
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={vy}
                    onChange={(e) => setVy(e.target.value)}
                    className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-3 rounded-md text-sm font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">
                    Vz (m/s) [Vertical]
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={vz}
                    onChange={(e) => setVz(e.target.value)}
                    className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-3 rounded-md text-sm font-mono"
                  />
                </div>
              </div>
            )}

            {/* Initial Coordinates */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4 pt-3 border-t border-border-color/60">
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">
                  Impact X₀ (m) [Crease]
                </label>
                <input
                  type="number"
                  step="0.05"
                  value={x0}
                  onChange={(e) => setX0(e.target.value)}
                  className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-3 rounded-md text-sm font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">
                  Impact Y₀ (m) [Pitch Center]
                </label>
                <input
                  type="number"
                  step="0.05"
                  value={y0}
                  onChange={(e) => setY0(e.target.value)}
                  className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-3 rounded-md text-sm font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">
                  Impact Z₀ (m) [Bat Height]
                </label>
                <input
                  type="number"
                  step="0.05"
                  value={z0}
                  onChange={(e) => setZ0(e.target.value)}
                  className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-3 rounded-md text-sm font-mono"
                />
              </div>
            </div>
          </div>

          {/* Ball Specifications */}
          <div className="card p-6 border border-border-color bg-bg-card rounded-xl">
            <div className="flex justify-between items-center pb-3 border-b border-border-color mb-4">
              <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
                <span>⚾</span> Cricket Ball Specifications
              </h3>
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-sky-500/10 text-accent-cyan border border-sky-500/20">
                Regulation
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">
                  Ball Mass (kg)
                </label>
                <input
                  type="number"
                  step="0.001"
                  min="0.1"
                  max="0.2"
                  value={mass}
                  onChange={(e) => setMass(e.target.value)}
                  className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-3 rounded-md text-sm font-mono"
                />
                <div className="text-[11px] text-text-muted mt-1">Standard: 156–163 g</div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">
                  Diameter (m)
                </label>
                <input
                  type="number"
                  step="0.001"
                  min="0.05"
                  max="0.1"
                  value={diameter}
                  onChange={(e) => setDiameter(e.target.value)}
                  className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-3 rounded-md text-sm font-mono"
                />
                <div className="text-[11px] text-text-muted mt-1">Standard: 71.3–72.9 mm</div>
              </div>
            </div>

            {/* Derived Properties */}
            <div className="p-3 bg-bg-primary rounded-lg border border-border-color flex flex-wrap gap-4 text-xs font-mono">
              <div>
                <span className="text-text-muted font-sans">Radius R: </span>
                <span className="text-accent-cyan font-bold">{ballProps.radius.toFixed(4)} m</span>
              </div>
              <div>
                <span className="text-text-muted font-sans">Area A: </span>
                <span className="text-accent-cyan font-bold">{ballProps.crossSectionArea.toExponential(3)} m²</span>
              </div>
              <div>
                <span className="text-text-muted font-sans">Moment of Inertia I: </span>
                <span className="text-accent-cyan font-bold">{ballProps.momentOfInertia.toExponential(3)} kg·m²</span>
              </div>
            </div>
          </div>

          {/* Aerodynamics & Magnus */}
          <div className="card p-6 border border-border-color bg-bg-card rounded-xl">
            <div className="flex justify-between items-center pb-3 border-b border-border-color mb-4">
              <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
                <span>💨</span> Aerodynamics & Environmental Physics
              </h3>
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-accent-green border border-emerald-500/20">
                Baker (2010)
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">
                  Drag Regime
                </label>
                <select
                  value={dragModel}
                  onChange={(e) => setDragModel(e.target.value)}
                  className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-3 rounded-md text-sm"
                >
                  <option value="reynolds_dependent">Reynolds-dependent Cd(Re) [Baker 2010]</option>
                  <option value="constant">Constant Drag Coefficient</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">
                  Base Drag Coeff (Cd)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.1"
                  max="1.0"
                  value={cd}
                  onChange={(e) => setCd(e.target.value)}
                  className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-3 rounded-md text-sm font-mono"
                />
              </div>
            </div>

            {/* Spin Vector */}
            <div className="mb-4">
              <label className="block text-xs font-semibold text-text-secondary mb-1">
                Angular Spin Vector [ωx, ωy, ωz] (rad/s)
              </label>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <input
                    type="number"
                    step="10"
                    value={spinX}
                    onChange={(e) => setSpinX(e.target.value)}
                    className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-2 rounded-md text-xs font-mono"
                    title="Backspin (+)/Topspin (-)"
                  />
                  <div className="text-[10px] text-text-muted mt-0.5">ωx: Backspin</div>
                </div>
                <div>
                  <input
                    type="number"
                    step="10"
                    value={spinY}
                    onChange={(e) => setSpinY(e.target.value)}
                    className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-2 rounded-md text-xs font-mono"
                    title="Rifle spin"
                  />
                  <div className="text-[10px] text-text-muted mt-0.5">ωy: Rifle</div>
                </div>
                <div>
                  <input
                    type="number"
                    step="10"
                    value={spinZ}
                    onChange={(e) => setSpinZ(e.target.value)}
                    className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-2 rounded-md text-xs font-mono"
                    title="Sidespin"
                  />
                  <div className="text-[10px] text-text-muted mt-0.5">ωz: Sidespin</div>
                </div>
              </div>
            </div>

            {/* Wind Vector */}
            <div>
              <label className="block text-xs font-semibold text-text-secondary mb-1">
                Atmospheric Wind Vector [Wx, Wy, Wz] (m/s)
              </label>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <input
                    type="number"
                    step="0.5"
                    value={windX}
                    onChange={(e) => setWindX(e.target.value)}
                    className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-2 rounded-md text-xs font-mono"
                  />
                  <div className="text-[10px] text-text-muted mt-0.5">Crosswind X</div>
                </div>
                <div>
                  <input
                    type="number"
                    step="0.5"
                    value={windY}
                    onChange={(e) => setWindY(e.target.value)}
                    className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-2 rounded-md text-xs font-mono"
                  />
                  <div className="text-[10px] text-text-muted mt-0.5">Head/Tail Y</div>
                </div>
                <div>
                  <input
                    type="number"
                    step="0.5"
                    value={windZ}
                    onChange={(e) => setWindZ(e.target.value)}
                    className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-2 rounded-md text-xs font-mono"
                  />
                  <div className="text-[10px] text-text-muted mt-0.5">Updraft Z</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Turf, Stadium Geometry, Fielding */}
        <div className="space-y-6">
          {/* Turf & Outfield Ground Interaction */}
          <div className="card p-6 border border-border-color bg-bg-card rounded-xl">
            <div className="flex justify-between items-center pb-3 border-b border-border-color mb-4">
              <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
                <span>🌱</span> Turf & Ground Interaction Presets
              </h3>
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-accent-green border border-emerald-500/20">
                Banerjee (2012)
              </span>
            </div>

            <div className="mb-4">
              <label className="block text-xs font-semibold text-text-secondary mb-1">
                Surface Material Preset
              </label>
              <select
                value={turfPreset}
                onChange={(e) => handleTurfChange(e.target.value)}
                className="form-control w-full bg-bg-primary text-text-primary border-border-color py-2 px-3 rounded-md text-sm"
              >
                <option value="natural_grass">Natural Cricket Outfield (Standard)</option>
                <option value="dry_outfield">Dry Fast Outfield (High bounce, low friction)</option>
                <option value="wet_outfield">Wet Heavy Outfield (Sluggish roll, dead bounce)</option>
                <option value="hard_practice_surface">Hard Synthetic Practice Surface</option>
              </select>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">
                  Restitution (en)
                </label>
                <input
                  type="number"
                  step="0.02"
                  min="0.1"
                  max="0.9"
                  value={restitution}
                  onChange={(e) => setRestitution(e.target.value)}
                  className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-2 rounded-md text-xs font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">
                  Friction (μt)
                </label>
                <input
                  type="number"
                  step="0.02"
                  min="0.1"
                  max="0.8"
                  value={friction}
                  onChange={(e) => setFriction(e.target.value)}
                  className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-2 rounded-md text-xs font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">
                  Rolling (μroll)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.02"
                  max="0.5"
                  value={rollingCoeff}
                  onChange={(e) => setRollingCoeff(e.target.value)}
                  className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-2 rounded-md text-xs font-mono"
                />
              </div>
            </div>
          </div>

          {/* Stadium Geometry */}
          <div className="card p-6 border border-border-color bg-bg-card rounded-xl">
            <div className="flex justify-between items-center pb-3 border-b border-border-color mb-4">
              <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
                <span>🏟️</span> Stadium & Boundary Geometry
              </h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">
                  Boundary Profile
                </label>
                <select
                  value={boundaryShape}
                  onChange={(e) => setBoundaryShape(e.target.value)}
                  className="form-control w-full bg-bg-primary text-text-primary border-border-color py-2 px-3 rounded-md text-sm"
                >
                  <option value="circle">Circular (Uniform radius)</option>
                  <option value="elliptical">Elliptical (Straight vs Square)</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">
                  Boundary Distance (m)
                </label>
                <input
                  type="number"
                  step="1"
                  min="50"
                  max="95"
                  value={boundaryRadius}
                  onChange={(e) => setBoundaryRadius(e.target.value)}
                  className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1.5 px-3 rounded-md text-sm font-mono"
                />
                <div className="text-[11px] text-text-muted mt-1">Standard international: 65–75 m</div>
              </div>
            </div>
          </div>

          {/* Fielding Setup Card */}
          <div className="card p-6 border border-border-color bg-bg-card rounded-xl">
            <div className="flex justify-between items-center pb-3 border-b border-border-color mb-4">
              <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
                <span>🛡️</span> Fielding Positions & Tactics
              </h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">
                  Tactical Preset
                </label>
                <select
                  value={fieldingPreset}
                  onChange={(e) => handleFieldingPresetChange(e.target.value)}
                  className="form-control w-full bg-bg-primary text-text-primary border-border-color py-2 px-3 rounded-md text-sm"
                >
                  <option value="square_leg_study">Square Leg & Deep Sq Leg Focus (Study Setup)</option>
                  <option value="powerplay">T20 Powerplay (2 Deep, 30-yd ring)</option>
                  <option value="attacking">Attacking Test (3 Slips, Gully, Silly Mid-off)</option>
                  <option value="middle_overs">Middle Overs (4 Deep Boundary Sweepers)</option>
                  <option value="death_overs">Death Overs (5 Deep, Boundary Protection)</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">
                  Format Rule Filter
                </label>
                <select
                  value={matchFormat}
                  onChange={(e) => setMatchFormat(e.target.value)}
                  className="form-control w-full bg-bg-primary text-text-primary border-border-color py-2 px-3 rounded-md text-sm"
                >
                  <option value="T20">T20 International (Powerplay ≤ 2 Deep)</option>
                  <option value="ODI">ODI International (Powerplay ≤ 2 Deep)</option>
                  <option value="Test">Test Match (Unrestricted Field)</option>
                </select>
              </div>
            </div>

            {/* 2D Fielding Radar */}
            <div className="mb-5">
              <FieldingRadar 
                boundaryRadius={parseFloat(boundaryRadius) || 70.0} 
                format={matchFormat} 
                selectedFielderIndex={selectedFielderIndex}
                onSelectFielder={(idx) => setSelectedFielderIndex(idx)}
              />
            </div>

            {/* Global Fielder Athletic & Mobility Configuration */}
            <div className="mt-4 pt-4 border-t border-border-color/60 space-y-4">
              <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2">
                <div>
                  <h4 className="text-xs font-bold text-accent-cyan uppercase tracking-wider flex items-center gap-1.5">
                    <Sliders className="w-3.5 h-3.5" />
                    Global Athletic & Mobility Profile
                  </h4>
                  <p className="text-[11px] text-text-muted">
                    Configure fielder athletic capabilities for sprint-based airborne interception.
                  </p>
                </div>
                
                {/* Mobility Presets */}
                <div className="flex flex-wrap items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => handleSetMobilityPreset('stationary')}
                    className={`text-xs px-2.5 py-1 rounded-md font-medium border transition-colors ${
                      mobilityPreset === 'stationary'
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-sm'
                        : 'bg-bg-primary text-text-secondary border-border-color hover:text-text-primary'
                    }`}
                    title="Sprint speed = 0.0 m/s: tests whether ball falls directly into fielder's hands without sprinting"
                  >
                    🛑 Stationary (0.0 m/s)
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSetMobilityPreset('club')}
                    className={`text-xs px-2.5 py-1 rounded-md font-medium border transition-colors ${
                      mobilityPreset === 'club'
                        ? 'bg-sky-500/20 text-sky-300 border-sky-500/40 shadow-sm'
                        : 'bg-bg-primary text-text-secondary border-border-color hover:text-text-primary'
                    }`}
                    title="Sprint speed = 5.0 m/s, reaction time = 0.45s: recreational / club level"
                  >
                    🏃 Club (5.0 m/s)
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSetMobilityPreset('elite')}
                    className={`text-xs px-2.5 py-1 rounded-md font-medium border transition-colors ${
                      mobilityPreset === 'elite'
                        ? 'bg-emerald-500/20 text-accent-green border-emerald-500/40 shadow-sm'
                        : 'bg-bg-primary text-text-secondary border-border-color hover:text-text-primary'
                    }`}
                    title="Sprint speed = 7.0 m/s, reaction time = 0.35s: elite international fielder"
                  >
                    ⚡ Elite (7.0 m/s)
                  </button>
                </div>
              </div>

              {/* Athletic Sliders / Numeric Inputs */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-bg-secondary p-3.5 rounded-lg border border-border-color/60">
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="text-xs font-medium text-text-secondary">
                      Max Sprint Speed (v_max)
                    </label>
                    <span className="text-[11px] font-mono text-accent-cyan font-semibold">
                      {(globalSprintSpeed * 3.6).toFixed(1)} km/h
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min="0.0"
                      max="10.0"
                      step="0.5"
                      value={globalSprintSpeed}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 0;
                        setGlobalSprintSpeed(val);
                        setMobilityPreset('custom');
                      }}
                      className="w-full accent-accent-primary h-1.5 bg-bg-primary rounded-lg cursor-pointer"
                    />
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="12"
                      value={globalSprintSpeed}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 0;
                        setGlobalSprintSpeed(val);
                        setMobilityPreset('custom');
                      }}
                      className="form-control w-20 bg-bg-primary text-text-primary border-border-color py-1 px-2 rounded text-xs font-mono text-right"
                    />
                    <span className="text-[10px] text-text-muted">m/s</span>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="text-xs font-medium text-text-secondary">
                      Reaction Latency (t_react)
                    </label>
                    <span className="text-[11px] font-mono text-text-primary">
                      {globalReactionTime.toFixed(2)} s
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min="0.10"
                      max="0.70"
                      step="0.05"
                      value={globalReactionTime}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 0.35;
                        setGlobalReactionTime(val);
                        setMobilityPreset('custom');
                      }}
                      className="w-full accent-accent-primary h-1.5 bg-bg-primary rounded-lg cursor-pointer"
                    />
                    <input
                      type="number"
                      step="0.05"
                      min="0.05"
                      max="1.0"
                      value={globalReactionTime}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 0.35;
                        setGlobalReactionTime(val);
                        setMobilityPreset('custom');
                      }}
                      className="form-control w-20 bg-bg-primary text-text-primary border-border-color py-1 px-2 rounded text-xs font-mono text-right"
                    />
                    <span className="text-[10px] text-text-muted">s</span>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="text-xs font-medium text-text-secondary">
                      Catch / Dive Reach (r_reach)
                    </label>
                    <span className="text-[11px] font-mono text-text-primary">
                      {globalReachRadius.toFixed(1)} m
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min="0.5"
                      max="3.0"
                      step="0.1"
                      value={globalReachRadius}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 1.8;
                        setGlobalReachRadius(val);
                        setMobilityPreset('custom');
                      }}
                      className="w-full accent-accent-primary h-1.5 bg-bg-primary rounded-lg cursor-pointer"
                    />
                    <input
                      type="number"
                      step="0.1"
                      min="0.5"
                      max="4.0"
                      value={globalReachRadius}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 1.8;
                        setGlobalReachRadius(val);
                        setMobilityPreset('custom');
                      }}
                      className="form-control w-20 bg-bg-primary text-text-primary border-border-color py-1 px-2 rounded text-xs font-mono text-right"
                    />
                    <span className="text-[10px] text-text-muted">m</span>
                  </div>
                </div>
              </div>

              {/* Vertical Catch Window & Apply to All Button */}
              <div className="flex flex-wrap items-center justify-between gap-3 text-xs bg-bg-secondary/60 p-2.5 rounded-lg border border-border-color/40">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="text-text-secondary font-medium">Vertical Catch Window:</span>
                    <span className="text-text-muted">Min</span>
                    <input
                      type="number"
                      step="0.05"
                      min="0.0"
                      max="1.5"
                      value={globalMinCatchHeight}
                      onChange={(e) => setGlobalMinCatchHeight(parseFloat(e.target.value) || 0.25)}
                      className="form-control w-16 bg-bg-primary text-text-primary border-border-color py-0.5 px-1.5 rounded text-xs font-mono text-center"
                    />
                    <span className="text-text-muted">m to Max</span>
                    <input
                      type="number"
                      step="0.05"
                      min="1.5"
                      max="3.5"
                      value={globalMaxCatchHeight}
                      onChange={(e) => setGlobalMaxCatchHeight(parseFloat(e.target.value) || 2.30)}
                      className="form-control w-16 bg-bg-primary text-text-primary border-border-color py-0.5 px-1.5 rounded text-xs font-mono text-center"
                    />
                    <span className="text-text-muted">m (Jump reach)</span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleApplyGlobalToAll}
                  className="btn btn-secondary text-xs py-1 px-3 flex items-center gap-1.5 text-accent-green hover:border-accent-green"
                  title="Applies the above sprint, reaction, and reach parameters to all 11 fielders"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Apply Profile to All 11 Fielders</span>
                </button>
              </div>

              {/* Individual Fielder Inspector & Editor */}
              <div className="mt-4 pt-4 border-t border-border-color/60 space-y-3">
                <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2">
                  <h4 className="text-xs font-bold text-accent-gold uppercase tracking-wider flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5" />
                    Individual Fielder Customization & Coordinates
                  </h4>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-text-secondary font-medium">Select Fielder:</span>
                    <select
                      value={selectedFielderIndex}
                      onChange={(e) => setSelectedFielderIndex(Number(e.target.value))}
                      className="form-control bg-bg-primary text-text-primary border-border-color py-1 px-2.5 rounded text-xs font-medium"
                    >
                      {fielders.map((f, idx) => (
                        <option key={f.id || idx} value={idx}>
                          #{idx + 1} {f.name || f.role} ({f.x}m, {f.y}m)
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Selected Fielder Card */}
                {fielders[selectedFielderIndex] && (() => {
                  const cf = fielders[selectedFielderIndex];
                  const fx = Number(cf.x || 0);
                  const fy = Number(cf.y || 0);
                  const dist = Math.hypot(fx, fy);
                  const azimDeg = (Math.atan2(fy, fx) * 180 / Math.PI).toFixed(1);
                  const isDeepFielder = dist > 27.432;
                  const isOffsideFielder = fy >= 0;

                  return (
                    <div className="p-3.5 bg-bg-secondary rounded-lg border border-border-color/70 space-y-3">
                      <div className="flex flex-wrap justify-between items-center gap-2 pb-2 border-b border-border-color/40">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-text-primary text-xs">
                            {cf.name || cf.role}
                          </span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-bg-primary text-accent-cyan border border-border-color">
                            {cf.role || 'fielder'}
                          </span>
                          <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                            isDeepFielder
                              ? 'bg-purple-500/10 text-purple-400 border-purple-500/20'
                              : 'bg-emerald-500/10 text-accent-green border-emerald-500/20'
                          }`}>
                            {isDeepFielder ? 'Deep Boundary Outfield' : 'Inside 30-Yd Circle'}
                          </span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-bg-primary text-text-muted border border-border-color">
                            {isOffsideFielder ? 'Off-Side (+Y)' : 'Leg-Side (-Y)'}
                          </span>
                        </div>

                        <div className="text-[11px] font-mono text-text-muted">
                          R = <span className="text-text-primary font-bold">{dist.toFixed(1)}m</span> @ <span className="text-text-primary font-bold">{azimDeg}°</span>
                        </div>
                      </div>

                      {/* Coordinates & Custom Attributes Grid */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                        <div>
                          <label className="block text-[11px] font-medium text-text-secondary mb-1">
                            X Coord (Downfield m)
                          </label>
                          <input
                            type="number"
                            step="0.5"
                            value={cf.x}
                            onChange={(e) => updateSelectedFielder('x', parseFloat(e.target.value) || 0)}
                            className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1 px-2 rounded font-mono text-xs"
                          />
                        </div>

                        <div>
                          <label className="block text-[11px] font-medium text-text-secondary mb-1">
                            Y Coord (Lateral m)
                          </label>
                          <input
                            type="number"
                            step="0.5"
                            value={cf.y}
                            onChange={(e) => updateSelectedFielder('y', parseFloat(e.target.value) || 0)}
                            className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1 px-2 rounded font-mono text-xs"
                          />
                        </div>

                        <div>
                          <label className="block text-[11px] font-medium text-text-secondary mb-1 flex justify-between">
                            <span>Sprint (v_max)</span>
                            <span className="text-[10px] text-accent-cyan">
                              {((cf.max_sprint_speed_m_s !== undefined ? cf.max_sprint_speed_m_s : globalSprintSpeed) * 3.6).toFixed(1)} km/h
                            </span>
                          </label>
                          <div className="flex items-center gap-1.5">
                            <input
                              type="number"
                              step="0.5"
                              min="0"
                              max="12"
                              value={cf.max_sprint_speed_m_s !== undefined ? cf.max_sprint_speed_m_s : globalSprintSpeed}
                              onChange={(e) => updateSelectedFielder('max_sprint_speed_m_s', parseFloat(e.target.value) || 0)}
                              className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1 px-2 rounded font-mono text-xs"
                            />
                            <span className="text-[10px] text-text-muted">m/s</span>
                          </div>
                        </div>

                        <div>
                          <label className="block text-[11px] font-medium text-text-secondary mb-1">
                            Catch Radius (reach)
                          </label>
                          <div className="flex items-center gap-1.5">
                            <input
                              type="number"
                              step="0.1"
                              min="0.5"
                              max="4.0"
                              value={cf.reach_radius_m !== undefined ? cf.reach_radius_m : (cf.catching_radius || globalReachRadius)}
                              onChange={(e) => {
                                const val = parseFloat(e.target.value) || 1.8;
                                updateSelectedFielder('reach_radius_m', val);
                                updateSelectedFielder('catching_radius', val);
                              }}
                              className="form-control w-full bg-bg-primary text-text-primary border-border-color py-1 px-2 rounded font-mono text-xs"
                            />
                            <span className="text-[10px] text-text-muted">m</span>
                          </div>
                        </div>
                      </div>

                      {/* Quick Fielder Actions */}
                      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-border-color/40 text-xs">
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => updateSelectedFielder('max_sprint_speed_m_s', 0.0)}
                            className="btn btn-secondary text-[11px] py-1 px-2 text-amber-400 hover:border-amber-400"
                            title="Set this fielder to stationary: tests catch without running"
                          >
                            Set Stationary (0.0 m/s)
                          </button>
                          <button
                            type="button"
                            onClick={() => updateSelectedFielder('max_sprint_speed_m_s', 7.0)}
                            className="btn btn-secondary text-[11px] py-1 px-2 text-accent-green hover:border-accent-green"
                            title="Set this fielder to elite sprint speed (7.0 m/s)"
                          >
                            Set Elite (7.0 m/s)
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              updateSelectedFielder('max_sprint_speed_m_s', globalSprintSpeed);
                              updateSelectedFielder('reaction_time_s', globalReactionTime);
                              updateSelectedFielder('reach_radius_m', globalReachRadius);
                              updateSelectedFielder('catching_radius', globalReachRadius);
                              updateSelectedFielder('min_catch_height_m', globalMinCatchHeight);
                              updateSelectedFielder('max_catch_height_m', globalMaxCatchHeight);
                            }}
                            className="btn btn-secondary text-[11px] py-1 px-2 text-text-muted hover:text-text-primary"
                          >
                            Reset to Global Profile
                          </button>
                        </div>

                        <button
                          type="button"
                          onClick={() => {
                            const curSprint = cf.max_sprint_speed_m_s !== undefined ? cf.max_sprint_speed_m_s : globalSprintSpeed;
                            const curReact = cf.reaction_time_s !== undefined ? cf.reaction_time_s : globalReactionTime;
                            const curReach = cf.reach_radius_m !== undefined ? cf.reach_radius_m : (cf.catching_radius || globalReachRadius);
                            const curMinZ = cf.min_catch_height_m !== undefined ? cf.min_catch_height_m : globalMinCatchHeight;
                            const curMaxZ = cf.max_catch_height_m !== undefined ? cf.max_catch_height_m : globalMaxCatchHeight;

                            setGlobalSprintSpeed(curSprint);
                            setGlobalReactionTime(curReact);
                            setGlobalReachRadius(curReach);
                            setGlobalMinCatchHeight(curMinZ);
                            setGlobalMaxCatchHeight(curMaxZ);

                            setFielders(prev => prev.map(f => ({
                              ...f,
                              max_sprint_speed_m_s: curSprint,
                              reaction_time_s: curReact,
                              reach_radius_m: curReach,
                              catching_radius: curReach,
                              min_catch_height_m: curMinZ,
                              max_catch_height_m: curMaxZ,
                            })));
                          }}
                          className="btn btn-secondary text-[11px] py-1 px-2.5 text-accent-cyan hover:border-accent-cyan flex items-center gap-1"
                          title="Copy this fielder's athletic attributes to all other fielders"
                        >
                          <Users className="w-3 h-3" />
                          <span>Copy This Fielder's Attributes to All</span>
                        </button>
                      </div>
                    </div>
                  );
                })()}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Action Footer */}
      <div className="flex justify-end gap-3 pt-4 border-t border-border-color">
        <button
          type="button"
          onClick={handleReset}
          className="btn btn-secondary text-sm py-2 px-4 flex items-center gap-2"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Reset Defaults</span>
        </button>
        <button
          type="button"
          disabled={isSubmitting}
          onClick={handleSubmit}
          className="btn btn-primary text-sm py-2 px-6 flex items-center gap-2 shadow-lg disabled:opacity-50"
        >
          <Zap className="w-4 h-4 fill-current" />
          <span>{isSubmitting ? 'Calculating Trajectory...' : 'Execute & Predict Trajectory'}</span>
        </button>
      </div>
    </div>
  );
}

