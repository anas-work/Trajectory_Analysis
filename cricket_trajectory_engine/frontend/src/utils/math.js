export function anglesToCartesian(speed = 0, elevDeg = 0, azimDeg = 0) {
  const elevRad = (Number(elevDeg) * Math.PI) / 180;
  const azimRad = (Number(azimDeg) * Math.PI) / 180;
  const vxy = Number(speed) * Math.cos(elevRad);
  const vx = vxy * Math.cos(azimRad);
  const vy = vxy * Math.sin(azimRad);
  const vz = Number(speed) * Math.sin(elevRad);
  return { vx, vy, vz };
}

export function cartesianToAngles(vx = 0, vy = 0, vz = 0) {
  const vX = Number(vx) || 0;
  const vY = Number(vy) || 0;
  const vZ = Number(vz) || 0;
  const vxy = Math.hypot(vX, vY);
  const speed = Math.hypot(vxy, vZ);
  const elevDeg = (Math.atan2(vZ, vxy) * 180) / Math.PI;
  const azimDeg = (Math.atan2(vY, vX) * 180) / Math.PI;
  return { 
    speed, 
    elevDeg, 
    azimDeg,
    elevation: elevDeg,
    azimuth: azimDeg,
  };
}

export function calculateDerivedBallProperties(massKg = 0.156, diameterM = 0.072) {
  const radius = diameterM / 2.0;
  const area = Math.PI * radius * radius;
  const moi = (2.0 / 5.0) * massKg * radius * radius;
  return { 
    radius, 
    area, 
    moi,
    crossSectionArea: area,
    momentOfInertia: moi,
  };
}

export const Z_BAT_CREASE = 8.84; // Striker popping crease position in Three.js Z-axis

export function simToThreeCoords(xSim = 0, ySim = 0, zSim = 0, zBat = Z_BAT_CREASE) {
  return {
    x: -Number(ySim || 0),
    y: Math.max(0, Number(zSim || 0)),
    z: zBat - Number(xSim || 0),
  };
}

export function threeToSimCoords(px = 0, py = 0, pz = 0, zBat = Z_BAT_CREASE) {
  return {
    x: zBat - Number(pz || 0),
    y: -Number(px || 0),
    z: Math.max(0, Number(py || 0)),
  };
}

export function decomposeVelocity(speedMs = 0, elevDeg = 0, azimDeg = 0) {
  const elevRad = (Number(elevDeg) * Math.PI) / 180;
  const azimRad = (Number(azimDeg) * Math.PI) / 180;
  const spd = Number(speedMs) || 0;
  const vh = spd * Math.cos(elevRad);
  const vx = vh * Math.cos(azimRad);
  const vy = vh * Math.sin(azimRad);
  const vz = spd * Math.sin(elevRad);
  return {
    speedMs: spd,
    speedKmh: spd * 3.6,
    vh: Math.abs(vh),
    vhSigned: vh,
    vz: vz,
    vx: vx,
    vy: vy,
    elevDeg: Number(elevDeg),
    azimDeg: Number(azimDeg),
  };
}

export function normalizeTrajectory(rawPoints = []) {
  if (!rawPoints || rawPoints.length === 0) return [];
  return rawPoints.map(pt => {
    if (Array.isArray(pt)) {
      return pt;
    }
    const t = pt.time_s !== undefined ? pt.time_s : (pt.t !== undefined ? pt.t : 0);
    const x = pt.x !== undefined ? pt.x : 0;
    const y = pt.y !== undefined ? pt.y : 0;
    const z = pt.z !== undefined ? pt.z : 0;
    const vx = pt.vx !== undefined ? pt.vx : 0;
    const vy = pt.vy !== undefined ? pt.vy : 0;
    const vz = pt.vz !== undefined ? pt.vz : 0;
    const phase = pt.phase !== undefined ? pt.phase : (z > 0.05 ? 0 : 2);
    const row = [t, x, y, z, vx, vy, vz, phase];
    if (pt.event) {
      row.push(pt.event);
    }
    return row;
  });
}
