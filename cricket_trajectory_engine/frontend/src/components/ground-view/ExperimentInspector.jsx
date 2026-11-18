import React, { useState, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { formatTimestamp, getOutcomeClass } from '../../utils/formatters';
import * as api from '../../services/api';
import { 
  Compass, 
  FolderClock, 
  FileCode2, 
  Video, 
  Trash2, 
  Upload, 
  CheckCircle2, 
  AlertCircle 
} from 'lucide-react';

export default function ExperimentInspector() {
  const { 
    currentExperiment, 
    activeExperimentId, 
    setActiveTab, 
    deleteRecord, 
    loadExperiment,
    refreshArchive 
  } = useApp();

  const fileInputRef = useRef(null);
  const clipVideoRef = useRef(null);
  const [clipSpeed, setClipSpeed] = useState(1.0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState(null);

  const handleClipSpeed = (spd) => {
    setClipSpeed(spd);
    if (clipVideoRef.current) {
      clipVideoRef.current.playbackRate = spd;
    }
  };

  const expId = activeExperimentId || currentExperiment?.experiment_id || currentExperiment?.id || 'EXP-ACTIVE';
  const expName = currentExperiment?.name || currentExperiment?.config?.name || expId;
  const createdAt = currentExperiment?.created_at || currentExperiment?.timestamp || '';
  const outcome = currentExperiment?.results?.outcome_call || currentExperiment?.results?.outcome || 'IN_PLAY';
  const cfg = currentExperiment?.config || {};
  const res = currentExperiment?.results || {};
  const trace = currentExperiment?.calculation_trace || {};

  // Ground Truth Clip
  const hasClip = Boolean(currentExperiment?.has_ground_truth_clip || currentExperiment?.ground_truth_clip_url);
  const rawClipUrl = currentExperiment?.ground_truth_clip_url || (hasClip ? `/artifacts/${encodeURIComponent(expId)}/videos/ground_truth_clip.mp4` : null);
  const clipUrl = api.resolveAssetUrl(rawClipUrl);

  const handleUploadClip = async () => {
    const file = fileInputRef.current?.files?.[0];
    if (!file) {
      alert('Please select an MP4 or WebM video file first.');
      return;
    }

    setIsUploading(true);
    setUploadMessage({ type: 'info', text: `Uploading "${file.name}" (${(file.size / (1024 * 1024)).toFixed(2)} MB)...` });

    try {
      await api.uploadGroundTruthClip(expId, file);
      setUploadMessage({ type: 'success', text: `✔ Ground truth clip saved and verified for ${expId}.` });
      await refreshArchive();
      await loadExperiment(expId, false, false);
    } catch (err) {
      console.error('Upload failed:', err);
      setUploadMessage({ type: 'error', text: `Upload error: ${err.message}` });
    } finally {
      setIsUploading(false);
    }
  };

  // Kinematics calculations
  const vel0 = cfg.vel0 || [0, 0, 0];
  const pos0 = cfg.pos0 || [0, 0, 0.9];
  const speedKmh = Number(cfg.speed0_kmh || (cfg.speed ? cfg.speed * 3.6 : Math.hypot(vel0[0] || 0, vel0[1] || 0, vel0[2] || 0) * 3.6) || 0);
  const speedMs = speedKmh / 3.6;
  const elev = Number(cfg.elevation_deg !== undefined && cfg.elevation_deg !== null ? cfg.elevation_deg : (cfg.elevation || 0));
  const azim = Number(cfg.azimuth_deg !== undefined && cfg.azimuth_deg !== null ? cfg.azimuth_deg : (cfg.azimuth || 0));

  // Ball properties
  const ball = cfg.ball || {};
  const massKg = Number(ball.mass_kg || ball.mass || 0.156);
  const diamM = Number(ball.diameter_m || ball.diameter || 0.072);
  const radiusM = diamM / 2.0;
  const areaM2 = Math.PI * Math.pow(radiusM, 2);
  const moi = 0.4 * massKg * Math.pow(radiusM, 2);

  // Environment & Turf
  const env = cfg.environment || {};
  const aero = cfg.aerodynamics || {};
  const rho = Number(env.air_density_kg_m3 || 1.205);
  const cd = Number(env.constant_cd || aero.cd_base || 0.32);
  const en = Number(env.restitution_normal !== undefined && env.restitution_normal !== null ? env.restitution_normal : 0.45);
  const mut = Number(env.friction_tangential !== undefined && env.friction_tangential !== null ? env.friction_tangential : 0.38);
  const muRoll = Number(env.rolling_resistance_coeff !== undefined && env.rolling_resistance_coeff !== null ? env.rolling_resistance_coeff : 0.12);
  const stadium = cfg.stadium || {};
  const bndRadius = Number(stadium.boundary_radius_m || stadium.boundary_radius || 70.0);
  const spin = aero.spin_vector || env.spin_vector || [0, 0, 0];
  const wind = env.wind_vector || [0, 0, 0];

  // Calculated Results
  const steps = trace.steps || [];
  const stepMap = {};
  steps.forEach((s) => {
    if (s.step_id) stepMap[s.step_id] = s;
  });

  const apex = Number(res.max_height_m || 0);
  const tApex = Number(res.time_to_apex_s || 0);
  const carry = Number(res.carry_distance_m !== undefined && res.carry_distance_m !== null ? res.carry_distance_m : (res.d_pitch || 0));
  const tFlight = Number(res.flight_time_s || 0);

  const pLanding = res.first_landing_pos_m || [0, 0, 0];
  const totalBounces = Number(res.total_bounces || 0);
  const aRoll = -muRoll * 9.80665;
  const rollDist = Number(res.post_bounce_roll_m || 0);
  const totalDist = Number(res.total_distance_m || res.horizontal_distance_m || 0);
  const unconstrainedRoll = Number(res.unconstrained_rollout_m || 0);
  const margin = Number(res.margin_to_rope_m !== undefined && res.margin_to_rope_m !== null ? res.margin_to_rope_m : (totalDist - bndRadius));
  const clears = Boolean(res.clears_rope);
  const resSpeed = res.residual_speed_at_rope_kmh;

  let decisionText = `${outcome} (${res.estimated_runs !== undefined ? res.estimated_runs : 0} Runs)`;
  const fi = res.fielder_interception;
  if (fi) {
    if (fi.can_intercept) {
      decisionText += ` — Caught by ${fi.fielder_name || fi.role_name || 'Fielder'} (${fi.catch_type || 'Catch'}) at t=${Number(fi.catch_time_s || fi.intercept_time_s || 0).toFixed(2)}s`;
    } else if (fi.nearest_fielder) {
      decisionText += ` — ${fi.nearest_fielder.role_name}: ${fi.nearest_fielder.spatial_relationship}`;
    }
  }

  const warnings = res.warnings || [];

  return (
    <div id="experiment-inspector-suite" className="card p-6 border border-border-color bg-bg-card rounded-xl space-y-6 scroll-mt-6">
      {/* Active Experiment Status Header */}
      <div className="flex justify-between items-center pb-4 border-b border-border-color flex-wrap gap-4">
        <div>
          <div className="text-[11px] font-bold uppercase tracking-wider text-accent-cyan flex items-center gap-1.5 mb-1.5">
            <span>📋</span> Detailed Delivery Inspection & Forensic Flight Parameters
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <span className={`outcome-banner ${getOutcomeClass(outcome)} text-xs px-2.5 py-0.5 m-0`}>
              {outcome}
            </span>
            <h3 className="text-lg font-bold text-text-primary">
              {expName}
            </h3>
            <span className="font-mono text-xs px-2 py-0.5 rounded bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20">
              {expId}
            </span>
          </div>
          <div className="text-xs text-text-secondary mt-1 flex items-center gap-2">
            <span>Recorded: <strong className="text-text-primary">{createdAt ? formatTimestamp(createdAt) : 'Live Session'}</strong></span>
            <span className="text-border-color">|</span>
            <span>Storage: <strong className="text-accent-cyan">SQLite Engine (experiments.db)</strong></span>
          </div>
        </div>

        <div className="flex gap-2 items-center flex-wrap">
          <button
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            className="btn btn-primary text-xs py-1.5 px-3 flex items-center gap-1"
          >
            <Compass className="w-3.5 h-3.5" />
            <span>3D Stadium View</span>
          </button>
          <button
            onClick={() => setActiveTab('tab-history')}
            className="btn btn-secondary text-xs py-1.5 px-3 flex items-center gap-1"
          >
            <FolderClock className="w-3.5 h-3.5" />
            <span>Back to History</span>
          </button>
          <button
            onClick={() => setActiveTab('tab-formulas')}
            className="btn btn-secondary text-xs py-1.5 px-3 flex items-center gap-1"
          >
            <FileCode2 className="w-3.5 h-3.5" />
            <span>Full Formula Trace</span>
          </button>
          <button
            onClick={() => setActiveTab('tab-videos')}
            className="btn btn-secondary text-xs py-1.5 px-3 flex items-center gap-1"
          >
            <Video className="w-3.5 h-3.5" />
            <span>Hawkeye Video</span>
          </button>
          <button
            onClick={() => deleteRecord(expId)}
            className="btn btn-danger text-xs py-1.5 px-3 flex items-center gap-1"
            title="Delete this delivery record from database"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Delete</span>
          </button>
        </div>
      </div>

      {/* Ground Truth Video & Upload Section */}
      <div className="p-4 rounded-lg bg-bg-secondary border border-border-color">
        <div className="flex justify-between items-center mb-3 pb-2 border-b border-border-color">
          <h4 className="text-sm font-bold text-text-primary flex items-center gap-2">
            <span>🎥</span> Ground Truth Camera Footage & Match Clip Verification
          </h4>
          <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
            hasClip 
              ? 'bg-emerald-500/15 text-accent-green border-emerald-500/30' 
              : 'text-text-muted border-border-color'
          }`}>
            {hasClip ? '● Clip Available' : '○ No Clip'}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
          {/* Player or Placeholder */}
          <div className="bg-black rounded-lg overflow-hidden border border-border-color min-h-[220px] flex flex-col items-center justify-center">
            {hasClip && clipUrl ? (
              <div className="w-full flex flex-col">
                <video
                  ref={clipVideoRef}
                  controls
                  preload="metadata"
                  playsInline
                  src={clipUrl}
                  className="w-full max-h-[260px] block object-contain bg-black"
                />
                <div className="w-full bg-bg-card border-t border-border-color px-3 py-1.5 flex items-center justify-between text-xs">
                  <span className="text-[11px] font-mono text-text-muted flex items-center gap-1">
                    <span>⚡</span> Speed:
                  </span>
                  <div className="flex items-center gap-1">
                    {[0.25, 0.5, 1.0, 1.5, 2.0].map((spd) => {
                      const isActive = Math.abs(clipSpeed - spd) < 0.05;
                      return (
                        <button
                          key={spd}
                          type="button"
                          onClick={() => handleClipSpeed(spd)}
                          className={`px-1.5 py-0.5 text-[10px] font-mono rounded transition-colors ${
                            isActive
                              ? 'bg-accent-primary text-white font-bold'
                              : 'bg-bg-secondary text-text-secondary hover:text-text-primary'
                          }`}
                          title={`Set video speed to ${spd}x`}
                        >
                          {spd}x
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center p-6 text-text-muted">
                <div className="text-3xl mb-2">📹</div>
                <div className="font-semibold text-text-primary text-sm mb-1">
                  No Real-World Camera Clip Attached Yet
                </div>
                <div className="text-xs max-w-xs mx-auto leading-relaxed">
                  Upload the broadcast footage or camera clip for this ball to inspect physical ground truth alongside the 3D trajectory engine.
                </div>
              </div>
            )}
          </div>

          {/* Verification Details & Upload Controls */}
          <div className="flex flex-col justify-between h-full space-y-4">
            <div>
              <div className="text-xs font-semibold text-text-primary mb-1">
                Ground Truth Comparison Protocol
              </div>
              <p className="text-xs text-text-secondary leading-relaxed mb-3">
                All 10 pre-seeded real deliveries include broadcast camera footage (<code className="text-accent-cyan">clip_cam1.mp4</code> / <code className="text-accent-cyan">clip_cam2.mp4</code>). For any new experiment, you can optionally upload a video clip to link physical ground truth directly with the simulation record.
              </p>

              {hasClip && (
                <div className="p-2.5 rounded bg-sky-500/10 border border-sky-500/30 text-xs">
                  <div className="text-accent-cyan font-semibold mb-0.5 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Match Video Clip Linked & Verified
                  </div>
                  <div className="font-mono text-[11px] text-text-muted break-all">
                    {clipUrl}
                  </div>
                </div>
              )}
            </div>

            {/* Upload Box */}
            <div className="p-3 bg-bg-card rounded-lg border border-dashed border-border-color">
              <label className="block text-xs font-semibold text-text-primary mb-1.5">
                Attach / Replace Match Clip (MP4 / WebM)
              </label>
              <input
                ref={fileInputRef}
                type="file"
                accept="video/mp4,video/webm,video/quicktime"
                className="form-control text-xs w-full bg-bg-primary text-text-primary border-border-color py-1 px-2 rounded mb-2"
              />
              <div className="flex gap-2 items-center">
                <button
                  disabled={isUploading}
                  onClick={handleUploadClip}
                  className="btn btn-primary text-xs py-1.5 px-3 flex items-center gap-1.5 disabled:opacity-50"
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span>{isUploading ? 'Uploading...' : 'Upload Match Clip'}</span>
                </button>
              </div>
              {uploadMessage && (
                <div className={`text-[11px] mt-1.5 font-medium ${
                  uploadMessage.type === 'success' ? 'text-accent-green' : uploadMessage.type === 'error' ? 'text-accent-red' : 'text-accent-cyan'
                }`}>
                  {uploadMessage.text}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Two-Column Forensic Inspector: Inputs vs Calculations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Authoritative Inputs */}
        <div className="card p-5 border border-border-color bg-bg-secondary rounded-xl space-y-4">
          <div className="flex justify-between items-center pb-2.5 border-b border-border-color">
            <h4 className="text-sm font-bold text-accent-cyan flex items-center gap-2">
              <span>📥</span> Input Data Used in Simulation
            </h4>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20">
              Authoritative Inputs
            </span>
          </div>

          {/* 1. Launch Kinematics */}
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-text-muted mb-2">
              1. Launch Kinematics & Release State
            </div>
            <table className="w-full text-xs">
              <tbody className="divide-y divide-border-color/40">
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Launch Speed (v₀)</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">{speedKmh.toFixed(2)} km/h ({speedMs.toFixed(2)} m/s)</td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Elevation Angle (θ)</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">{elev.toFixed(2)}°</td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Azimuth Angle (φ)</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">{azim.toFixed(2)}°</td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Initial Velocity Vector (v⃗₀)</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">[{Number(vel0[0] || 0).toFixed(3)}, {Number(vel0[1] || 0).toFixed(3)}, {Number(vel0[2] || 0).toFixed(3)}] m/s</td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Initial Release Coords (r⃗₀)</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">[{Number(pos0[0] || 0).toFixed(3)}, {Number(pos0[1] || 0).toFixed(3)}, {Number(pos0[2] || 0).toFixed(3)}] m</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* 2. Ball Specifications */}
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-text-muted mb-2">
              2. Cricket Ball Specifications
            </div>
            <table className="w-full text-xs">
              <tbody className="divide-y divide-border-color/40">
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Ball Mass (m)</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">{(massKg * 1000).toFixed(1)} g ({massKg.toFixed(3)} kg)</td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Diameter (d) & Radius (R)</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">{(diamM * 100).toFixed(2)} cm (R = {(radiusM * 100).toFixed(2)} cm)</td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Cross-Sectional Area (A = πR²)</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">{areaM2.toExponential(4)} m²</td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Moment of Inertia (I = ⅖mR²)</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">{moi.toExponential(4)} kg·m²</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* 3. Environment & Stadium */}
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-text-muted mb-2">
              3. Atmosphere, Turf & Stadium Geometry
            </div>
            <table className="w-full text-xs">
              <tbody className="divide-y divide-border-color/40">
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Air Density (ρ) & Base Cd</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">ρ = {rho.toFixed(3)} kg/m³ | Cd = {cd.toFixed(3)}</td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Turf Restitution (en) & Friction (μt)</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">en = {en.toFixed(2)} | μt = {mut.toFixed(2)}</td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Rolling Resistance (μ_roll)</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">μ_roll = {muRoll.toFixed(3)}</td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Boundary Rope Radius (R_bnd)</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">{bndRadius.toFixed(1)} m</td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Wind Vector & Spin Dynamics</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">Spin: [{spin[0]}, {spin[1]}, {spin[2]}] | Wind: [{wind[0]}, {wind[1]}, {wind[2]}]</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: Calculated Results */}
        <div className="card p-5 border border-border-color bg-bg-secondary rounded-xl space-y-4">
          <div className="flex justify-between items-center pb-2.5 border-b border-border-color">
            <h4 className="text-sm font-bold text-accent-gold flex items-center gap-2">
              <span>🧮</span> Mathematical Calculations & Derivations
            </h4>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-accent-green border border-emerald-500/20">
              Physics Trace
            </span>
          </div>

          {/* 1. Aerodynamics & Flight Arc */}
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-text-muted mb-2">
              1. Aerodynamics & Flight Arc
            </div>
            <table className="w-full text-xs">
              <tbody className="divide-y divide-border-color/40">
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Reynolds Number (Re)</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">
                    {stepMap['step_reynolds_number']?.result_formatted || `${((rho * speedMs * diamM) / 1.81e-5).toExponential(2)}`}
                  </td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Aerodynamic Drag Force (|F⃗_D|)</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">
                    {stepMap['step_aerodynamic_drag']?.result_formatted || `${(0.5 * rho * cd * areaM2 * Math.pow(speedMs, 2)).toFixed(3)} N`}
                  </td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Maximum Apex Height (z_max)</td>
                  <td className="py-1.5 text-right font-mono text-accent-gold font-bold">{apex.toFixed(2)} m</td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Time to Apex (t_apex)</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">{tApex.toFixed(3)} s</td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Carry Distance (1st Pitch Landing)</td>
                  <td className="py-1.5 text-right font-mono text-sky-400 font-bold">{carry.toFixed(2)} m</td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Flight Duration to Pitch (t_flight)</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">{tFlight.toFixed(3)} s</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* 2. Pitch Impact & Energy Loss */}
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-text-muted mb-2">
              2. Pitch Impact & Energy Loss
            </div>
            <table className="w-full text-xs">
              <tbody className="divide-y divide-border-color/40">
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">1st Pitch Impact Coords</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">[{Number(pLanding[0] || 0).toFixed(2)}, {Number(pLanding[1] || 0).toFixed(2)}, {Number(pLanding[2] || 0).toFixed(2)}] m</td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Total Bounces Detected</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">{totalBounces} bounce{totalBounces === 1 ? '' : 's'}</td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Rebound Restitution Impact</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">en = {en.toFixed(2)}</td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Kinetic Energy Dissipation</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">{((1.0 - Math.pow(en, 2)) * 100.0).toFixed(1)}% kinetic loss</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* 3. Outfield Rollout & Decision Rule */}
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-text-muted mb-2">
              3. Outfield Rollout & Decision Rule
            </div>
            <table className="w-full text-xs">
              <tbody className="divide-y divide-border-color/40">
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Turf Deceleration (a_roll)</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">{aRoll.toFixed(3)} m/s²</td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Post-Bounce Rollout Distance</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">
                    {outcome.includes('FOUR') && unconstrainedRoll > totalDist
                      ? `${rollDist.toFixed(2)} m (Capped at rope)`
                      : `${rollDist.toFixed(2)} m`}
                  </td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Total Distance Traveled</td>
                  <td className="py-1.5 text-right font-mono font-bold text-text-primary">{totalDist.toFixed(2)} m</td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Boundary Clearance Margin</td>
                  <td className="py-1.5 text-right font-mono text-text-primary">
                    {clears ? `+${Math.abs(margin).toFixed(2)} m (cleared)` : `-${Math.abs(margin).toFixed(2)} m (short)`}
                  </td>
                </tr>
                <tr>
                  <td className="py-1.5 text-text-secondary font-medium">Official Umpire Decision</td>
                  <td className="py-1.5 text-right font-bold text-accent-green">{decisionText}</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* 4. Fielder Interception & Catch Zone Analysis */}
          {fi && (
            <div>
              <div className="text-[11px] font-bold uppercase tracking-wider text-text-muted mb-2 flex items-center justify-between">
                <span>4. Fielder Interception & Spatial Catch Zone</span>
                {fi.can_intercept ? (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-accent-green border border-emerald-500/20 font-mono">
                    Interception Confirmed
                  </span>
                ) : (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono">
                    Ball Grounded / In-Play
                  </span>
                )}
              </div>
              <table className="w-full text-xs">
                <tbody className="divide-y divide-border-color/40">
                  <tr>
                    <td className="py-1.5 text-text-secondary font-medium">Nearest Tactical Fielder</td>
                    <td className="py-1.5 text-right font-mono text-text-primary font-bold">
                      {fi.nearest_fielder?.role_name || fi.fielder_name || fi.role_name || 'Fielder'}
                      {fi.nearest_fielder?.fielder_coords && (
                        <span className="text-text-muted font-normal text-[11px] ml-1.5">
                          [{fi.nearest_fielder.fielder_coords[0]}m, {fi.nearest_fielder.fielder_coords[1]}m]
                        </span>
                      )}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-1.5 text-text-secondary font-medium">Distance from Landing to Fielder</td>
                    <td className="py-1.5 text-right font-mono text-sky-400 font-bold">
                      {fi.nearest_fielder?.distance_to_landing_m !== undefined
                        ? `${fi.nearest_fielder.distance_to_landing_m.toFixed(2)} m`
                        : 'N/A'}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-1.5 text-text-secondary font-medium">Spatial Trajectory Relationship</td>
                    <td className="py-1.5 text-right font-mono text-text-primary font-semibold">
                      {fi.nearest_fielder?.spatial_relationship || (fi.can_intercept ? 'In Reach' : 'Grounded')}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-1.5 text-text-secondary font-medium">Interception Classification</td>
                    <td className="py-1.5 text-right font-mono font-bold text-accent-cyan">
                      {fi.can_intercept
                        ? `${fi.catch_type || 'Catch'} at t=${Number(fi.catch_time_s || fi.intercept_time_s || 0).toFixed(2)}s`
                        : 'Unintercepted (Pitched In-Play)'}
                    </td>
                  </tr>
                  {fi.can_intercept && (
                    <tr>
                      <td className="py-1.5 text-text-secondary font-medium">Required Fielder Sprint Speed</td>
                      <td className="py-1.5 text-right font-mono text-text-primary">
                        {Number(fi.required_speed_m_s || 0) <= 0.1
                          ? '0.00 m/s (Direct into hands / Stationary catch)'
                          : `${Number(fi.required_speed_m_s).toFixed(2)} m/s (Fielder sprint required)`}
                      </td>
                    </tr>
                  )}
                  {fi.nearest_fielder && (
                    <tr>
                      <td className="py-1.5 text-text-secondary font-medium">Configured Fielder Capabilities</td>
                      <td className="py-1.5 text-right font-mono text-text-primary text-[11px]">
                        Sprint: {fi.nearest_fielder.max_sprint_speed_m_s !== undefined ? `${Number(fi.nearest_fielder.max_sprint_speed_m_s).toFixed(1)} m/s` : '7.0 m/s'} | Reach: {fi.nearest_fielder.reach_radius_m !== undefined ? `${Number(fi.nearest_fielder.reach_radius_m).toFixed(1)} m` : '1.8 m'} | React: {fi.nearest_fielder.reaction_time_s !== undefined ? `${Number(fi.nearest_fielder.reaction_time_s).toFixed(2)} s` : '0.35 s'}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Physical Rationale & Scientific Notes Banner */}
      <div className="p-4 rounded-lg bg-sky-500/5 border border-border-color text-xs leading-relaxed space-y-1.5">
        <div className="font-semibold text-accent-cyan flex items-center gap-1.5">
          <span>📌</span> Physical Rationale & Scientific Derivation Notes:
        </div>
        <ul className="list-disc pl-5 text-text-secondary space-y-1">
          {warnings.length > 0 ? (
            warnings.map((w, idx) => <li key={idx}>{w}</li>)
          ) : (
            <li>
              Clean physical trajectory integration using standard Runge-Kutta 4th/5th-order Dormand-Prince solver (RK45) under MCC Laws. Boundary radius R = {bndRadius.toFixed(1)} m.
            </li>
          )}
        </ul>
      </div>
    </div>
  );
}

