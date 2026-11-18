import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { formatTimestamp, getOutcomeClass } from '../../utils/formatters';
import * as api from '../../services/api';
import { Video, Download, Eye, FileText, Film } from 'lucide-react';

export default function VideosTab() {
  const { 
    activeExperimentId, 
    currentExperiment, 
    loadExperiment, 
    loadDeliveryDetails, 
    refreshArchive 
  } = useApp();

  const [videos, setVideos] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRenderingActive, setIsRenderingActive] = useState(false);
  const [renderingIds, setRenderingIds] = useState(new Set());

  const loadGallery = async () => {
    setIsLoading(true);
    try {
      const data = await api.fetchVideoGallery();
      const list = Array.isArray(data) ? data : (data?.videos || []);
      setVideos(list);
    } catch (err) {
      console.error('Failed to load video gallery:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadGallery();
  }, []);

  const handleRenderActive = async () => {
    const expId = activeExperimentId || currentExperiment?.experiment_id || currentExperiment?.id;
    if (!expId) {
      alert('Please select or run an experiment first before rendering an analytical video.');
      return;
    }

    setIsRenderingActive(true);
    try {
      const res = await api.renderAnalyticalVideo(expId);
      alert(`Analytical broadcast video generated successfully for ${expId}!\nOutput: ${res.video_mp4}`);
      await refreshArchive();
      await loadGallery();
    } catch (err) {
      console.error('Render video failed:', err);
      alert(`Render video failed: ${err.message}`);
    } finally {
      setIsRenderingActive(false);
    }
  };

  const handleRenderSpecific = async (expId) => {
    setRenderingIds((prev) => new Set(prev).add(expId));
    try {
      await api.renderAnalyticalVideo(expId);
      await loadGallery();
    } catch (err) {
      console.error('Render video failed:', err);
      alert(`Render video failed for ${expId}: ${err.message}`);
    } finally {
      setRenderingIds((prev) => {
        const next = new Set(prev);
        next.delete(expId);
        return next;
      });
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Banner & Render Action */}
      <div className="card p-6 border border-border-color bg-bg-card rounded-xl space-y-4">
        <div className="flex justify-between items-center pb-3 border-b border-border-color">
          <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
            <span>🎥</span> Analytical Multi-View Video Export
          </h3>
          <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-sky-500/10 text-accent-cyan border border-sky-500/20">
            Broadcast Quality
          </span>
        </div>

        <p className="text-xs text-text-secondary leading-relaxed">
          Generate comprehensive 4-panel analytical videos combining Isometric 3D, Side Elevation with Apex dimension line, Top-Down Ground view with fielding cordon, and live Telemetry HUD.
        </p>

        <button
          disabled={isRenderingActive}
          onClick={handleRenderActive}
          className="btn btn-primary text-xs py-2.5 px-4 flex items-center gap-2 disabled:opacity-50"
        >
          <Film className="w-4 h-4" />
          <span>{isRenderingActive ? 'Rendering 4-Panel Analytical Video...' : 'Render Multi-View Analytical Video Now'}</span>
        </button>
      </div>

      {/* Video Gallery Archive */}
      <div className="card p-6 border border-border-color bg-bg-card rounded-xl space-y-4">
        <div className="flex justify-between items-center pb-3 border-b border-border-color">
          <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
            <span>🎬</span> Generated Video Archive
          </h3>
          <span className="text-xs font-mono text-text-muted">
            {videos.length} Video Clips
          </span>
        </div>

        {isLoading ? (
          <div className="py-12 text-center text-text-muted text-xs">
            Loading video archive...
          </div>
        ) : videos.length === 0 ? (
          <div className="p-12 text-center text-text-muted bg-bg-secondary rounded-xl border border-dashed border-border-color">
            <div className="text-3xl mb-2">🎬</div>
            <p className="text-sm font-semibold text-text-primary mb-1">No Analytical Videos Rendered Yet</p>
            <p className="text-xs max-w-sm mx-auto">
              Select an experiment from History or run a simulation, then click the render button above to produce a 4-panel analytical Hawkeye video.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {videos.map((v) => (
              <VideoCardItem
                key={v.experiment_id}
                v={v}
                isRendering={renderingIds.has(v.experiment_id)}
                onRender={handleRenderSpecific}
                onDetails={loadDeliveryDetails}
                on3DView={(id) => loadExperiment(id, true, false)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function VideoCardItem({ v, isRendering, onRender, onDetails, on3DView }) {
  const videoRef = useRef(null);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);

  const hasVideo = Boolean(v.has_video && v.video_url);
  const outcome = v.outcome_call || 'IN_PLAY';
  const speedKmh = Number(v.launch_speed_kmh || 0);
  const elev = Number(v.elevation_deg || 0);
  const totalDist = Number(v.total_distance_m || 0);
  const apex = Number(v.max_height_m || 0);

  const handleSpeedChange = (spd) => {
    setPlaybackSpeed(spd);
    if (videoRef.current) {
      videoRef.current.playbackRate = spd;
    }
  };

  return (
    <div className="rounded-xl border border-border-color bg-bg-secondary overflow-hidden flex flex-col justify-between hover:border-accent-primary/40 transition-colors shadow-md">
      {/* Media Header */}
      {hasVideo ? (
        <div className="relative bg-black flex flex-col items-center justify-center">
          <div className="relative w-full aspect-video flex items-center justify-center">
            <video
              ref={videoRef}
              controls
              preload="metadata"
              src={api.resolveAssetUrl(v.video_url)}
              className="w-full h-full object-contain"
            />
            <span className={`outcome-banner ${getOutcomeClass(outcome)} absolute top-2.5 right-2.5 text-[10px] px-2 py-0.5 shadow-md`}>
              {outcome}
            </span>
          </div>

          {/* Video Speed Bar */}
          <div className="w-full bg-bg-card/95 border-t border-border-color/60 px-3 py-1.5 flex items-center justify-between text-xs">
            <span className="text-[11px] font-mono text-text-muted flex items-center gap-1">
              <span>⚡</span> Speed:
            </span>
            <div className="flex items-center gap-1">
              {[0.25, 0.5, 1.0, 1.5, 2.0].map((spd) => {
                const isActive = Math.abs(playbackSpeed - spd) < 0.05;
                return (
                  <button
                    key={spd}
                    type="button"
                    onClick={() => handleSpeedChange(spd)}
                    className={`px-1.5 py-0.5 text-[10px] font-mono rounded transition-colors ${
                      isActive
                        ? 'bg-accent-primary text-white font-bold'
                        : 'bg-bg-secondary text-text-secondary hover:text-text-primary hover:bg-bg-primary'
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
        <div className="relative bg-bg-card aspect-video flex flex-col items-center justify-center text-center p-4 border-b border-border-color">
          <Film className="w-8 h-8 text-text-muted mb-2" />
          <div className="text-xs font-bold text-text-primary mb-1">Video Not Rendered</div>
          <div className="text-[11px] text-text-muted mb-3 max-w-[200px]">
            Render 4-panel Hawkeye video with live HUD and 3D overlays.
          </div>
          <button
            disabled={isRendering}
            onClick={() => onRender(v.experiment_id)}
            className="btn btn-primary text-xs py-1 px-3 flex items-center gap-1.5 disabled:opacity-50"
          >
            <Video className="w-3 h-3" />
            <span>{isRendering ? 'Rendering...' : 'Render Video'}</span>
          </button>
          <span className={`outcome-banner ${getOutcomeClass(outcome)} absolute top-2.5 right-2.5 text-[10px] px-2 py-0.5`}>
            {outcome}
          </span>
        </div>
      )}

      {/* Body Content */}
      <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
        <div>
          <div className="flex justify-between items-baseline mb-1">
            <span
              onClick={() => onDetails(v.experiment_id)}
              className="font-mono text-xs font-bold text-accent-cyan cursor-pointer hover:underline"
            >
              {v.experiment_id}
            </span>
            <span className="text-[11px] text-text-muted font-mono">
              {speedKmh.toFixed(1)} km/h @ {elev.toFixed(1)}°
            </span>
          </div>

          <div className="text-[11px] text-text-muted mb-2">
            📅 {formatTimestamp(v.created_at)}
          </div>

          <h4
            onClick={() => onDetails(v.experiment_id)}
            className="text-sm font-semibold text-text-primary cursor-pointer hover:text-accent-primary transition-colors line-clamp-1"
          >
            {v.name || v.experiment_id}
          </h4>

          <div className="flex gap-4 text-xs text-text-secondary mt-2 font-mono">
            <div>Dist: <strong className="text-text-primary">{totalDist.toFixed(1)}m</strong></div>
            <div>Apex: <strong className="text-accent-gold">{apex.toFixed(1)}m</strong></div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 pt-2 border-t border-border-color/60">
          <button
            onClick={() => onDetails(v.experiment_id)}
            className="btn btn-primary text-[11px] py-1.5 px-2 flex-1 flex items-center justify-center gap-1"
          >
            <FileText className="w-3 h-3" />
            <span>Details</span>
          </button>

          <button
            onClick={() => on3DView(v.experiment_id)}
            className="btn btn-secondary text-[11px] py-1.5 px-2 flex-1 flex items-center justify-center gap-1"
          >
            <Eye className="w-3 h-3" />
            <span>3D View</span>
          </button>

          {hasVideo && (
            <a
              href={api.resolveAssetUrl(v.video_url)}
              download={`${v.experiment_id}_presentation.mp4`}
              className="btn btn-secondary text-[11px] py-1.5 px-2 flex items-center justify-center gap-1"
              title="Download MP4"
            >
              <Download className="w-3 h-3" />
              <span>MP4</span>
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

