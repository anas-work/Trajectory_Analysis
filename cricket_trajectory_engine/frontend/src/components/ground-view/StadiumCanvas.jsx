import React, { useRef, useEffect } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { useApp } from '../../context/AppContext';

export default function StadiumCanvas() {
  const canvasRef = useRef(null);
  const threeRef = useRef(null);
  const { trajectory, metrics, fielders, theme, playback, cameraView, setPlayback } = useApp();

  // Helper: Create Text Sprite
  const createTextSprite = (text) => {
    const canvas = document.createElement('canvas');
    canvas.width = 180;
    canvas.height = 44;
    const ctx = canvas.getContext('2d');

    ctx.fillStyle = 'rgba(10, 14, 20, 0.85)';
    ctx.strokeStyle = 'rgba(0, 210, 255, 0.7)';
    ctx.lineWidth = 2;
    if (ctx.roundRect) {
      ctx.beginPath();
      ctx.roundRect(4, 4, 172, 36, 6);
      ctx.fill();
      ctx.stroke();
    } else {
      ctx.fillRect(4, 4, 172, 36);
      ctx.strokeRect(4, 4, 172, 36);
    }

    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 14px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, 90, 22);

    const texture = new THREE.CanvasTexture(canvas);
    const spriteMat = new THREE.SpriteMaterial({ map: texture, transparent: true });
    const sprite = new THREE.Sprite(spriteMat);
    sprite.scale.set(3.4, 0.85, 1.0);
    return sprite;
  };

  // Helper: Build Wickets
  const buildWickets = (group, x, z) => {
    const stumpMat = new THREE.MeshStandardMaterial({ color: 0xe0c088, roughness: 0.5 });
    for (let offset = -0.11; offset <= 0.11; offset += 0.11) {
      const stumpGeo = new THREE.CylinderGeometry(0.02, 0.02, 0.71, 8);
      const stump = new THREE.Mesh(stumpGeo, stumpMat);
      stump.position.set(x + offset, 0.355, z);
      group.add(stump);
    }
  };

  // Helper: Build Batsman Humanoid
  const buildBatsman = (group, x, z) => {
    const batsman = new THREE.Group();
    batsman.name = 'batsmanHumanoid';
    batsman.position.set(x, 0, z);

    const skinMat = new THREE.MeshStandardMaterial({ color: 0xd4a373, roughness: 0.6 });
    const pantsMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.7 });
    const padMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.35 });
    const shoeMat = new THREE.MeshStandardMaterial({ color: 0xf1f5f9, roughness: 0.3 });
    const jerseyMat = new THREE.MeshStandardMaterial({ color: 0x1e3a8a, roughness: 0.65 });
    const helmetMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.3 });
    const grilleMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.85, roughness: 0.2 });
    const gloveMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.4 });
    const batBladeMat = new THREE.MeshStandardMaterial({ color: 0xdfad7b, roughness: 0.45 });
    const batHandleMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.7 });

    // Shoes
    const shoeL = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.08, 0.26), shoeMat);
    shoeL.position.set(-0.06, 0.04, -0.22);
    batsman.add(shoeL);

    const shoeR = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.08, 0.26), shoeMat);
    shoeR.position.set(0.16, 0.04, 0.12);
    batsman.add(shoeR);

    // Pads
    const legL = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.05, 0.46, 8), pantsMat);
    legL.position.set(-0.06, 0.30, -0.20);
    batsman.add(legL);

    const padL = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.52, 0.12), padMat);
    padL.position.set(-0.06, 0.32, -0.25);
    batsman.add(padL);

    const legR = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.05, 0.46, 8), pantsMat);
    legR.position.set(0.16, 0.30, 0.12);
    batsman.add(legR);

    const padR = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.52, 0.12), padMat);
    padR.position.set(0.16, 0.32, 0.07);
    batsman.add(padR);

    // Torso
    const torso = new THREE.Mesh(new THREE.BoxGeometry(0.36, 0.46, 0.22), jerseyMat);
    torso.position.set(0.05, 1.18, -0.04);
    batsman.add(torso);

    // Head & Helmet
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.11, 14, 14), skinMat);
    head.position.set(0.05, 1.57, -0.02);
    batsman.add(head);

    const helmet = new THREE.Mesh(new THREE.SphereGeometry(0.125, 16, 16, 0, Math.PI * 2, 0, Math.PI * 0.72), helmetMat);
    helmet.position.set(0.05, 1.58, -0.02);
    batsman.add(helmet);

    const peak = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.02, 0.10), helmetMat);
    peak.position.set(0.05, 1.56, -0.13);
    peak.rotation.x = 0.15;
    batsman.add(peak);

    const grille = new THREE.Mesh(new THREE.TorusGeometry(0.09, 0.008, 6, 16, Math.PI), grilleMat);
    grille.position.set(0.05, 1.53, -0.09);
    grille.rotation.x = -Math.PI / 2;
    batsman.add(grille);

    // Bat
    const batHandle = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.34, 8), batHandleMat);
    batHandle.position.set(0.0, 0.76, -0.11);
    batHandle.rotation.x = 0.35;
    batHandle.rotation.z = -0.15;
    batsman.add(batHandle);

    const batBlade = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.60, 0.035), batBladeMat);
    batBlade.position.set(-0.06, 0.36, -0.02);
    batBlade.rotation.x = 0.35;
    batBlade.rotation.z = -0.15;
    batsman.add(batBlade);

    group.add(batsman);
  };

  // Helper: Build Humanoid Fielder
  const createHumanoidFielder = (f, posX, posZ) => {
    const fielderGroup = new THREE.Group();
    const isKeeper = f.role === 'wicketkeeper' || f.name.includes('Keeper');

    const jerseyColor = isKeeper ? 0xf5a623 : 0x00b4d8;
    const pantsMat = new THREE.MeshStandardMaterial({ color: 0xf5f7fa, roughness: 0.6 });
    const jerseyMat = new THREE.MeshStandardMaterial({ color: jerseyColor, roughness: 0.5 });
    const skinMat = new THREE.MeshStandardMaterial({ color: 0xffdfc4, roughness: 0.5 });
    const capMat = new THREE.MeshStandardMaterial({ color: isKeeper ? 0xd35400 : 0x073b4c, roughness: 0.4 });

    // Legs
    const legGeo = new THREE.CylinderGeometry(0.08, 0.07, 0.72, 8);
    const leftLeg = new THREE.Mesh(legGeo, pantsMat);
    leftLeg.position.set(-0.13, 0.36, 0.0);
    fielderGroup.add(leftLeg);

    const rightLeg = new THREE.Mesh(legGeo, pantsMat);
    rightLeg.position.set(0.13, 0.36, 0.0);
    fielderGroup.add(rightLeg);

    // Torso
    const torsoGeo = new THREE.BoxGeometry(0.38, 0.52, 0.24);
    const torso = new THREE.Mesh(torsoGeo, jerseyMat);
    torso.position.set(0, 0.95, 0.02);
    fielderGroup.add(torso);

    // Head & Cap
    const headGeo = new THREE.SphereGeometry(0.13, 12, 12);
    const head = new THREE.Mesh(headGeo, skinMat);
    head.position.set(0, 1.34, 0.04);
    fielderGroup.add(head);

    const capGeo = new THREE.SphereGeometry(0.135, 12, 12, 0, Math.PI * 2, 0, Math.PI / 2);
    const cap = new THREE.Mesh(capGeo, capMat);
    cap.position.set(0, 1.37, 0.04);
    fielderGroup.add(cap);

    // Catching reach ring
    const reachR = f.catching_radius || 1.8;
    const reachGeo = new THREE.RingGeometry(reachR - 0.06, reachR, 32);
    const reachMat = new THREE.MeshBasicMaterial({
      color: isKeeper ? 0xf5a623 : 0x00b4d8,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.28,
    });
    const reachRing = new THREE.Mesh(reachGeo, reachMat);
    reachRing.rotation.x = -Math.PI / 2;
    reachRing.position.y = 0.04;
    fielderGroup.add(reachRing);

    // Name Sprite
    const nameSprite = createTextSprite(f.name);
    nameSprite.position.set(0, isKeeper ? 1.45 : 1.85, 0);
    fielderGroup.add(nameSprite);

    // Position and face batsman at (0, 0, 8.84)
    fielderGroup.position.set(posX, 0, posZ);
    fielderGroup.rotation.y = Math.atan2(0 - posX, 8.84 - posZ);

    return fielderGroup;
  };

  // Build Full Stadium Environment
  const buildStadium = (group) => {
    const Z_BAT = 8.84;

    // 0. Infinite Outer Ground Apron (Radius 260m)
    const apronGeo = new THREE.CircleGeometry(260, 64);
    const apronMat = new THREE.MeshStandardMaterial({ color: 0x07090e, roughness: 0.95 });
    const apronMesh = new THREE.Mesh(apronGeo, apronMat);
    apronMesh.rotation.x = -Math.PI / 2;
    apronMesh.position.set(0, -0.05, Z_BAT);
    group.add(apronMesh);

    // 1. Outfield Grass Disc (Radius 84m)
    const grassGeo = new THREE.CircleGeometry(84, 64);
    const grassMat = new THREE.MeshStandardMaterial({ color: 0x0f2e1b, roughness: 0.82 });
    const grassMesh = new THREE.Mesh(grassGeo, grassMat);
    grassMesh.rotation.x = -Math.PI / 2;
    grassMesh.position.set(0, 0, Z_BAT);
    group.add(grassMesh);

    // Concentric mowing stripe rings
    for (let r = 8; r < 82; r += 7) {
      const ringGeo = new THREE.RingGeometry(r, r + 3.5, 64);
      const ringMat = new THREE.MeshBasicMaterial({ color: 0x143c24, side: THREE.DoubleSide });
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.rotation.x = -Math.PI / 2;
      ringMesh.position.set(0, 0.01, Z_BAT);
      group.add(ringMesh);
    }

    // 2. Pitch Strip (20.12m x 3.05m)
    const pitchGeo = new THREE.PlaneGeometry(3.05, 20.12);
    const pitchMat = new THREE.MeshStandardMaterial({ color: 0xbfa77a, roughness: 0.65 });
    const pitchMesh = new THREE.Mesh(pitchGeo, pitchMat);
    pitchMesh.rotation.x = -Math.PI / 2;
    pitchMesh.position.set(0, 0.02, 0);
    group.add(pitchMesh);

    // Creases
    const lineMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    const creaseBat = new THREE.Mesh(new THREE.PlaneGeometry(3.66, 0.08), lineMat);
    creaseBat.rotation.x = -Math.PI / 2;
    creaseBat.position.set(0, 0.03, Z_BAT);
    group.add(creaseBat);

    const creaseBowl = new THREE.Mesh(new THREE.PlaneGeometry(3.66, 0.08), lineMat);
    creaseBowl.rotation.x = -Math.PI / 2;
    creaseBowl.position.set(0, 0.03, -Z_BAT);
    group.add(creaseBowl);

    // Wickets
    buildWickets(group, 0, 10.06);
    buildWickets(group, 0, -10.06);

    // Batsman Humanoid
    buildBatsman(group, 0.15, Z_BAT);

    // 30-Yard Infield Circle
    const circle30Geo = new THREE.RingGeometry(27.35, 27.5, 64);
    const circle30Mat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.45,
    });
    const circle30Mesh = new THREE.Mesh(circle30Geo, circle30Mat);
    circle30Mesh.rotation.x = -Math.PI / 2;
    circle30Mesh.position.set(0, 0.03, Z_BAT);
    group.add(circle30Mesh);

    // Boundary Rope (70m radius)
    const boundaryRadius = 70.0;
    const ropeGeo = new THREE.TorusGeometry(boundaryRadius, 0.16, 8, 80);
    const ropeMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.35 });
    const ropeMesh = new THREE.Mesh(ropeGeo, ropeMat);
    ropeMesh.rotation.x = Math.PI / 2;
    ropeMesh.position.set(0, 0.12, Z_BAT);
    group.add(ropeMesh);

    // Foam Boundary Cushions
    const foamGeo = new THREE.ConeGeometry(0.35, 0.45, 4);
    const foamMat = new THREE.MeshStandardMaterial({ color: 0x10b981, roughness: 0.4 });
    for (let a = 0; a < Math.PI * 2; a += Math.PI / 16) {
      const foam = new THREE.Mesh(foamGeo, foamMat);
      foam.position.set(Math.cos(a) * boundaryRadius, 0.22, Z_BAT + Math.sin(a) * boundaryRadius);
      group.add(foam);
    }

    // Grandstand Seating Bowl
    const tier1Geo = new THREE.CylinderGeometry(90, 84, 2.8, 64, 1, true);
    const tier1Mat = new THREE.MeshStandardMaterial({ color: 0x881337, roughness: 0.7 });
    const tier1Mesh = new THREE.Mesh(tier1Geo, tier1Mat);
    tier1Mesh.position.set(0, 1.4, Z_BAT);
    group.add(tier1Mesh);

    const tier2Geo = new THREE.CylinderGeometry(96, 90, 3.7, 64, 1, true);
    const tier2Mat = new THREE.MeshStandardMaterial({ color: 0x064e3b, roughness: 0.7 });
    const tier2Mesh = new THREE.Mesh(tier2Geo, tier2Mat);
    tier2Mesh.position.set(0, 4.65, Z_BAT);
    group.add(tier2Mesh);

    const tier3Geo = new THREE.CylinderGeometry(102, 96, 5.0, 64, 1, true);
    const tier3Mat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.7 });
    const tier3Mesh = new THREE.Mesh(tier3Geo, tier3Mat);
    tier3Mesh.position.set(0, 9.0, Z_BAT);
    group.add(tier3Mesh);

    // 4 Floodlight Pylons
    const towerPositions = [
      { x: 80, z: Z_BAT + 80 },
      { x: -80, z: Z_BAT + 80 },
      { x: 80, z: Z_BAT - 80 },
      { x: -80, z: Z_BAT - 80 },
    ];
    const pylonMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.6, roughness: 0.4 });
    towerPositions.forEach((pos) => {
      const mastGeo = new THREE.CylinderGeometry(0.55, 0.95, 36, 8);
      const mast = new THREE.Mesh(mastGeo, pylonMat);
      mast.position.set(pos.x, 18, pos.z);
      group.add(mast);

      const headGeo = new THREE.BoxGeometry(6.5, 3.2, 0.8);
      const head = new THREE.Mesh(headGeo, pylonMat);
      head.position.set(pos.x, 36.5, pos.z);
      head.lookAt(0, 10, Z_BAT);
      group.add(head);

      const towerLight = new THREE.PointLight(0xfff8e7, 0.45, 180);
      towerLight.position.set(pos.x * 0.9, 36, Z_BAT + (pos.z - Z_BAT) * 0.9);
      group.add(towerLight);
    });
  };

  // Initial WebGL Setup
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const width = canvas.parentElement?.clientWidth || 800;
    const height = canvas.parentElement?.clientHeight || 500;

    const scene = new THREE.Scene();
    const bgHex = theme === 'titanium' ? 0x0d1117 : (theme === 'carbon' ? 0x010204 : 0x090a0f);
    scene.background = new THREE.Color(bgHex);
    scene.fog = new THREE.Fog(bgHex, 150, 480);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1500);
    camera.position.set(28, 30, 32);

    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 6.0;
    controls.maxDistance = 160.0;
    controls.maxPolarAngle = Math.PI / 2 - 0.04;
    controls.target.set(0, 2, -10);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.75);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xfffaed, 0.85);
    dirLight.position.set(30, 90, 40);
    scene.add(dirLight);

    // Stadium Architecture
    const stadiumGroup = new THREE.Group();
    scene.add(stadiumGroup);
    buildStadium(stadiumGroup);

    // Ball Mesh
    const ballGeo = new THREE.SphereGeometry(0.35, 16, 16);
    const ballMat = new THREE.MeshStandardMaterial({ color: 0xd90429, roughness: 0.3 });
    const ballMesh = new THREE.Mesh(ballGeo, ballMat);
    ballMesh.visible = false;
    scene.add(ballMesh);

    // Apex Marker & Line
    const apexGeo = new THREE.SphereGeometry(0.3, 12, 12);
    const apexMat = new THREE.MeshBasicMaterial({ color: 0xf5a623 });
    const apexMarker = new THREE.Mesh(apexGeo, apexMat);
    apexMarker.visible = false;
    scene.add(apexMarker);

    const dropLineMat = new THREE.LineDashedMaterial({ color: 0xffffff, dashSize: 0.5, gapSize: 0.5 });
    const dropLineGeo = new THREE.BufferGeometry();
    const apexDropLine = new THREE.Line(dropLineGeo, dropLineMat);
    apexDropLine.visible = false;
    scene.add(apexDropLine);

    threeRef.current = {
      scene,
      camera,
      renderer,
      controls,
      stadiumGroup,
      ballMesh,
      apexMarker,
      apexDropLine,
      flightLine: null,
      rollLine: null,
      firstImpactGroup: null,
      fielderMeshes: [],
    };

    let animationFrameId;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!canvas || !renderer || !camera) return;
      const w = canvas.parentElement?.clientWidth || 800;
      const h = canvas.parentElement?.clientHeight || 500;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
      threeRef.current = null;
    };
  }, []);

  // Update Theme Colors
  useEffect(() => {
    if (!threeRef.current) return;
    const bgHex = theme === 'titanium' ? 0x0d1117 : (theme === 'carbon' ? 0x010204 : 0x090a0f);
    threeRef.current.scene.background = new THREE.Color(bgHex);
    threeRef.current.scene.fog = new THREE.Fog(bgHex, 150, 480);
  }, [theme]);

  // Update Fielders in 3D
  useEffect(() => {
    if (!threeRef.current) return;
    const { scene, fielderMeshes } = threeRef.current;

    fielderMeshes.forEach((mesh) => scene.remove(mesh));
    threeRef.current.fielderMeshes = [];

    fielders.forEach((f) => {
      const posX = -f.y;
      const posZ = 8.84 - f.x;
      const mesh = createHumanoidFielder(f, posX, posZ);
      scene.add(mesh);
      threeRef.current.fielderMeshes.push(mesh);
    });
  }, [fielders]);

  // Update Trajectory Lines & Markers
  useEffect(() => {
    if (!threeRef.current || !trajectory || trajectory.length === 0) return;
    const { scene, apexMarker, apexDropLine, ballMesh } = threeRef.current;

    if (threeRef.current.flightLine) scene.remove(threeRef.current.flightLine);
    if (threeRef.current.rollLine) scene.remove(threeRef.current.rollLine);
    if (threeRef.current.firstImpactGroup) {
      scene.remove(threeRef.current.firstImpactGroup);
      threeRef.current.firstImpactGroup = null;
    }

    const flightPoints = [];
    const rollPoints = [];
    let apexPoint = null;
    let maxZ = -Infinity;
    let firstImpactPoint = null;

    trajectory.forEach((pt) => {
      const px = -pt[2];
      const py = Math.max(0, pt[3]);
      const pz = 8.84 - pt[1];
      const phase = pt[7] !== undefined ? pt[7] : (py > 0.05 ? 0 : 2);
      const vec = new THREE.Vector3(px, py, pz);

      if (phase === 0 || phase === 1) {
        flightPoints.push(vec);
      } else {
        rollPoints.push(vec);
        if (!firstImpactPoint) firstImpactPoint = vec;
      }

      if (pt[3] > maxZ) {
        maxZ = pt[3];
        apexPoint = vec;
      }
    });

    if (!firstImpactPoint && rollPoints.length > 0) {
      firstImpactPoint = rollPoints[0];
    } else if (!firstImpactPoint && metrics && metrics.first_landing_pos_m) {
      const flp = metrics.first_landing_pos_m;
      firstImpactPoint = new THREE.Vector3(-flp[1], Math.max(0.04, flp[2]), 8.84 - flp[0]);
    } else if (!firstImpactPoint && flightPoints.length > 0) {
      firstImpactPoint = flightPoints[flightPoints.length - 1];
    }

    if (flightPoints.length > 1) {
      const flightGeo = new THREE.BufferGeometry().setFromPoints(flightPoints);
      const flightMat = new THREE.LineBasicMaterial({ color: 0x00d2ff, linewidth: 3 });
      threeRef.current.flightLine = new THREE.Line(flightGeo, flightMat);
      scene.add(threeRef.current.flightLine);
    }

    if (rollPoints.length > 1) {
      const rollGeo = new THREE.BufferGeometry().setFromPoints(rollPoints);
      const rollMat = new THREE.LineBasicMaterial({ color: 0xf1c40f, linewidth: 2 });
      threeRef.current.rollLine = new THREE.Line(rollGeo, rollMat);
      scene.add(threeRef.current.rollLine);
    }

    if (apexPoint && apexMarker && apexDropLine) {
      apexMarker.position.copy(apexPoint);
      apexMarker.visible = true;

      const dropPoints = [apexPoint, new THREE.Vector3(apexPoint.x, 0.05, apexPoint.z)];
      apexDropLine.geometry.setFromPoints(dropPoints);
      apexDropLine.computeLineDistances();
      apexDropLine.visible = true;
    }

    // Impact Marker
    if (firstImpactPoint && metrics) {
      const impactGroup = new THREE.Group();
      const ringGeo = new THREE.RingGeometry(0.35, 0.65, 32);
      const ringMat = new THREE.MeshBasicMaterial({
        color: 0x38bdf8,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.85,
      });
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.rotation.x = -Math.PI / 2;
      ringMesh.position.set(firstImpactPoint.x, 0.04, firstImpactPoint.z);
      impactGroup.add(ringMesh);

      const centerDisk = new THREE.Mesh(
        new THREE.CircleGeometry(0.18, 16),
        new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide })
      );
      centerDisk.rotation.x = -Math.PI / 2;
      centerDisk.position.set(firstImpactPoint.x, 0.045, firstImpactPoint.z);
      impactGroup.add(centerDisk);

      const carryDist = Number(metrics.carry_distance_m !== undefined && metrics.carry_distance_m !== null
        ? metrics.carry_distance_m
        : (metrics.d_pitch || 0));
      if (carryDist > 0) {
        const labelSprite = createTextSprite(`1st Impact: ${carryDist.toFixed(1)}m`);
        labelSprite.position.set(firstImpactPoint.x, 1.3, firstImpactPoint.z);
        impactGroup.add(labelSprite);
      }

      scene.add(impactGroup);
      threeRef.current.firstImpactGroup = impactGroup;
    }

    // Reset ball position
    if (trajectory.length > 0 && ballMesh) {
      const start = trajectory[0];
      ballMesh.position.set(-start[2], Math.max(0, start[3]), 8.84 - start[1]);
      ballMesh.visible = true;
    }
  }, [trajectory, metrics]);

  // Live Ball Animation
  useEffect(() => {
    if (!threeRef.current || !threeRef.current.ballMesh || !trajectory || trajectory.length === 0) return;
    const t = playback.currentTime;
    let state = trajectory[0];

    for (let i = 0; i < trajectory.length - 1; i++) {
      if (t >= trajectory[i][0] && t <= trajectory[i + 1][0]) {
        const alpha = (t - trajectory[i][0]) / (trajectory[i + 1][0] - trajectory[i][0]);
        state = [
          t,
          trajectory[i][1] + alpha * (trajectory[i + 1][1] - trajectory[i][1]),
          trajectory[i][2] + alpha * (trajectory[i + 1][2] - trajectory[i][2]),
          trajectory[i][3] + alpha * (trajectory[i + 1][3] - trajectory[i][3]),
          trajectory[i][4] + alpha * (trajectory[i + 1][4] - trajectory[i][4]),
          trajectory[i][5] + alpha * (trajectory[i + 1][5] - trajectory[i][5]),
          trajectory[i][6] + alpha * (trajectory[i + 1][6] - trajectory[i][6]),
        ];
        break;
      }
    }

    threeRef.current.ballMesh.position.set(-state[2], Math.max(0, state[3]), 8.84 - state[1]);
  }, [playback.currentTime, trajectory]);

  // Camera Presets
  useEffect(() => {
    if (!threeRef.current || !threeRef.current.camera || !threeRef.current.controls) return;
    const { camera, controls } = threeRef.current;

    switch (cameraView) {
      case 'isometric':
        camera.position.set(-30, 32, 38);
        controls.target.set(0, 3, -10);
        break;
      case 'side':
        camera.position.set(70, 15, -6);
        controls.target.set(0, 4, -6);
        break;
      case 'top':
        camera.position.set(0, 145, 8.84);
        controls.target.set(0, 0, 8.84);
        break;
      case 'rear':
        camera.position.set(0, 3.0, 19.0);
        controls.target.set(0, 4, -35);
        break;
      case 'bowler':
        camera.position.set(0, 4.0, -28);
        controls.target.set(0, 1.8, 8.84);
        break;
      default:
        break;
    }
    controls.update();
  }, [cameraView]);

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-full block cursor-grab active:cursor-grabbing outline-none"
    />
  );
}

