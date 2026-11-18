import React from 'react';
import { useApp } from '../../context/AppContext';
import { formatTimestamp, getOutcomeClass, isDeliveryRecord } from '../../utils/formatters';
import { RotateCw, Search, Video, Eye, FileText, Trash2 } from 'lucide-react';

export default function HistoryTab() {
  const { 
    allExperiments, 
    historyFilter, 
    setHistoryFilter, 
    historySearchQuery, 
    setHistorySearchQuery, 
    loadExperiment, 
    loadDeliveryDetails, 
    deleteRecord, 
    refreshArchive 
  } = useApp();

  // Filter & Search Logic
  const query = (historySearchQuery || '').trim().toLowerCase();
  const deliveriesCount = allExperiments.filter((e) => isDeliveryRecord(e)).length;
  const customCount = allExperiments.length - deliveriesCount;

  const filtered = allExperiments.filter((exp) => {
    const isDeliv = isDeliveryRecord(exp);
    if (historyFilter === 'deliveries' && !isDeliv) return false;
    if (historyFilter === 'custom' && isDeliv) return false;

    if (query) {
      const id = (exp.id || exp.experiment_id || '').toLowerCase();
      const name = (exp.name || '').toLowerCase();
      const outcome = (exp.outcome_call || exp.summary?.outcome || '').toLowerCase();
      const desc = (exp.description || '').toLowerCase();
      return id.includes(query) || name.includes(query) || outcome.includes(query) || desc.includes(query);
    }
    return true;
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="card p-6 border border-border-color bg-bg-card rounded-xl space-y-4">
        {/* Header */}
        <div className="flex justify-between items-center pb-3 border-b border-border-color flex-wrap gap-2">
          <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
            <span>📁</span> Persisted Simulation Archive
          </h3>
          <button
            onClick={() => refreshArchive()}
            className="btn btn-secondary text-xs py-1.5 px-3 flex items-center gap-1.5"
          >
            <RotateCw className="w-3.5 h-3.5" />
            <span>Refresh List</span>
          </button>
        </div>

        {/* Filter Buttons & Live Search */}
        <div className="flex justify-between items-center flex-wrap gap-3 p-3 bg-bg-secondary rounded-lg border border-border-color">
          <div className="flex gap-2 items-center flex-wrap">
            <button
              onClick={() => setHistoryFilter('all')}
              className={`text-xs px-3 py-1.5 rounded-md font-medium transition-colors ${
                historyFilter === 'all'
                  ? 'bg-accent-primary text-white shadow-sm'
                  : 'bg-bg-card text-text-secondary hover:text-text-primary border border-border-color'
              }`}
            >
              All Records ({allExperiments.length})
            </button>
            <button
              onClick={() => setHistoryFilter('deliveries')}
              className={`text-xs px-3 py-1.5 rounded-md font-medium transition-colors ${
                historyFilter === 'deliveries'
                  ? 'bg-accent-primary text-white shadow-sm'
                  : 'bg-bg-card text-text-secondary hover:text-text-primary border border-border-color'
              }`}
            >
              🏏 Real Match Deliveries ({deliveriesCount})
            </button>
            <button
              onClick={() => setHistoryFilter('custom')}
              className={`text-xs px-3 py-1.5 rounded-md font-medium transition-colors ${
                historyFilter === 'custom'
                  ? 'bg-accent-primary text-white shadow-sm'
                  : 'bg-bg-card text-text-secondary hover:text-text-primary border border-border-color'
              }`}
            >
              🔬 Custom Simulations ({customCount})
            </button>
          </div>

          <div className="relative min-w-[260px] flex-1 sm:flex-initial">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input
              type="text"
              value={historySearchQuery}
              onChange={(e) => setHistorySearchQuery(e.target.value)}
              placeholder="Search deliveries, IDs, outcomes..."
              className="form-control w-full bg-bg-card text-text-primary border-border-color pl-8 pr-3 py-1.5 rounded-md text-xs"
            />
          </div>
        </div>

        {/* Guidance Note */}
        <div className="p-3 rounded-lg bg-sky-500/10 border border-sky-500/20 text-xs text-text-secondary flex items-start gap-2.5">
          <span className="text-base select-none">💡</span>
          <div className="leading-relaxed">
            <strong className="text-text-primary">Quick Navigation: </strong>
            Tap or click anywhere on any delivery row (or click <strong>📋 Details</strong>) to inspect the complete flight report, launch physics, kinematics, and real ground-truth video. Click <strong>🏟️ 3D View</strong> to watch the ball trajectory in the stadium. Use <strong>🗑️ Delete</strong> to remove records from SQLite storage.
          </div>
        </div>

        {/* Table Container */}
        <div className="overflow-x-auto rounded-lg border border-border-color bg-bg-card shadow-lg">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-border-color bg-bg-secondary text-text-muted font-mono uppercase tracking-wider text-[11px]">
                <th className="py-3 px-4 min-w-[170px]">Delivery / ID</th>
                <th className="py-3 px-4 min-w-[140px]">Date & Time</th>
                <th className="py-3 px-4 min-w-[190px]">Name / Scenario</th>
                <th className="py-3 px-4 min-w-[110px]">Launch Speed</th>
                <th className="py-3 px-4 min-w-[110px]">Angles (θ, φ)</th>
                <th className="py-3 px-4 min-w-[85px]">Apex</th>
                <th className="py-3 px-4 min-w-[95px]">Distance</th>
                <th className="py-3 px-4 min-w-[110px]">Outcome</th>
                <th className="py-3 px-4 min-w-[110px]">Ground Truth</th>
                <th className="py-3 px-4 min-w-[100px]">Storage</th>
                <th className="py-3 px-4 min-w-[210px] text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-color/40">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={11} className="text-center py-8 text-text-muted">
                    No simulation records match the selected filter or search query.
                  </td>
                </tr>
              ) : (
                filtered.map((exp) => {
                  const expId = exp.id || exp.experiment_id || 'EXP';
                  const speedKmh = Number(exp.launch_speed_kmh || (exp.summary?.launch_speed_m_s ? exp.summary.launch_speed_m_s * 3.6 : 0) || 0);
                  const elev = Number(exp.elevation_deg !== undefined && exp.elevation_deg !== null ? exp.elevation_deg : (exp.summary?.elevation_deg || 0));
                  const azim = Number(exp.azimuth_deg !== undefined && exp.azimuth_deg !== null ? exp.azimuth_deg : (exp.summary?.azimuth_deg || 0));
                  const apex = Number(exp.max_height_m !== undefined && exp.max_height_m !== null ? exp.max_height_m : (exp.summary?.max_height_m || 0));
                  const dist = Number(exp.total_distance_m !== undefined && exp.total_distance_m !== null ? exp.total_distance_m : (exp.summary?.total_distance_m || exp.summary?.horizontal_distance_m || 0));
                  const outcome = exp.outcome_call || exp.summary?.outcome || 'IN_PLAY';
                  const createdAt = exp.created_at || exp.timestamp || '';
                  const isDeliv = isDeliveryRecord(exp);
                  const hasGtClip = Boolean(exp.has_ground_truth_clip);

                  return (
                    <tr
                      key={expId}
                      onClick={() => loadDeliveryDetails(expId)}
                      className="hover:bg-bg-card-hover/80 cursor-pointer transition-colors group"
                      title={`Click to view detailed report, parameters, and match clip for ${expId}`}
                    >
                      {/* ID */}
                      <td className="py-3 px-4 font-mono font-bold whitespace-nowrap">
                        <span className="text-accent-cyan group-hover:underline">
                          {expId}
                        </span>
                        {isDeliv && (
                          <span className="ml-2 text-[10px] font-mono px-1.5 py-0.5 rounded bg-sky-500/15 text-accent-cyan border border-sky-500/30">
                            🏏 Match
                          </span>
                        )}
                      </td>

                      {/* Date */}
                      <td className="py-3 px-4 text-text-muted whitespace-nowrap">
                        {formatTimestamp(createdAt)}
                      </td>

                      {/* Name */}
                      <td className="py-3 px-4 font-medium text-text-primary whitespace-normal max-w-[200px]">
                        {exp.name || expId}
                      </td>

                      {/* Speed */}
                      <td className="py-3 px-4 font-mono whitespace-nowrap">
                        {speedKmh.toFixed(1)} km/h
                      </td>

                      {/* Angles */}
                      <td className="py-3 px-4 font-mono whitespace-nowrap">
                        {elev.toFixed(1)}°, {azim.toFixed(1)}°
                      </td>

                      {/* Apex */}
                      <td className="py-3 px-4 font-mono font-semibold text-accent-gold whitespace-nowrap">
                        {apex.toFixed(1)} m
                      </td>

                      {/* Distance */}
                      <td className="py-3 px-4 font-mono font-semibold text-text-primary whitespace-nowrap">
                        {dist.toFixed(1)} m
                      </td>

                      {/* Outcome */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className={`outcome-banner ${getOutcomeClass(outcome)} text-[11px] px-2 py-0.5`}>
                          {outcome}
                        </span>
                      </td>

                      {/* Ground Truth */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        {hasGtClip ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-accent-green border border-emerald-500/30">
                            <Video className="w-3 h-3" />
                            Clip Avail
                          </span>
                        ) : (
                          <span className="text-text-muted text-[11px]">○ No clip</span>
                        )}
                      </td>

                      {/* Storage */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${
                          isDeliv
                            ? 'bg-sky-500/10 text-accent-cyan border-sky-500/30'
                            : 'bg-emerald-500/10 text-accent-green border-emerald-500/30'
                        }`}>
                          {isDeliv ? 'SQLite Match' : 'SQLite DB'}
                        </span>
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-4 whitespace-nowrap text-center">
                        <div
                          className="flex gap-1.5 justify-center items-center"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <button
                            type="button"
                            onClick={() => loadDeliveryDetails(expId)}
                            className="btn btn-primary text-[11px] py-1 px-2 flex items-center gap-1"
                            title="Inspect Detailed Report, Kinematics, Video & Formulas"
                          >
                            <FileText className="w-3 h-3" />
                            <span>Details</span>
                          </button>

                          <button
                            type="button"
                            onClick={() => loadExperiment(expId, true, false)}
                            className="btn btn-secondary text-[11px] py-1 px-2 flex items-center gap-1"
                            title="View in 3D Stadium Visualizer"
                          >
                            <Eye className="w-3 h-3" />
                            <span>3D View</span>
                          </button>

                          <button
                            type="button"
                            onClick={() => deleteRecord(expId)}
                            className="btn btn-danger text-[11px] py-1 px-2 flex items-center gap-1"
                            title="Delete this record permanently from database"
                          >
                            <Trash2 className="w-3 h-3" />
                            <span>Delete</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

