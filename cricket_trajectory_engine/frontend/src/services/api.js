/**
 * Centralized API Service for Cricket Trajectory Platform
 */

export const API_BASE = (typeof window !== "undefined" && window.location.port === "5173")
  ? `http://${window.location.hostname}:8000`
  : "";

export function resolveAssetUrl(url) {
  if (!url) return url;
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  return `${API_BASE}${url.startsWith("/") ? "" : "/"}${url}`;
}

export async function runSimulation(config) {
  const res = await fetch(`${API_BASE}/api/simulation/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Simulation failed with HTTP ${res.status}`);
  }
  return await res.json();
}

export async function fetchExperiments() {
  const res = await fetch(`${API_BASE}/api/experiments`);
  if (!res.ok) {
    throw new Error(`Failed to fetch experiments archive: ${res.statusText}`);
  }
  const data = await res.json();
  return Array.isArray(data) ? data : (data.experiments || []);
}

export async function fetchExperimentById(id) {
  const res = await fetch(`${API_BASE}/api/experiments/${encodeURIComponent(id)}`);
  if (!res.ok) {
    throw new Error(`Experiment ${id} not found (${res.status})`);
  }
  return await res.json();
}

export async function deleteExperiment(id) {
  const res = await fetch(`${API_BASE}/api/experiments/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to delete experiment: ${res.statusText}`);
  }
  return await res.json();
}

export async function uploadGroundTruthClip(id, file) {
  const res = await fetch(`${API_BASE}/api/experiments/${encodeURIComponent(id)}/upload_clip`, {
    method: "POST",
    headers: {
      "Content-Type": file.type || "video/mp4",
    },
    body: file,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Upload failed with status ${res.status}`);
  }
  return await res.json();
}

export async function renderAnalyticalVideo(id) {
  const res = await fetch(`${API_BASE}/api/experiments/${encodeURIComponent(id)}/render_video`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Video render failed with status ${res.status}`);
  }
  return await res.json();
}

export async function fetchComparison(idA, idB) {
  let ids = [];
  if (Array.isArray(idA)) {
    ids.push(...idA);
  } else if (idA) {
    ids.push(idA);
  }
  if (Array.isArray(idB)) {
    ids.push(...idB);
  } else if (idB) {
    ids.push(idB);
  }
  // Ensure flat array of non-empty strings
  const flatIds = ids.flat(Infinity).filter((x) => typeof x === "string" && x.trim().length > 0);
  if (flatIds.length === 1) {
    flatIds.push(flatIds[0]);
  }
  const baseline = flatIds[0] || "";
  const res = await fetch(`${API_BASE}/api/comparison`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ experiment_ids: flatIds, baseline_id: baseline }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Comparison failed: ${res.statusText}`);
  }
  return await res.json();
}

export async function fetchVideoGallery() {
  const res = await fetch(`${API_BASE}/api/experiments/gallery/videos`);
  if (!res.ok) {
    throw new Error(`Failed to load video gallery: ${res.statusText}`);
  }
  const data = await res.json();
  return data.videos || (Array.isArray(data) ? data : []);
}

export async function fetchFieldingPresets() {
  const res = await fetch(`${API_BASE}/api/fielding/presets`);
  if (!res.ok) return null;
  return await res.json();
}

export async function validateFielding(fielders, formatRules = "T20") {
  const res = await fetch(`${API_BASE}/api/fielding/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fielders, format_rules: formatRules }),
  });
  if (!res.ok) return { valid: true, warnings: [] };
  return await res.json();
}

