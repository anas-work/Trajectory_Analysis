import React, { useRef, useEffect } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { useApp } from '../../context/AppContext';
import { batsmanDataUri, bowlerDataUri, fielderDataUri } from './cricketerSprites';

// ─────────────────────────────────────────────────────────────────────────────
// Coordinate Mapping & Official Cricket Ground Constants (MCC Law 6 & 8)
// ─────────────────────────────────────────────────────────────────────────────
const Z_BAT = 8.84; // Striker's popping crease position along pitch axis

function simToThree(bx, by, bz) {
  return new THREE.Vector3(
    Number(by || 0),
    Math.max(0, Number(bz || 0)),
    Z_BAT - Number(bx || 0)
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// High-DPI Text Sprite Helper for Technical Telemetry Badges
// ─────────────────────────────────────────────────────────────────────────────
function createTelemetrySprite(lines = [], options = {}) {
  const {
    fontSize = 12,
    bgColor = 'rgba(8, 14, 26, 0.94)',
    borderColor = 'rgba(0, 229, 255, 0.85)',
    textColor = '#ffffff',
    highlightColor = '#00e5ff',
    height = 44,
    worldHeight = 0.95,
  } = options;

  const textLines = Array.isArray(lines) ? lines : [lines];

  // Dynamic width auto-measurement to prevent any text clipping or bleeding
  const calcCanvas = document.createElement('canvas');
  const calcCtx = calcCanvas.getContext('2d');
  let maxW = 0;
  textLines.forEach((line, idx) => {
    calcCtx.font = (textLines.length === 1 || idx === 0)
      ? `bold ${fontSize}px "JetBrains Mono", Inter, sans-serif`
      : `${fontSize - 1}px "JetBrains Mono", sans-serif`;
    const measured = calcCtx.measureText(line)?.width || 0;
    const approx = line.length * (fontSize * 0.78);
    const lineW = Math.max(measured, approx);
    if (lineW > maxW) maxW = lineW;
  });

  const width = Math.max(options.width || 0, Math.ceil(maxW + 36));

  const canvas = document.createElement('canvas');
  canvas.width = width * 2;
  canvas.height = height * 2;
  const ctx = canvas.getContext('2d');
  ctx.scale(2, 2);

  ctx.fillStyle = bgColor;
  ctx.strokeStyle = borderColor;
  ctx.lineWidth = 1.5;
  if (ctx.roundRect) {
    ctx.beginPath();
    ctx.roundRect(2, 2, width - 4, height - 4, 6);
    ctx.fill();
    ctx.stroke();
  } else {
    ctx.fillRect(2, 2, width - 4, height - 4);
    ctx.strokeRect(2, 2, width - 4, height - 4);
  }

  // Accent left indicator bar
  ctx.fillStyle = highlightColor;
  ctx.fillRect(3, 3, 3.5, height - 6);

  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';

  if (textLines.length === 1) {
    ctx.fillStyle = textColor;
    ctx.font = `bold ${fontSize}px "JetBrains Mono", Inter, sans-serif`;
    ctx.fillText(textLines[0], 14, height / 2);
  } else {
    const lineHeight = (height - 8) / textLines.length;
    textLines.forEach((line, idx) => {
      ctx.fillStyle = idx === 0 ? highlightColor : textColor;
      ctx.font = idx === 0 ? `bold ${fontSize}px Inter, sans-serif` : `${fontSize - 1}px "JetBrains Mono", sans-serif`;
      ctx.fillText(line, 14, 6 + idx * lineHeight + lineHeight / 2);
    });
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.minFilter = THREE.LinearFilter;
  const mat = new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: false });
  const sprite = new THREE.Sprite(mat);
  sprite.scale.set((width / height) * worldHeight, worldHeight, 1);
  return sprite;
}

// ─────────────────────────────────────────────────────────────────────────────
// Natural Striped Grass Outfield Texture (Matching Reference MCG Image)
// ─────────────────────────────────────────────────────────────────────────────
function createOutfieldGrassTexture() {
  const size = 1024;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');

  ctx.fillStyle = '#2d6a32';
  ctx.fillRect(0, 0, size, size);

  // Parallel Longitudinal Mowing Stripes running down pitch axis
  const numStripes = 24;
  const stripeW = size / numStripes;
  for (let i = 0; i < numStripes; i++) {
    if (i % 2 === 0) {
      ctx.fillStyle = 'rgba(64, 148, 72, 0.35)';
    } else {
      ctx.fillStyle = 'rgba(28, 78, 33, 0.38)';
    }
    ctx.fillRect(i * stripeW, 0, stripeW, size);
  }

  // Faint circular mower cut rings
  const cx = size / 2;
  const cy = size / 2;
  for (let r = 60; r < size * 0.48; r += 80) {
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.035)';
    ctx.lineWidth = 14;
    ctx.stroke();
  }

  // Natural grass blade grain
  const imgData = ctx.getImageData(0, 0, size, size);
  const data = imgData.data;
  for (let i = 0; i < data.length; i += 4) {
    const noise = (Math.random() - 0.5) * 10;
    data[i] = Math.min(255, Math.max(0, data[i] + noise));
    data[i + 1] = Math.min(255, Math.max(0, data[i + 1] + noise * 1.1));
    data[i + 2] = Math.min(255, Math.max(0, data[i + 2] + noise * 0.8));
  }
  ctx.putImageData(imgData, 0, 0);

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

// ─────────────────────────────────────────────────────────────────────────────
// Natural Soil Pitch Texture
// ─────────────────────────────────────────────────────────────────────────────
function createPitchTexture() {
  const w = 256;
  const h = 1024;
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d');

  ctx.fillStyle = '#c5aa7b';
  ctx.fillRect(0, 0, w, h);

  for (let x = 0; x < w; x += 6) {
    ctx.fillStyle = (x / 6) % 2 === 0 ? 'rgba(155, 130, 85, 0.18)' : 'rgba(225, 205, 168, 0.15)';
    ctx.fillRect(x, 0, 6, h);
  }

  const gradTop = ctx.createRadialGradient(w / 2, 70, 8, w / 2, 70, 75);
  gradTop.addColorStop(0, 'rgba(140, 110, 70, 0.40)');
  gradTop.addColorStop(1, 'rgba(140, 110, 70, 0)');
  ctx.fillStyle = gradTop;
  ctx.fillRect(0, 0, w, 150);

  const gradBottom = ctx.createRadialGradient(w / 2, h - 70, 8, w / 2, h - 70, 75);
  gradBottom.addColorStop(0, 'rgba(140, 110, 70, 0.40)');
  gradBottom.addColorStop(1, 'rgba(140, 110, 70, 0)');
  ctx.fillStyle = gradBottom;
  ctx.fillRect(0, h - 150, w, 150);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

// ─────────────────────────────────────────────────────────────────────────────
// Deep Australian Summer Sky Dome (MCG Daylight)
// ─────────────────────────────────────────────────────────────────────────────
function createDaylightSkyDome() {
  const skyGeo = new THREE.SphereGeometry(950, 32, 24);
  const canvas = document.createElement('canvas');
  canvas.width = 128;
  canvas.height = 512;
  const ctx = canvas.getContext('2d');
  const grad = ctx.createLinearGradient(0, 0, 0, 512);
  grad.addColorStop(0.0, '#0b62c4');
  grad.addColorStop(0.35, '#257ce3');
  grad.addColorStop(0.70, '#60a5fa');
  grad.addColorStop(0.92, '#bae6fd');
  grad.addColorStop(1.0, '#dbeafe');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 128, 512);

  const skyTex = new THREE.CanvasTexture(canvas);
  skyTex.colorSpace = THREE.SRGBColorSpace;
  const skyMat = new THREE.MeshBasicMaterial({
    map: skyTex,
    side: THREE.BackSide,
    depthWrite: false,
  });
  const sky = new THREE.Mesh(skyGeo, skyMat);
  sky.name = 'skyDome';
  sky.position.set(0, 0, Z_BAT);
  return sky;
}

// ─────────────────────────────────────────────────────────────────────────────
// Regulation Wickets & Bails
// ─────────────────────────────────────────────────────────────────────────────
function buildRegulationWickets(group, x, z) {
  const stumpMat = new THREE.MeshStandardMaterial({ color: 0xdfb76c, roughness: 0.35, metalness: 0.05 });
  const bailMat = new THREE.MeshStandardMaterial({ color: 0xf5d68a, roughness: 0.4 });
  const stumpHeight = 0.7112;
  const stumpRadius = 0.0175;
  const spacing = 0.1143;

  [-spacing, 0, spacing].forEach((off) => {
    const geo = new THREE.CylinderGeometry(stumpRadius, stumpRadius, stumpHeight, 16);
    const mesh = new THREE.Mesh(geo, stumpMat);
    mesh.position.set(x + off, stumpHeight / 2, z);
    mesh.castShadow = true;
    group.add(mesh);
  });

  [-spacing / 2, spacing / 2].forEach((bx) => {
    const bailGeo = new THREE.CylinderGeometry(0.008, 0.008, 0.11, 12);
    const bail = new THREE.Mesh(bailGeo, bailMat);
    bail.rotation.z = Math.PI / 2;
    bail.position.set(x + bx, stumpHeight + 0.008, z);
    bail.castShadow = true;
    group.add(bail);
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Photo-Realistic Batsman Camera-Facing Sprite (MS Dhoni Cutout)
// ─────────────────────────────────────────────────────────────────────────────
function buildPhotoBatsman(group, x, z, texture) {
  const batsmanGroup = new THREE.Group();
  batsmanGroup.name = 'batsmanMarker';
  batsmanGroup.position.set(x, 0, z);

  // Soft oval drop shadow on turf
  const shadowGeo = new THREE.PlaneGeometry(0.85, 0.45);
  const shadowMat = new THREE.MeshBasicMaterial({
    color: 0x000000,
    transparent: true,
    opacity: 0.45,
  });
  const shadow = new THREE.Mesh(shadowGeo, shadowMat);
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.set(0, 0.022, 0);
  batsmanGroup.add(shadow);

  // 3D Sprite with anchor at bottom center (Feet firmly on turf)
  const mat = new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    depthWrite: false,
  });
  const sprite = new THREE.Sprite(mat);
  sprite.center.set(0.5, 0.0);
  // Cropped Dhoni image aspect ratio: 288x487 -> width = 1.85 * (288 / 487) = 1.09m
  sprite.scale.set(1.10, 1.85, 1.0);
  sprite.position.set(0, 0.025, 0);
  batsmanGroup.add(sprite);

  // Sleek Batsman & Dhoni Badge floating comfortably above head (clear of face)
  const nameSprite = createTelemetrySprite('MS Dhoni (Batsman)', {
    fontSize: 10,
    bgColor: 'rgba(8, 14, 26, 0.92)',
    borderColor: 'rgba(234, 179, 8, 0.90)',
    highlightColor: '#eab308',
    textColor: '#f1f5f9',
    height: 22,
    worldHeight: 0.20,
  });
  nameSprite.position.set(0, 2.05, 0);
  batsmanGroup.add(nameSprite);

  group.add(batsmanGroup);
}

// ─────────────────────────────────────────────────────────────────────────────
// Photo-Realistic Bowler Camera-Facing Sprite (Jasprit Bumrah Delivery Leap)
// ─────────────────────────────────────────────────────────────────────────────
function buildPhotoBowler(group, x, z, texture) {
  const bowlerGroup = new THREE.Group();
  bowlerGroup.name = 'bowlerMarker';
  bowlerGroup.position.set(x, 0, z);

  const shadowGeo = new THREE.PlaneGeometry(0.70, 0.40);
  const shadowMat = new THREE.MeshBasicMaterial({
    color: 0x000000,
    transparent: true,
    opacity: 0.45,
  });
  const shadow = new THREE.Mesh(shadowGeo, shadowMat);
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.set(0, 0.022, 0);
  bowlerGroup.add(shadow);

  const mat = new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    depthWrite: false,
  });
  const sprite = new THREE.Sprite(mat);
  sprite.center.set(0.5, 0.0);
  sprite.scale.set(0.65, 2.25, 1.0);
  sprite.position.set(0, 0.025, 0);
  bowlerGroup.add(sprite);

  const nameSprite = createTelemetrySprite('Bowler (Bumrah)', {
    fontSize: 11,
    bgColor: 'rgba(8, 14, 26, 0.92)',
    borderColor: 'rgba(168, 85, 247, 0.90)',
    highlightColor: '#a855f7',
    textColor: '#f1f5f9',
    width: 100,
    height: 22,
    worldHeight: 0.32,
  });
  nameSprite.position.set(0, 2.45, 0);
  bowlerGroup.add(nameSprite);

  group.add(bowlerGroup);
}

// ─────────────────────────────────────────────────────────────────────────────
// Photo-Realistic Fielder Camera-Facing Sprite (Indian Blue Kit) + Minimalist Badge
// ─────────────────────────────────────────────────────────────────────────────
function buildPhotoFielder(f, posX, posZ, fielderTex, bowlerTex) {
  const fg = new THREE.Group();
  const isKeeper = f.role === 'wicketkeeper' || (f.name || '').toLowerCase().includes('keeper');
  const isBowler = f.role === 'bowler' || (f.name || '').toLowerCase().includes('bowler');

  // Catching reach radius ring on turf
  const reachR = f.catching_radius || f.reach_radius_m || 1.8;
  const reachGeo = new THREE.RingGeometry(reachR - 0.06, reachR, 48);
  const reachMat = new THREE.MeshBasicMaterial({
    color: isKeeper ? 0xf59e0b : (isBowler ? 0xa855f7 : 0x00e5ff),
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0.35,
  });
  const reachRing = new THREE.Mesh(reachGeo, reachMat);
  reachRing.rotation.x = -Math.PI / 2;
  reachRing.position.y = 0.022;
  fg.add(reachRing);

  // Soft oval drop shadow on turf
  const shadowGeo = new THREE.PlaneGeometry(0.65, 0.35);
  const shadowMat = new THREE.MeshBasicMaterial({
    color: 0x000000,
    transparent: true,
    opacity: 0.42,
  });
  const shadow = new THREE.Mesh(shadowGeo, shadowMat);
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.set(0, 0.025, 0);
  fg.add(shadow);

  // Select texture & dimensions: Bowler gets Bumrah, others get Blue Kit Fielder
  const texToUse = isBowler && bowlerTex ? bowlerTex : fielderTex;
  const mat = new THREE.SpriteMaterial({
    map: texToUse,
    transparent: true,
    depthWrite: false,
  });
  const sprite = new THREE.Sprite(mat);
  sprite.center.set(0.5, 0.0);
  if (isBowler) {
    sprite.scale.set(0.65, 2.25, 1.0);
  } else {
    sprite.scale.set(0.64, 1.85, 1.0);
  }
  sprite.position.set(0, 0.025, 0);
  fg.add(sprite);

  // Minimalist, Clean Fielder Name Pill (Proportional & Non-Intrusive)
  const badgeLabel = isBowler ? 'Bowler (Bumrah)' : (f.name || f.role || 'Fielder');
  const badgeBorder = isKeeper
    ? 'rgba(245, 158, 11, 0.85)'
    : (isBowler ? 'rgba(168, 85, 247, 0.85)' : 'rgba(0, 229, 255, 0.75)');
  const badgeHighlight = isKeeper ? '#f59e0b' : (isBowler ? '#a855f7' : '#00e5ff');

  const nameSprite = createTelemetrySprite(badgeLabel, {
    fontSize: 11,
    bgColor: 'rgba(8, 14, 26, 0.92)',
    borderColor: badgeBorder,
    highlightColor: badgeHighlight,
    textColor: '#f1f5f9',
    width: Math.max(76, badgeLabel.length * 8.2),
    height: 22,
    worldHeight: 0.30,
  });
  nameSprite.position.set(0, isBowler ? 2.45 : (isKeeper ? 2.05 : 2.05), 0);
  fg.add(nameSprite);

  fg.position.set(posX, 0, posZ);
  return fg;
}

// ─────────────────────────────────────────────────────────────────────────────
// MCG-Style Cricket Stadium Architecture (Matching Reference Image 2)
// ─────────────────────────────────────────────────────────────────────────────
function buildModernStadium(group) {
  const centerZ = Z_BAT;

  // 1. Manicured Outer Run-off Apron (Radius 160m)
  const apronGeo = new THREE.CircleGeometry(160, 96);
  const apronMat = new THREE.MeshStandardMaterial({
    color: 0x1e4a23,
    roughness: 0.92,
    metalness: 0.02,
  });
  const apron = new THREE.Mesh(apronGeo, apronMat);
  apron.rotation.x = -Math.PI / 2;
  apron.position.set(0, -0.06, centerZ);
  apron.receiveShadow = true;
  group.add(apron);

  // 2. High-Precision Outfield Turf (Radius 85m) with Mowing Stripes Texture
  const grassTex = createOutfieldGrassTexture();
  const grassGeo = new THREE.CircleGeometry(85, 96);
  const grassMat = new THREE.MeshStandardMaterial({
    map: grassTex,
    color: 0xffffff,
    roughness: 0.72,
    metalness: 0.04,
  });
  const grass = new THREE.Mesh(grassGeo, grassMat);
  grass.rotation.x = -Math.PI / 2;
  grass.position.set(0, 0, centerZ);
  grass.receiveShadow = true;
  group.add(grass);

  // 3. Outfield Distance Range Rings (20m, 40m, 60m, 70m, 80m)
  const rangeDistances = [20, 40, 60, 70, 80];
  rangeDistances.forEach((dist) => {
    const ringGeo = new THREE.RingGeometry(dist - 0.05, dist + 0.05, 96);
    const isBoundary = dist === 70;
    const ringMat = new THREE.MeshBasicMaterial({
      color: isBoundary ? 0xf59e0b : 0xffffff,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: isBoundary ? 0.75 : 0.20,
    });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = -Math.PI / 2;
    ring.position.set(0, 0.012, centerZ);
    group.add(ring);

    const label = createTelemetrySprite(`${dist}m`, {
      fontSize: 10,
      bgColor: 'rgba(15, 23, 42, 0.85)',
      borderColor: isBoundary ? 'rgba(245, 158, 11, 0.7)' : 'rgba(255, 255, 255, 0.35)',
      textColor: isBoundary ? '#f59e0b' : '#f1f5f9',
      width: 54,
      height: 22,
    });
    const ang = Math.PI / 4;
    label.position.set(Math.sin(ang) * dist, 0.32, centerZ - Math.cos(ang) * dist);
    group.add(label);
  });

  // 4. Central Cricket Pitch
  const pitchTex = createPitchTexture();
  const pitchGeo = new THREE.PlaneGeometry(3.05, 22.56);
  const pitchMat = new THREE.MeshStandardMaterial({
    map: pitchTex,
    roughness: 0.75,
    metalness: 0.02,
  });
  const pitch = new THREE.Mesh(pitchGeo, pitchMat);
  pitch.rotation.x = -Math.PI / 2;
  pitch.position.set(0, 0.02, centerZ - 10.06);
  pitch.receiveShadow = true;
  group.add(pitch);

  // Pitch Creases
  const creaseMat = new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide });

  // Striker Popping Crease
  const strikerPopping = new THREE.Mesh(new THREE.PlaneGeometry(3.66, 0.07), creaseMat);
  strikerPopping.rotation.x = -Math.PI / 2;
  strikerPopping.position.set(0, 0.035, centerZ);
  group.add(strikerPopping);

  // Striker Bowling Crease
  const strikerBowling = new THREE.Mesh(new THREE.PlaneGeometry(2.64, 0.06), creaseMat);
  strikerBowling.rotation.x = -Math.PI / 2;
  strikerBowling.position.set(0, 0.035, centerZ + 1.22);
  group.add(strikerBowling);

  // Bowler Popping Crease
  const bowlerPopping = new THREE.Mesh(new THREE.PlaneGeometry(3.66, 0.07), creaseMat);
  bowlerPopping.rotation.x = -Math.PI / 2;
  bowlerPopping.position.set(0, 0.035, centerZ - 17.68);
  group.add(bowlerPopping);

  // Bowler Bowling Crease
  const bowlerBowling = new THREE.Mesh(new THREE.PlaneGeometry(2.64, 0.06), creaseMat);
  bowlerBowling.rotation.x = -Math.PI / 2;
  bowlerBowling.position.set(0, 0.035, centerZ - 20.12);
  group.add(bowlerBowling);

  // Regulation Wickets
  buildRegulationWickets(group, 0, centerZ + 1.22);
  buildRegulationWickets(group, 0, centerZ - 20.12);

  // 5. 30-Yard Infield Circle
  const circle30R = 27.43;
  const c30Geo = new THREE.RingGeometry(circle30R - 0.07, circle30R + 0.07, 80);
  const c30Mat = new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide, transparent: true, opacity: 0.45 });
  const c30Mesh = new THREE.Mesh(c30Geo, c30Mat);
  c30Mesh.rotation.x = -Math.PI / 2;
  c30Mesh.position.set(0, 0.025, centerZ - 8.84);
  group.add(c30Mesh);

  // 6. Official Boundary Rope (Radius 70m)
  const bndR = 70.0;
  const ropePoints = [];
  for (let i = 0; i <= 128; i++) {
    const a = (i / 128) * Math.PI * 2;
    ropePoints.push(new THREE.Vector3(Math.cos(a) * bndR, 0.10, centerZ + Math.sin(a) * bndR));
  }
  const ropeCurve = new THREE.CatmullRomCurve3(ropePoints, true);
  const ropeGeo = new THREE.TubeGeometry(ropeCurve, 128, 0.13, 8, true);
  const ropeMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.35 });
  const rope = new THREE.Mesh(ropeGeo, ropeMat);
  rope.receiveShadow = true;
  group.add(rope);

  // Boundary Foam Sponsor Wedges
  const wedgeGeo = new THREE.BoxGeometry(0.38, 0.28, 1.3);
  const wedgeMat = new THREE.MeshStandardMaterial({ color: 0x0f766e, roughness: 0.4 });
  for (let a = 0; a < Math.PI * 2; a += Math.PI / 16) {
    const wedge = new THREE.Mesh(wedgeGeo, wedgeMat);
    wedge.position.set(Math.cos(a) * (bndR + 0.32), 0.14, centerZ + Math.sin(a) * (bndR + 0.32));
    wedge.rotation.y = -a;
    group.add(wedge);
  }

  // 7. Perimeter Advertising Wall (Radius 85m to 85.5m, Height 1.4m)
  const ledGeo = new THREE.CylinderGeometry(85.5, 85, 1.4, 80, 1, true);
  const ledMat = new THREE.MeshStandardMaterial({
    color: 0x0369a1,
    roughness: 0.5,
    emissive: 0x0284c7,
    emissiveIntensity: 0.25,
    side: THREE.BackSide,
  });
  const ledRibbon = new THREE.Mesh(ledGeo, ledMat);
  ledRibbon.position.set(0, 0.7, centerZ);
  group.add(ledRibbon);

  // 8. MCG Grandstand Stadium Architecture (Image 2)
  const mcgNavySeatMat = new THREE.MeshStandardMaterial({
    color: 0x1b3a57,
    roughness: 0.55,
    metalness: 0.1,
  });
  const mcgSlateSeatMat = new THREE.MeshStandardMaterial({
    color: 0x142d45,
    roughness: 0.58,
    metalness: 0.1,
  });
  const fasciaWhiteMat = new THREE.MeshStandardMaterial({
    color: 0xffffff,
    roughness: 0.3,
    metalness: 0.2,
  });
  const concreteMat = new THREE.MeshStandardMaterial({
    color: 0x64748b,
    roughness: 0.8,
  });
  const roofCanopyMat = new THREE.MeshStandardMaterial({
    color: 0xf8fafc,
    roughness: 0.35,
    side: THREE.DoubleSide,
  });
  const steelTrussMat = new THREE.MeshStandardMaterial({
    color: 0xe2e8f0,
    roughness: 0.3,
    metalness: 0.5,
  });

  // --- Tier 1 (Lower Seating Bowl): Radius 87m -> 104m, Height 1.0m -> 7.8m ---
  const numStepsT1 = 8;
  const rT1Start = 87;
  const rT1End = 104;
  const hT1Start = 1.0;
  const hT1End = 7.8;
  for (let s = 0; s < numStepsT1; s++) {
    const t = s / numStepsT1;
    const rInner = rT1Start + t * (rT1End - rT1Start);
    const rOuter = rInner + (rT1End - rT1Start) / numStepsT1;
    const yStep = hT1Start + t * (hT1End - hT1Start);

    const tierGeo = new THREE.CylinderGeometry(rInner, rOuter, 0.85, 80, 1, true);
    const tierMesh = new THREE.Mesh(tierGeo, s % 2 === 0 ? mcgNavySeatMat : mcgSlateSeatMat);
    tierMesh.position.set(0, yStep, centerZ);
    group.add(tierMesh);
  }

  const fasciaT1Geo = new THREE.CylinderGeometry(87.1, 87.1, 0.5, 80, 1, true);
  const fasciaT1 = new THREE.Mesh(fasciaT1Geo, fasciaWhiteMat);
  fasciaT1.position.set(0, 1.25, centerZ);
  group.add(fasciaT1);

  // --- Concourse Walkway (Radius 104m -> 108m, Height 8.2m) ---
  const concourseGeo = new THREE.RingGeometry(104, 108, 80);
  const concourse = new THREE.Mesh(concourseGeo, concreteMat);
  concourse.rotation.x = -Math.PI / 2;
  concourse.position.set(0, 8.2, centerZ);
  group.add(concourse);

  // --- Tier 2 (Upper Seating Bowl): Radius 108m -> 128m, Height 9.5m -> 21.5m ---
  const numStepsT2 = 10;
  const rT2Start = 108;
  const rT2End = 128;
  const hT2Start = 9.5;
  const hT2End = 21.5;
  for (let s = 0; s < numStepsT2; s++) {
    const t = s / numStepsT2;
    const rInner = rT2Start + t * (rT2End - rT2Start);
    const rOuter = rInner + (rT2End - rT2Start) / numStepsT2;
    const yStep = hT2Start + t * (hT2End - hT2Start);

    const tierGeo = new THREE.CylinderGeometry(rInner, rOuter, 1.2, 80, 1, true);
    const tierMesh = new THREE.Mesh(tierGeo, s % 2 === 0 ? mcgNavySeatMat : mcgSlateSeatMat);
    tierMesh.position.set(0, yStep, centerZ);
    group.add(tierMesh);
  }

  const fasciaT2Geo = new THREE.CylinderGeometry(108.1, 108.1, 0.6, 80, 1, true);
  const fasciaT2 = new THREE.Mesh(fasciaT2Geo, fasciaWhiteMat);
  fasciaT2.position.set(0, 9.8, centerZ);
  group.add(fasciaT2);

  // --- Stadium Outer Wall & Structural Columns ---
  const wallGeo = new THREE.CylinderGeometry(131, 131, 24, 80, 1, true);
  const wallMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.8 });
  const wall = new THREE.Mesh(wallGeo, wallMat);
  wall.position.set(0, 12, centerZ);
  group.add(wall);

  // --- Cantilevered Wave Roof Canopy ---
  const roofGeo = new THREE.RingGeometry(96, 136, 80);
  const roof = new THREE.Mesh(roofGeo, roofCanopyMat);
  roof.rotation.x = -Math.PI / 2;
  roof.position.set(0, 26, centerZ);
  group.add(roof);

  for (let a = 0; a < Math.PI * 2; a += Math.PI / 12) {
    const trussPts = [
      new THREE.Vector3(Math.cos(a) * 131, 23, centerZ + Math.sin(a) * 131),
      new THREE.Vector3(Math.cos(a) * 98, 26.5, centerZ + Math.sin(a) * 98),
    ];
    const trussGeo = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(trussPts), 8, 0.40, 6, false);
    const truss = new THREE.Mesh(trussGeo, steelTrussMat);
    group.add(truss);
  }

  // --- Floodlight Pylon Mast ---
  const floodlightAngles = [Math.PI / 4, (3 * Math.PI) / 4, (5 * Math.PI) / 4, (7 * Math.PI) / 4];
  floodlightAngles.forEach((ang) => {
    const fx = Math.cos(ang) * 142;
    const fz = centerZ + Math.sin(ang) * 142;

    const mastGeo = new THREE.CylinderGeometry(1.2, 3.6, 54, 8);
    const mast = new THREE.Mesh(mastGeo, steelTrussMat);
    mast.position.set(fx, 27, fz);
    group.add(mast);

    const headGeo = new THREE.BoxGeometry(10, 6, 1.2);
    const headMat = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      emissive: 0xfffaed,
      emissiveIntensity: 0.75,
      roughness: 0.2,
    });
    const head = new THREE.Mesh(headGeo, headMat);
    head.position.set(fx, 54, fz);
    head.lookAt(0, 10, centerZ);
    group.add(head);

    const light = new THREE.PointLight(0xfffaed, 0.8, 260);
    light.position.set(fx * 0.92, 52, centerZ + (fz - centerZ) * 0.92);
    group.add(light);
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Precision Elevation Angle Arc & Velocity Kinematics Vector Construct
// ─────────────────────────────────────────────────────────────────────────────
function buildElevationKinematicsConstruct(config, metrics, pt0) {
  const group = new THREE.Group();
  group.name = 'elevationKinematicsConstruct';

  const vx0 = pt0 ? (pt0[4] || 0) : 25;
  const vy0 = pt0 ? (pt0[5] || 0) : 0;
  const vz0 = pt0 ? (pt0[6] || 0) : 15;
  const p0 = pt0 ? simToThree(pt0[1] || 0, pt0[2] || 0, pt0[3] || 0.9) : new THREE.Vector3(0, 0.9, Z_BAT);

  const speedMs = Math.hypot(vx0, vy0, vz0) || 28;
  const speedKmh = speedMs * 3.6;
  const vxy = Math.hypot(vx0, vy0) || 1e-6;
  const elevRad = Math.atan2(vz0, vxy);
  const elevDeg = (elevRad * 180) / Math.PI;
  const vhKmh = vxy * 3.6;
  const vzKmh = vz0 * 3.6;

  const uH = new THREE.Vector3(-vy0 / vxy, 0, -vx0 / vxy).normalize();
  const uUp = new THREE.Vector3(0, 1, 0);
  const uV = new THREE.Vector3(-vy0 / speedMs, vz0 / speedMs, -vx0 / speedMs).normalize();

  const arrowLen = Math.min(Math.max(speedMs * 0.25, 4.5), 10.0);
  const arcR = Math.min(Math.max(arrowLen * 0.65, 3.0), 6.5);

  const baseEnd = p0.clone().addScaledVector(uH, arrowLen * 1.05);
  const baseGeo = new THREE.BufferGeometry().setFromPoints([p0, baseEnd]);
  const baseMat = new THREE.LineDashedMaterial({
    color: 0xffffff,
    dashSize: 0.35,
    gapSize: 0.22,
    transparent: true,
    opacity: 0.75,
  });
  const baseLine = new THREE.Line(baseGeo, baseMat);
  baseLine.computeLineDistances();
  group.add(baseLine);

  const vhLen = arrowLen * Math.cos(elevRad);
  if (vhLen > 0.1) {
    const vhArrow = new THREE.ArrowHelper(uH, p0, vhLen, 0x10b981, 0.4, 0.22);
    group.add(vhArrow);
  }

  const vhTip = p0.clone().addScaledVector(uH, vhLen);
  const vzLen = Math.abs(arrowLen * Math.sin(elevRad));
  const vzDir = vz0 >= 0 ? uUp : uUp.clone().negate();
  if (vzLen > 0.08) {
    const vzArrow = new THREE.ArrowHelper(vzDir, vhTip, vzLen, vz0 >= 0 ? 0xf59e0b : 0xef4444, 0.4, 0.2);
    group.add(vzArrow);
  }

  const resArrow = new THREE.ArrowHelper(uV, p0, arrowLen, 0x00e5ff, 0.7, 0.35);
  group.add(resArrow);

  const arcSteps = 32;
  const arcPoints = [];
  const fanVertices = [p0.x, p0.y, p0.z];

  for (let i = 0; i <= arcSteps; i++) {
    const alpha = (i / arcSteps) * elevRad;
    const pt = p0.clone()
      .addScaledVector(uH, Math.cos(alpha) * arcR)
      .addScaledVector(uUp, Math.sin(alpha) * arcR);
    arcPoints.push(pt);
    fanVertices.push(pt.x, pt.y, pt.z);
  }

  const arcGeo = new THREE.BufferGeometry().setFromPoints(arcPoints);
  const arcMat = new THREE.LineBasicMaterial({ color: 0x00e5ff, linewidth: 3 });
  group.add(new THREE.Line(arcGeo, arcMat));

  const fanIndices = [];
  for (let i = 1; i <= arcSteps; i++) {
    fanIndices.push(0, i, i + 1);
  }
  const fanGeo = new THREE.BufferGeometry();
  fanGeo.setAttribute('position', new THREE.Float32BufferAttribute(fanVertices, 3));
  fanGeo.setIndex(fanIndices);
  fanGeo.computeVertexNormals();

  const fanMat = new THREE.MeshBasicMaterial({
    color: elevDeg >= 0 ? 0x00e5ff : 0xf59e0b,
    transparent: true,
    opacity: 0.22,
    side: THREE.DoubleSide,
  });
  group.add(new THREE.Mesh(fanGeo, fanMat));

  const midAlpha = elevRad * 0.5;
  const badgePos = p0.clone()
    .addScaledVector(uH, Math.cos(midAlpha) * (arcR + 0.85))
    .addScaledVector(uUp, Math.sin(midAlpha) * (arcR + 0.85) + 0.2);

  const elevSign = elevDeg >= 0 ? '+' : '';
  const badgeSprite = createTelemetrySprite([
    `θ = ${elevSign}${elevDeg.toFixed(1)}°  |  V₀ = ${speedKmh.toFixed(1)} km/h`,
    `Vh = ${vhKmh.toFixed(1)} km/h  |  Vz = ${vzKmh.toFixed(1)} km/h`,
  ], {
    fontSize: 12,
    bgColor: 'rgba(8, 14, 26, 0.94)',
    borderColor: 'rgba(0, 229, 255, 0.9)',
    textColor: '#e2e8f0',
    highlightColor: '#00e5ff',
    width: 240,
    height: 48,
  });
  badgeSprite.position.copy(badgePos);
  group.add(badgeSprite);

  return group;
}

// ─────────────────────────────────────────────────────────────────────────────
// Ground Projection Shadow Ribbon & Vertical Plumb-Lines
// ─────────────────────────────────────────────────────────────────────────────
function buildTrajectoryGroundShadow(points = [], apexPoint = null) {
  const group = new THREE.Group();
  group.name = 'trajectoryGroundShadow';

  if (!points || points.length < 2) return group;

  const shadowPoints = points.map((p) => new THREE.Vector3(p.x, 0.02, p.z));
  const shadowCurve = new THREE.CatmullRomCurve3(shadowPoints);
  const shadowGeo = new THREE.BufferGeometry().setFromPoints(shadowCurve.getPoints(Math.min(points.length * 3, 200)));
  const shadowMat = new THREE.LineBasicMaterial({
    color: 0x14401c,
    linewidth: 4,
    transparent: true,
    opacity: 0.70,
  });
  group.add(new THREE.Line(shadowGeo, shadowMat));

  if (apexPoint) {
    const plumbPts = [apexPoint, new THREE.Vector3(apexPoint.x, 0.03, apexPoint.z)];
    const plumbGeo = new THREE.BufferGeometry().setFromPoints(plumbPts);
    const plumbMat = new THREE.LineDashedMaterial({
      color: 0xf59e0b,
      dashSize: 0.45,
      gapSize: 0.35,
      transparent: true,
      opacity: 0.85,
    });
    const plumbLine = new THREE.Line(plumbGeo, plumbMat);
    plumbLine.computeLineDistances();
    group.add(plumbLine);
  }

  return group;
}

// ─────────────────────────────────────────────────────────────────────────────
// Main StadiumCanvas Component
// ─────────────────────────────────────────────────────────────────────────────
export default function StadiumCanvas() {
  const canvasRef = useRef(null);
  const threeRef = useRef(null);
  const { trajectory, metrics, fielders, playback, cameraView } = useApp();

  // ── Initial WebGL Setup ────────────────────────────────────────────────────
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const width = canvas.parentElement?.clientWidth || 900;
    const height = canvas.parentElement?.clientHeight || 540;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x87ceeb);
    scene.fog = new THREE.Fog(0xb8e2f8, 280, 950);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 2000);
    camera.position.set(-42, 34, 52);

    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 0.92;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    // ── Controls Setup ────────────────────────────────────────────────────────
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.screenSpacePanning = false;
    controls.mouseButtons = {
      LEFT: THREE.MOUSE.ROTATE,
      MIDDLE: THREE.MOUSE.DOLLY,
      RIGHT: THREE.MOUSE.PAN,
    };
    controls.touches = {
      ONE: THREE.TOUCH.ROTATE,
      TWO: THREE.TOUCH.DOLLY_PAN,
    };
    controls.maxPolarAngle = Math.PI / 2 - 0.02;
    controls.minPolarAngle = 0.05;
    controls.minDistance = 3.0;
    controls.maxDistance = 240.0;
    controls.target.set(0, 2, -6);

    // ── Lighting ─────────────────────────────────────────────────────────────
    const ambient = new THREE.AmbientLight(0xffffff, 0.20);
    scene.add(ambient);

    const hemi = new THREE.HemisphereLight(0x7dd3fc, 0x27672b, 0.55);
    scene.add(hemi);

    const sun = new THREE.DirectionalLight(0xfffcf0, 1.25);
    sun.position.set(70, 120, 50);
    sun.castShadow = true;
    sun.shadow.mapSize.width = 2048;
    sun.shadow.mapSize.height = 2048;
    sun.shadow.camera.near = 10;
    sun.shadow.camera.far = 420;
    sun.shadow.camera.left = -110;
    sun.shadow.camera.right = 110;
    sun.shadow.camera.top = 110;
    sun.shadow.camera.bottom = -110;
    sun.shadow.bias = -0.00015;
    scene.add(sun);

    const fillLight = new THREE.DirectionalLight(0xcfd8dc, 0.30);
    fillLight.position.set(-70, 60, -60);
    scene.add(fillLight);

    // ── Sky Dome & Stadium Architecture ───────────────────────────────────────
    const skyDome = createDaylightSkyDome();
    scene.add(skyDome);

    const stadiumGroup = new THREE.Group();
    scene.add(stadiumGroup);
    buildModernStadium(stadiumGroup);

    // ── Synchronous Base64 Cricketer Textures ─────────────────────────────────
    const texLoader = new THREE.TextureLoader();
    const batsmanTex = texLoader.load(batsmanDataUri);
    batsmanTex.colorSpace = THREE.SRGBColorSpace;

    const bowlerTex = texLoader.load(bowlerDataUri);
    bowlerTex.colorSpace = THREE.SRGBColorSpace;

    const fielderTex = texLoader.load(fielderDataUri);
    fielderTex.colorSpace = THREE.SRGBColorSpace;

    // Build Striker Billboard directly into the scene
    buildPhotoBatsman(stadiumGroup, 0.15, Z_BAT, batsmanTex);

    // ── Cricket Ball Mesh ────────────────────────────────────────────────────
    const ballGeo = new THREE.SphereGeometry(0.18, 32, 32);
    const ballMat = new THREE.MeshStandardMaterial({
      color: 0xc8102e,
      roughness: 0.25,
      metalness: 0.08,
      emissive: 0x1a0004,
      emissiveIntensity: 0.2,
    });
    const ballMesh = new THREE.Mesh(ballGeo, ballMat);
    ballMesh.castShadow = true;
    ballMesh.visible = false;
    scene.add(ballMesh);

    const seamGeo = new THREE.TorusGeometry(0.181, 0.01, 8, 48);
    const seamMat = new THREE.MeshStandardMaterial({ color: 0xf5deb3, roughness: 0.4 });
    const seamMesh = new THREE.Mesh(seamGeo, seamMat);
    ballMesh.add(seamMesh);

    // ── Cursor-Anchored Wheel Zoom Handler ───────────────────────────────────
    const raycaster = new THREE.Raycaster();
    const mouseVec = new THREE.Vector2();
    const groundPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
    const groundHit = new THREE.Vector3();

    const onWheel = (e) => {
      e.preventDefault();
      const rect = canvas.getBoundingClientRect();
      mouseVec.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouseVec.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouseVec, camera);
      const hasHit = raycaster.ray.intersectPlane(groundPlane, groundHit);

      const currentDist = camera.position.distanceTo(controls.target);
      const zoomDelta = e.deltaY;
      const zoomFactor = Math.min(Math.max(Math.abs(zoomDelta) * 0.0018, 0.06), 0.22);

      if (zoomDelta < 0) {
        if (currentDist > controls.minDistance) {
          if (hasHit && groundHit.length() < 135) {
            controls.target.lerp(groundHit, zoomFactor * 0.40);
          }
          const dir = new THREE.Vector3().subVectors(controls.target, camera.position).normalize();
          const moveDist = Math.min(currentDist * zoomFactor, currentDist - controls.minDistance);
          camera.position.addScaledVector(dir, moveDist);
        }
      } else {
        if (currentDist < controls.maxDistance) {
          const centerGround = new THREE.Vector3(0, 1.5, Z_BAT - 5);
          controls.target.lerp(centerGround, zoomFactor * 0.20);
          const dir = new THREE.Vector3().subVectors(camera.position, controls.target).normalize();
          const moveDist = Math.min(currentDist * zoomFactor, controls.maxDistance - currentDist);
          camera.position.addScaledVector(dir, moveDist);
        }
      }

      if (camera.position.y < 0.6) {
        camera.position.y = 0.6;
      }
      controls.update();
    };

    canvas.addEventListener('wheel', onWheel, { passive: false });

    // ── Stash Three Context ──────────────────────────────────────────────────
    threeRef.current = {
      scene,
      camera,
      renderer,
      controls,
      stadiumGroup,
      ballMesh,
      fielderTex,
      bowlerTex,
      batsmanTex,
      flightTube: null,
      rollTube: null,
      continuationTube: null,
      groundShadowGroup: null,
      elevationGroup: null,
      milestonesGroup: null,
      fielderMeshes: [],
    };

    let animId;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      controls.update();
      if (ballMesh.visible) {
        ballMesh.rotation.x += 0.035;
        ballMesh.rotation.z += 0.015;
      }
      renderer.render(scene, camera);
    };
    animate();

    const onResize = () => {
      if (!canvas || !renderer || !camera) return;
      const w = canvas.parentElement?.clientWidth || 900;
      const h = canvas.parentElement?.clientHeight || 540;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', onResize);

    return () => {
      cancelAnimationFrame(animId);
      canvas.removeEventListener('wheel', onWheel);
      window.removeEventListener('resize', onResize);
      renderer.dispose();
      threeRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Dynamic Zoom Limits Based on Simulation Extent ─────────────────────────
  useEffect(() => {
    if (!threeRef.current?.controls) return;
    const carry = Number(metrics?.carry_distance_m || metrics?.total_distance_m || 70);
    const sceneBound = Math.max(145, carry * 1.35);
    const dynamicMax = Math.min(320, Math.max(190, sceneBound * 1.65));
    threeRef.current.controls.maxDistance = dynamicMax;
  }, [metrics]);

  // ── Fielder Update with Uploaded Cricketer Sprites ─────────────────────────
  useEffect(() => {
    if (!threeRef.current) return;
    const { scene, fielderMeshes, fielderTex, bowlerTex } = threeRef.current;

    fielderMeshes.forEach((m) => {
      m.traverse((child) => {
        if (child.geometry) child.geometry.dispose();
      });
      scene.remove(m);
    });
    threeRef.current.fielderMeshes = [];

    (fielders || []).forEach((f) => {
      const posX = Number(f.y || 0);
      const posZ = Z_BAT - f.x;
      const mesh = buildPhotoFielder(f, posX, posZ, fielderTex, bowlerTex);
      scene.add(mesh);
      threeRef.current.fielderMeshes.push(mesh);
    });
  }, [fielders]);

  // ── Trajectory, Elevation Angle & Milestones Update ──────────────────────────
  useEffect(() => {
    if (!threeRef.current) return;
    const { scene, ballMesh } = threeRef.current;

    const disposeObj = (key) => {
      const obj = threeRef.current[key];
      if (obj) {
        obj.traverse((child) => {
          if (child.geometry) child.geometry.dispose();
          if (child.material) {
            if (Array.isArray(child.material)) child.material.forEach((m) => m.dispose());
            else child.material.dispose();
          }
        });
        scene.remove(obj);
        threeRef.current[key] = null;
      }
    };

    disposeObj('flightTube');
    disposeObj('rollTube');
    disposeObj('continuationTube');
    disposeObj('groundShadowGroup');
    disposeObj('elevationGroup');
    disposeObj('milestonesGroup');

    if (!trajectory || trajectory.length < 2) {
      ballMesh.visible = false;
      return;
    }

    const pt0 = trajectory[0];
    const elevGroup = buildElevationKinematicsConstruct(null, metrics, pt0);
    scene.add(elevGroup);
    threeRef.current.elevationGroup = elevGroup;

    const interception = metrics?.fielder_interception;
    const isCaught = Boolean(interception && interception.can_intercept);
    const catchTime = interception ? Number(interception.intercept_time_s || interception.time_s || 0) : 0;
    
    let catchVec = null;
    if (isCaught) {
      if (interception.intercept_position_m && interception.intercept_position_m.length === 3) {
        catchVec = simToThree(
          interception.intercept_position_m[0],
          interception.intercept_position_m[1],
          interception.intercept_position_m[2]
        );
      } else {
        for (let i = 0; i < trajectory.length; i++) {
          if (trajectory[i][0] >= catchTime) {
            catchVec = simToThree(trajectory[i][1], trajectory[i][2], trajectory[i][3]);
            break;
          }
        }
      }
    }

    let firstImpactVec = null;
    if (metrics?.first_landing_pos_m && metrics.first_landing_pos_m.length >= 2) {
      firstImpactVec = simToThree(metrics.first_landing_pos_m[0], metrics.first_landing_pos_m[1], 0.0);
    }

    const flightPoints = [];
    const continuationPoints = [];
    const rollPoints = [];
    const allPreCatchPoints = [];

    const launchPos = simToThree(pt0[1], pt0[2], pt0[3]);

    trajectory.forEach((row) => {
      const t = row[0];
      const p = simToThree(row[1], row[2], row[3]);
      const phase = row[7] || 0;

      if (isCaught && t > catchTime + 1e-4) {
        continuationPoints.push(p);
      } else {
        allPreCatchPoints.push(p);
        if (phase === 0) {
          flightPoints.push(p);
        } else {
          rollPoints.push(p);
        }
      }
    });

    if (isCaught && catchVec) {
      flightPoints.push(catchVec);
      continuationPoints.unshift(catchVec);
    }

    let apexPoint = null;
    let apexHeight = 0;
    let apexTime = 0;
    trajectory.forEach((r) => {
      if (r[3] > apexHeight) {
        apexHeight = r[3];
        apexTime = r[0];
        apexPoint = simToThree(r[1], r[2], r[3]);
      }
    });

    const groundShadow = buildTrajectoryGroundShadow(allPreCatchPoints, apexPoint);
    scene.add(groundShadow);
    threeRef.current.groundShadowGroup = groundShadow;

    if (flightPoints.length >= 2) {
      const flightCurve = new THREE.CatmullRomCurve3(flightPoints);
      const tubeSegments = Math.min(flightPoints.length * 4, 300);
      const tubeGeo = new THREE.TubeGeometry(flightCurve, tubeSegments, 0.14, 10, false);
      const tubeMat = new THREE.MeshStandardMaterial({
        color: 0x00e5ff,
        emissive: 0x0088aa,
        emissiveIntensity: 0.55,
        roughness: 0.25,
        metalness: 0.1,
      });
      const flightTube = new THREE.Mesh(tubeGeo, tubeMat);
      flightTube.castShadow = true;
      scene.add(flightTube);
      threeRef.current.flightTube = flightTube;
    }

    if (!isCaught && rollPoints.length >= 2) {
      const rollCurve = new THREE.CatmullRomCurve3(rollPoints);
      const tubeSegments = Math.min(rollPoints.length * 3, 160);
      const tubeGeo = new THREE.TubeGeometry(rollCurve, tubeSegments, 0.10, 8, false);
      const tubeMat = new THREE.MeshStandardMaterial({
        color: 0x10b981,
        emissive: 0x047857,
        emissiveIntensity: 0.45,
        roughness: 0.35,
      });
      const rollTube = new THREE.Mesh(tubeGeo, tubeMat);
      scene.add(rollTube);
      threeRef.current.rollTube = rollTube;
    }

    if (isCaught && continuationPoints.length >= 2) {
      const contCurve = new THREE.CatmullRomCurve3(continuationPoints);
      const contPoints = contCurve.getPoints(Math.min(continuationPoints.length * 2, 80));
      const contGeo = new THREE.BufferGeometry().setFromPoints(contPoints);
      const contMat = new THREE.LineDashedMaterial({
        color: 0x38bdf8,
        dashSize: 0.6,
        gapSize: 0.4,
        transparent: true,
        opacity: 0.45,
      });
      const continuationLine = new THREE.Line(contGeo, contMat);
      continuationLine.computeLineDistances();
      scene.add(continuationLine);
      threeRef.current.continuationTube = continuationLine;
    }

    const milestonesGroup = new THREE.Group();
    milestonesGroup.name = 'milestonesGroup';

    // Launch Marker
    const launchSphere = new THREE.Mesh(
      new THREE.SphereGeometry(0.24, 16, 16),
      new THREE.MeshStandardMaterial({ color: 0x00e5ff, emissive: 0x00aacc, emissiveIntensity: 0.7 })
    );
    launchSphere.position.copy(launchPos);
    milestonesGroup.add(launchSphere);

    const speedKmh = ((Math.hypot(pt0[4] || 0, pt0[5] || 0, pt0[6] || 0)) * 3.6);
    const launchBadge = createTelemetrySprite([
      'LAUNCH ORIGIN',
      `V₀ = ${speedKmh.toFixed(1)} km/h  |  z = ${(pt0[3] || 0.9).toFixed(2)} m`,
    ], {
      fontSize: 10,
      bgColor: 'rgba(8, 14, 26, 0.94)',
      borderColor: 'rgba(0, 229, 255, 0.9)',
      textColor: '#e0f2fe',
      highlightColor: '#00e5ff',
      height: 38,
      worldHeight: 0.28,
    });
    // Positioned safely to the off-side (+X) and mid-elevation (leaves batsman face and top toolbar completely clear)
    const badgeY = Math.max(1.25, launchPos.y + 0.35);
    launchBadge.position.set(launchPos.x + 1.6, badgeY, launchPos.z);
    milestonesGroup.add(launchBadge);

    // Subtle dashed leader line from ball launch point to telemetry badge
    const launchPlumbGeo = new THREE.BufferGeometry().setFromPoints([
      launchPos,
      new THREE.Vector3(launchPos.x + 1.6, badgeY, launchPos.z),
    ]);
    const launchPlumbLine = new THREE.Line(
      launchPlumbGeo,
      new THREE.LineDashedMaterial({ color: 0x00e5ff, dashSize: 0.15, gapSize: 0.12, transparent: true, opacity: 0.65 })
    );
    launchPlumbLine.computeLineDistances();
    milestonesGroup.add(launchPlumbLine);

    // Apex Marker
    if (apexPoint && apexHeight > 1.5) {
      const apexSphere = new THREE.Mesh(
        new THREE.SphereGeometry(0.26, 16, 16),
        new THREE.MeshStandardMaterial({ color: 0xf59e0b, emissive: 0xb45309, emissiveIntensity: 0.6 })
      );
      apexSphere.position.copy(apexPoint);
      milestonesGroup.add(apexSphere);

      const apexBadge = createTelemetrySprite([
        `APEX: ${apexHeight.toFixed(2)} m`,
        `t = ${apexTime.toFixed(2)} s`,
      ], {
        fontSize: 11,
        bgColor: 'rgba(15, 23, 42, 0.92)',
        borderColor: 'rgba(245, 158, 11, 0.9)',
        textColor: '#fef3c7',
        highlightColor: '#f59e0b',
        width: 130,
        height: 38,
      });
      apexBadge.position.set(apexPoint.x, apexPoint.y + 0.85, apexPoint.z);
      milestonesGroup.add(apexBadge);
    }

    // Catch Reticle
    if (isCaught && catchVec) {
      const fName = interception.role_name || interception.fielder_name || 'Fielder';
      const catchZ = Math.max(0.25, catchVec.y);

      const cGeo = new THREE.OctahedronGeometry(0.32);
      const cMat = new THREE.MeshStandardMaterial({
        color: 0xef4444,
        emissive: 0x991b1b,
        emissiveIntensity: 0.7,
      });
      const cMesh = new THREE.Mesh(cGeo, cMat);
      cMesh.position.copy(catchVec);
      milestonesGroup.add(cMesh);

      const plumbPts = [catchVec, new THREE.Vector3(catchVec.x, 0.04, catchVec.z)];
      const plumbLine = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(plumbPts),
        new THREE.LineDashedMaterial({ color: 0xef4444, dashSize: 0.3, gapSize: 0.2, transparent: true, opacity: 0.8 })
      );
      plumbLine.computeLineDistances();
      milestonesGroup.add(plumbLine);

      const catchBadge = createTelemetrySprite([
        `OUT: CAUGHT (${fName})`,
        `t = ${catchTime.toFixed(2)}s  |  z = ${catchZ.toFixed(2)}m`,
      ], {
        fontSize: 11,
        bgColor: 'rgba(20, 5, 8, 0.95)',
        borderColor: 'rgba(239, 68, 68, 0.95)',
        textColor: '#fee2e2',
        highlightColor: '#ef4444',
        width: 200,
        height: 44,
      });
      catchBadge.position.set(catchVec.x, catchVec.y + 1.1, catchVec.z);
      milestonesGroup.add(catchBadge);
    }

    // Ground Impact Reticle
    if (firstImpactVec) {
      const carryDist = Number(metrics?.carry_distance_m != null ? metrics.carry_distance_m : (metrics?.d_pitch || 0));

      const ringOuter = new THREE.Mesh(
        new THREE.RingGeometry(0.5, 0.8, 48),
        new THREE.MeshBasicMaterial({ color: 0x38bdf8, side: THREE.DoubleSide, transparent: true, opacity: 0.85 })
      );
      ringOuter.rotation.x = -Math.PI / 2;
      ringOuter.position.set(firstImpactVec.x, 0.03, firstImpactVec.z);
      milestonesGroup.add(ringOuter);

      const ringInner = new THREE.Mesh(
        new THREE.RingGeometry(0.18, 0.35, 36),
        new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide })
      );
      ringInner.rotation.x = -Math.PI / 2;
      ringInner.position.set(firstImpactVec.x, 0.035, firstImpactVec.z);
      milestonesGroup.add(ringInner);

      const chMat = new THREE.LineBasicMaterial({ color: 0x38bdf8 });
      const ch1 = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(firstImpactVec.x - 1.0, 0.04, firstImpactVec.z),
          new THREE.Vector3(firstImpactVec.x + 1.0, 0.04, firstImpactVec.z),
        ]),
        chMat
      );
      const ch2 = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(firstImpactVec.x, 0.04, firstImpactVec.z - 1.0),
          new THREE.Vector3(firstImpactVec.x, 0.04, firstImpactVec.z + 1.0),
        ]),
        chMat
      );
      milestonesGroup.add(ch1);
      milestonesGroup.add(ch2);

      const dropPts = [
        new THREE.Vector3(firstImpactVec.x, 1.8, firstImpactVec.z),
        new THREE.Vector3(firstImpactVec.x, 0.04, firstImpactVec.z),
      ];
      const dropLine = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(dropPts),
        new THREE.LineDashedMaterial({ color: 0x38bdf8, dashSize: 0.25, gapSize: 0.2, transparent: true, opacity: 0.6 })
      );
      dropLine.computeLineDistances();
      milestonesGroup.add(dropLine);

      const impactLabel = isCaught
        ? `Hypothetical Pitch: ${carryDist.toFixed(1)} m`
        : `1st Impact: ${carryDist.toFixed(1)} m`;

      const impactBadge = createTelemetrySprite([
        impactLabel,
        `Coords: [${(metrics?.first_landing_pos_m?.[0] || 0).toFixed(1)}, ${(metrics?.first_landing_pos_m?.[1] || 0).toFixed(1)}] m`,
      ], {
        fontSize: 11,
        bgColor: 'rgba(8, 20, 36, 0.94)',
        borderColor: 'rgba(56, 189, 248, 0.9)',
        textColor: '#e0f2fe',
        highlightColor: '#38bdf8',
        width: 175,
        height: 42,
      });
      impactBadge.position.set(firstImpactVec.x, 2.15, firstImpactVec.z);
      milestonesGroup.add(impactBadge);
    }

    scene.add(milestonesGroup);
    threeRef.current.milestonesGroup = milestonesGroup;

    ballMesh.position.copy(launchPos);
    ballMesh.visible = true;

  }, [trajectory, metrics]);

  // ── Live Ball Playback Animation ───────────────────────────────────────────
  useEffect(() => {
    if (!threeRef.current?.ballMesh || !trajectory || trajectory.length === 0) return;
    const t = playback.currentTime;
    let state = trajectory[0];

    for (let i = 0; i < trajectory.length - 1; i++) {
      if (t >= trajectory[i][0] && t <= trajectory[i + 1][0]) {
        const alpha = (t - trajectory[i][0]) / (trajectory[i + 1][0] - trajectory[i][0]);
        state = trajectory[i].map((v, idx) => {
          if (idx === 0) return t;
          return v + alpha * (trajectory[i + 1][idx] - v);
        });
        break;
      }
    }

    const pos = simToThree(state[1], state[2], state[3]);
    threeRef.current.ballMesh.position.copy(pos);

    const heightRatio = Math.min(1, state[3] / 25);
    threeRef.current.ballMesh.material.emissiveIntensity = 0.15 + heightRatio * 0.6;
  }, [playback.currentTime, trajectory]);

  // ── Dynamic Camera Presets & Focus Actions ────────────────────────────────
  useEffect(() => {
    if (!threeRef.current?.camera || !threeRef.current?.controls) return;
    const { camera, controls } = threeRef.current;

    switch (cameraView) {
      case 'reset':
      case 'isometric': {
        camera.position.set(-42, 34, 52);
        controls.target.set(0, 2, -6);
        break;
      }
      case 'focus-pitch': {
        camera.position.set(-9, 7.5, Z_BAT - 10.06 + 14);
        controls.target.set(0, 0.8, Z_BAT - 10.06);
        break;
      }
      case 'focus-impact': {
        const interception = metrics?.fielder_interception;
        const isCaught = Boolean(interception && interception.can_intercept);
        if (metrics?.first_landing_pos_m && metrics.first_landing_pos_m.length >= 2) {
          const iv = simToThree(metrics.first_landing_pos_m[0], metrics.first_landing_pos_m[1], 0);
          camera.position.set(iv.x - 14, 11, iv.z + 16);
          controls.target.set(iv.x, 0.5, iv.z);
        } else if (isCaught && interception?.intercept_position_m) {
          const cv = simToThree(
            interception.intercept_position_m[0],
            interception.intercept_position_m[1],
            interception.intercept_position_m[2]
          );
          camera.position.set(cv.x - 12, cv.y + 6, cv.z + 14);
          controls.target.set(cv.x, cv.y, cv.z);
        } else {
          camera.position.set(-36, 26, 40);
          controls.target.set(0, 2, -6);
        }
        break;
      }
      case 'side': {
        const pt0 = trajectory?.[0] || [0, 0, 0, 0, 25, 0, 15];
        const vx = pt0[4] || 25;
        const vy = pt0[5] || 0;
        const vxy = Math.hypot(vx, vy) || 1;

        const nx = vx / vxy;
        const nz = -vy / vxy;

        const carry = metrics?.carry_distance_m || 45;
        const midDist = carry * 0.45;
        const targetX = -(vy / vxy) * midDist;
        const targetZ = Z_BAT - (vx / vxy) * midDist;
        const targetY = Math.max(3.5, (metrics?.max_height_m || 8) * 0.5);

        const camDist = Math.max(45, carry * 0.95);
        camera.position.set(targetX + nx * camDist, targetY + 4, targetZ + nz * camDist);
        controls.target.set(targetX, targetY, targetZ);
        break;
      }
      case 'top': {
        camera.position.set(0, 125, Z_BAT - 10);
        controls.target.set(0, 0, Z_BAT - 10);
        break;
      }
      case 'rear': {
        camera.position.set(0, 4.5, Z_BAT + 12);
        controls.target.set(0, 3, Z_BAT - 25);
        break;
      }
      case 'bowler': {
        camera.position.set(0, 5, Z_BAT - 26);
        controls.target.set(0, 2, Z_BAT);
        break;
      }
      default:
        break;
    }
    controls.update();
  }, [cameraView, trajectory, metrics]);

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-full block cursor-grab active:cursor-grabbing outline-none"
    />
  );
}
