export function formatTimestamp(isoStr) {
  if (!isoStr) return "Just now";
  try {
    const d = new Date(isoStr);
    if (isNaN(d.getTime())) return isoStr;
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    const hh = String(d.getHours()).padStart(2, "0");
    const min = String(d.getMinutes()).padStart(2, "0");
    const ss = String(d.getSeconds()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd} ${hh}:${min}:${ss}`;
  } catch (e) {
    return isoStr;
  }
}

export function getOutcomeClass(outcome = "") {
  const o = String(outcome).toUpperCase();
  if (o.includes("SIX")) return "outcome-six text-purple-200 border-purple-500 bg-purple-950/40";
  if (o.includes("FOUR")) return "outcome-four text-amber-200 border-amber-500 bg-amber-950/40";
  if (o.includes("SHORT")) return "outcome-short text-amber-300 border-amber-500 bg-amber-950/40";
  if (o.includes("BEYOND") || o.includes("OVERHEAD")) return "outcome-beyond text-sky-200 border-sky-500 bg-sky-950/40";
  if (o.includes("CATCH") || o.includes("CAUGHT") || o.includes("OUT") || o.includes("POTENTIAL_CATCH") || o.includes("WICKET")) {
    return "outcome-out text-rose-200 border-rose-500 bg-rose-950/40";
  }
  return "outcome-inplay text-emerald-200 border-emerald-500 bg-emerald-950/40";
}

export function getOutcomeBadgeColor(outcome = "") {
  const o = String(outcome).toUpperCase();
  if (o.includes("SIX")) return "bg-purple-900/40 text-purple-300 border-purple-600/50";
  if (o.includes("FOUR")) return "bg-amber-900/40 text-amber-300 border-amber-600/50";
  if (o.includes("SHORT")) return "bg-amber-900/40 text-amber-300 border-amber-600/50";
  if (o.includes("BEYOND") || o.includes("OVERHEAD")) return "bg-sky-900/40 text-sky-300 border-sky-600/50";
  if (o.includes("CATCH") || o.includes("CAUGHT") || o.includes("OUT") || o.includes("POTENTIAL_CATCH") || o.includes("WICKET")) {
    return "bg-rose-900/40 text-rose-300 border-rose-600/50";
  }
  return "bg-emerald-900/40 text-emerald-300 border-emerald-600/50";
}

export function isDeliveryRecord(exp = {}) {
  const id = exp.id || exp.experiment_id || "";
  return Boolean(exp.is_seeded_delivery || id.startsWith("DELIVERY_") || (exp.tags && exp.tags.includes("real_delivery")));
}
