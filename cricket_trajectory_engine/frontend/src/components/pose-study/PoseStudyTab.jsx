import React, { useState } from 'react';
import { 
  Play, 
  Activity, 
  UserCheck, 
  ShieldAlert, 
  Compass, 
  Zap, 
  BarChart2, 
  Info, 
  ChevronRight,
  TrendingUp,
  CheckCircle2,
  XCircle,
  AlertTriangle
} from 'lucide-react';

const DELIVERIES_DATA = {
  "01": {
    id: "01",
    title: "Delivery 01: Forward Defensive / Push",
    folder: "01_Thebpca1_2026-08-19_cam1_d26_cam2_d27",
    hitFrame: 61,
    groundTruth: {
      shot: "Forward Defensive / Push",
      footwork: "Front-foot",
      elevation: "Grounded",
      speed: "17.7 km/h",
      launchElevation: "+4.5°",
      azimuth: "+10.3°"
    },
    posePrediction: {
      primaryShot: "Front-foot drive",
      secondaryShot: "Forward defensive / push",
      footwork: "Front-foot",
      elevation: "Grounded",
      confidence: "80.0%",
      strideRatio: 1.01,
      frontKneeAngle: "179.4°",
      torsoLean: "10.8°",
      armExtension: 0.88,
      shotMatch: false,
      footworkMatch: true
    },
    targetEvaluation: {
      targetClassified: "Main Striker Batsman",
      boxArea: "895,420 px²",
      boxLocation: "At batting crease (x: 529-1042, y: 1712-2721)",
      confidence: "0.950",
      bowlerFiltered: "Bowler/Non-Striker filtered out (Area: 87,300 px², x > 1500 px)",
      trackingStability: "100% across all 121 frames"
    },
    edgeDetection: {
      swingAzimuth: "+3.2°",
      ballExitAzimuth: "+10.3°",
      angularDiscrepancy: "7.1°",
      edgeStatus: "Middled Shot (No Edge)",
      edgeProbability: "3.2%",
      reasoning: "Swing azimuth and ball exit trajectory align within 7.1°. Low launch speed (17.7 km/h) confirms soft-handed defensive block."
    },
    phases: {
      stance: "Frames 0 - 14 (Settled in batting crease)",
      backswing: "Frame 15 (Wrists lift, trigger stride begins)",
      stride: "Frames 15 - 52 (Front foot strides forward along pitch)",
      execution: "Frames 53 - 59 (Downswing into ball line)",
      impact: "Frames 60 - 62 (Ball contact window)",
      followThrough: "Frames 63 - 120 (Checked follow-through)"
    },
    analyticalReason: "In 2D body pose, a forward defensive push shares an identical forward stride, lead shoulder dip, and vertical bat line with a front-foot drive. By cross-referencing ball exit speed (17.7 km/h), the engine correctly disambiguates the shot as a defensive push."
  },
  "02": {
    id: "02",
    title: "Delivery 02: Front-Foot Push / Drive",
    folder: "02_Theace1_2026-08-26_cam1_d35_cam2_d36",
    hitFrame: 50,
    groundTruth: {
      shot: "Front-Foot Push / Drive",
      footwork: "Front-foot",
      elevation: "Grounded",
      speed: "19.2 km/h",
      launchElevation: "-12.4°",
      azimuth: "+14.5°"
    },
    posePrediction: {
      primaryShot: "Front-foot drive",
      secondaryShot: "Forward defensive / push",
      footwork: "Front-foot",
      elevation: "Grounded",
      confidence: "80.0%",
      strideRatio: 1.51,
      frontKneeAngle: "176.5°",
      torsoLean: "22.3°",
      armExtension: 0.94,
      shotMatch: true,
      footworkMatch: true
    },
    targetEvaluation: {
      targetClassified: "Main Striker Batsman",
      boxArea: "948,367 px²",
      boxLocation: "At batting crease (x: 542-1125, y: 2063-3194)",
      confidence: "0.968",
      bowlerFiltered: "Non-striker in background filtered (Area: 87,849 px²)",
      trackingStability: "100% across all 121 frames"
    },
    edgeDetection: {
      swingAzimuth: "+21.8°",
      ballExitAzimuth: "+14.5°",
      angularDiscrepancy: "7.3°",
      edgeStatus: "Middled Shot (No Edge)",
      edgeProbability: "4.5%",
      reasoning: "Trajectory exit aligns with forward drive presentation. Negative elevation (-12.4°) confirms grounded stroke."
    },
    phases: {
      stance: "Frames 0 - 14",
      backswing: "Frame 15",
      stride: "Frames 15 - 41",
      execution: "Frames 42 - 48",
      impact: "Frames 49 - 51",
      followThrough: "Frames 52 - 120"
    },
    analyticalReason: "Extended stride ratio (1.51x) indicates aggressive forward stride down the ground. Forward torso lean of 22.3° keeps head positioned over the ball."
  },
  "03": {
    id: "03",
    title: "Delivery 03: Front-Foot Drive (Firm)",
    folder: "03_Theace9_2026-07-02_cam1_d5_cam2_d6",
    hitFrame: 47,
    groundTruth: {
      shot: "Front-Foot Drive (Firm)",
      footwork: "Front-foot",
      elevation: "Lofted / Firm",
      speed: "55.6 km/h",
      launchElevation: "+12.9°",
      azimuth: "-3.9°"
    },
    posePrediction: {
      primaryShot: "Front-foot drive",
      secondaryShot: "Forward defensive / push",
      footwork: "Front-foot",
      elevation: "Grounded",
      confidence: "80.0%",
      strideRatio: 0.72,
      frontKneeAngle: "129.5°",
      torsoLean: "61.3°",
      armExtension: 1.12,
      shotMatch: true,
      footworkMatch: true
    },
    targetEvaluation: {
      targetClassified: "Main Striker Batsman",
      boxArea: "770,250 px²",
      boxLocation: "At batting crease (x: 670-1409, y: 1271-2313)",
      confidence: "0.972",
      bowlerFiltered: "Bowler release filtered out",
      trackingStability: "100% across all 121 frames"
    },
    edgeDetection: {
      swingAzimuth: "-5.0°",
      ballExitAzimuth: "-3.9°",
      angularDiscrepancy: "1.1°",
      edgeStatus: "Middled Shot (Clean Middle)",
      edgeProbability: "0.8%",
      reasoning: "Near-perfect alignment between bat presentation and exit azimuth (-1.1°). High exit velocity (55.6 km/h) confirms clean power transfer."
    },
    phases: {
      stance: "Frames 0 - 16",
      backswing: "Frame 17",
      stride: "Frames 17 - 38",
      execution: "Frames 39 - 45",
      impact: "Frames 46 - 48",
      followThrough: "Frames 49 - 120"
    },
    analyticalReason: "High wrist velocity and arm extension (1.12) capture a firm straight drive. Exit speed reaches 55.6 km/h (highest in the 10-delivery dataset)."
  },
  "04": {
    id: "04",
    title: "Delivery 04: Forward Defensive (Smother)",
    folder: "04_Theace1_2026-08-17_cam1_d41_cam2_d40",
    hitFrame: 55,
    groundTruth: {
      shot: "Forward Defensive",
      footwork: "Front-foot",
      elevation: "Grounded",
      speed: "19.4 km/h",
      launchElevation: "-2.5°",
      azimuth: "-7.8°"
    },
    posePrediction: {
      primaryShot: "Sweep shot (False Positive)",
      secondaryShot: "Defensive",
      footwork: "Front-foot",
      elevation: "Grounded",
      confidence: "80.0%",
      strideRatio: 0.40,
      frontKneeAngle: "151.4°",
      torsoLean: "22.4°",
      armExtension: 0.81,
      shotMatch: false,
      footworkMatch: true
    },
    targetEvaluation: {
      targetClassified: "Main Striker Batsman",
      boxArea: "589,320 px²",
      boxLocation: "At batting crease (x: 613-1189, y: 1913-2936)",
      confidence: "0.965",
      bowlerFiltered: "Non-striker in background filtered",
      trackingStability: "100% across all 121 frames"
    },
    edgeDetection: {
      swingAzimuth: "-8.3°",
      ballExitAzimuth: "-7.8°",
      angularDiscrepancy: "0.5°",
      edgeStatus: "Middled Block (No Edge)",
      edgeProbability: "2.1%",
      reasoning: "Ball exit azimuth (-7.8°) is straight down the pitch. A genuine sweep shot travels at -60° to -110° to fine leg. Cross-referencing azimuth immediately corrects the sweep false positive!"
    },
    phases: {
      stance: "Frames 0 - 14",
      backswing: "Frame 15",
      stride: "Frames 15 - 46",
      execution: "Frames 47 - 53",
      impact: "Frames 54 - 56",
      followThrough: "Frames 57 - 120"
    },
    analyticalReason: "Key Failure Mode: The batsman dropped their back knee low to smother a dipping ball, causing 2D pose to misclassify the action as a sweep shot. The straight trajectory azimuth (-7.8°) invalidates the sweep classification."
  },
  "05": {
    id: "05",
    title: "Delivery 05: Front-Foot Drive / Punch",
    folder: "05_Thebpca1_2026-08-19_cam1_d31_cam2_d32",
    hitFrame: 55,
    groundTruth: {
      shot: "Front-Foot Drive / Punch",
      footwork: "Front-foot",
      elevation: "Grounded",
      speed: "32.5 km/h",
      launchElevation: "+4.7°",
      azimuth: "-7.1°"
    },
    posePrediction: {
      primaryShot: "Lofted On-Drive",
      secondaryShot: "Front-foot drive",
      footwork: "Front-foot",
      elevation: "Lofted",
      confidence: "90.0%",
      strideRatio: 0.87,
      frontKneeAngle: "177.1°",
      torsoLean: "9.9°",
      armExtension: 1.05,
      shotMatch: true,
      footworkMatch: true
    },
    targetEvaluation: {
      targetClassified: "Main Striker Batsman",
      boxArea: "475,700 px²",
      boxLocation: "At batting crease (x: 529-1012, y: 1681-2666)",
      confidence: "0.978",
      bowlerFiltered: "Background non-striker filtered",
      trackingStability: "100% across all 121 frames"
    },
    edgeDetection: {
      swingAzimuth: "-7.0°",
      ballExitAzimuth: "-7.1°",
      angularDiscrepancy: "0.1°",
      edgeStatus: "Clean Middle (No Edge)",
      edgeProbability: "0.5%",
      reasoning: "Exit velocity (32.5 km/h) and exact azimuth alignment confirm a crisp punch drive straight past mid-on."
    },
    phases: {
      stance: "Frames 0 - 17",
      backswing: "Frame 18",
      stride: "Frames 18 - 46",
      execution: "Frames 47 - 53",
      impact: "Frames 54 - 56",
      followThrough: "Frames 57 - 120"
    },
    analyticalReason: "Extended arm follow-through triggered lofted classifier, while trajectory elevation (+4.7°) confirms a flat punch drive."
  },
  "06": {
    id: "06",
    title: "Delivery 06: Forward Defensive (Late Block)",
    folder: "06_Thebpca1_2026-08-19_cam1_d23_cam2_d24",
    hitFrame: 60,
    groundTruth: {
      shot: "Forward Defensive",
      footwork: "Front-foot",
      elevation: "Grounded",
      speed: "20.6 km/h",
      launchElevation: "-8.6°",
      azimuth: "+6.8°"
    },
    posePrediction: {
      primaryShot: "Forward Defensive",
      secondaryShot: "Front-foot push",
      footwork: "Back-foot (Misclassified Footwork)",
      elevation: "Grounded",
      confidence: "82.0%",
      strideRatio: 0.13,
      frontKneeAngle: "177.7°",
      torsoLean: "7.5°",
      armExtension: 0.79,
      shotMatch: true,
      footworkMatch: false
    },
    targetEvaluation: {
      targetClassified: "Main Striker Batsman",
      boxArea: "483,500 px²",
      boxLocation: "At batting crease (x: 409-813, y: 1537-2734)",
      confidence: "0.967",
      bowlerFiltered: "Bowler release filtered out",
      trackingStability: "100% across all 121 frames"
    },
    edgeDetection: {
      swingAzimuth: "+7.6°",
      ballExitAzimuth: "+6.8°",
      angularDiscrepancy: "0.8°",
      edgeStatus: "Middled Defensive Block",
      edgeProbability: "1.9%",
      reasoning: "Defensive bat face presented straight. Exit speed of 20.6 km/h matches soft-handed block."
    },
    phases: {
      stance: "Frames 0 - 20",
      backswing: "Frame 21",
      stride: "Frames 21 - 51",
      execution: "Frames 52 - 58",
      impact: "Frames 59 - 61",
      followThrough: "Frames 62 - 120"
    },
    analyticalReason: "The batter made an initial step back in their crease before defending forward, causing footwork ratio to register low (0.13), resulting in back-foot label."
  },
  "07": {
    id: "07",
    title: "Delivery 07: Front-Foot Cover Drive",
    folder: "07_Theace1_2026-08-17_cam1_d12_cam2_d9",
    hitFrame: 56,
    groundTruth: {
      shot: "Front-Foot Cover Drive",
      footwork: "Front-foot",
      elevation: "Grounded",
      speed: "41.5 km/h",
      launchElevation: "-13.0°",
      azimuth: "+14.9°"
    },
    posePrediction: {
      primaryShot: "Sweep shot (False Positive)",
      secondaryShot: "Defensive",
      footwork: "Front-foot",
      elevation: "Lofted",
      confidence: "80.0%",
      strideRatio: 1.56,
      frontKneeAngle: "173.1°",
      torsoLean: "4.4°",
      armExtension: 1.15,
      shotMatch: false,
      footworkMatch: true
    },
    targetEvaluation: {
      targetClassified: "Main Striker Batsman",
      boxArea: "312,500 px²",
      boxLocation: "At batting crease (x: 546-881, y: 1961-2894)",
      confidence: "0.969",
      bowlerFiltered: "Bowler in background filtered",
      trackingStability: "100% across all 121 frames"
    },
    edgeDetection: {
      swingAzimuth: "+15.1°",
      ballExitAzimuth: "+14.9°",
      angularDiscrepancy: "0.2°",
      edgeStatus: "Clean Cover Drive (No Edge)",
      edgeProbability: "0.4%",
      reasoning: "Exit velocity (41.5 km/h) and off-side azimuth (+14.9°) confirm an authentic cover drive. Corrects the sweep false positive."
    },
    phases: {
      stance: "Frames 0 - 15",
      backswing: "Frame 16",
      stride: "Frames 16 - 47",
      execution: "Frames 48 - 54",
      impact: "Frames 55 - 57",
      followThrough: "Frames 58 - 120"
    },
    analyticalReason: "The batter dipped into a low cover drive. In 2D side-on projection, the deep crouch triggered sweep logic. High exit speed (41.5 km/h) and off-side azimuth easily resolve the true shot."
  },
  "08": {
    id: "08",
    title: "Delivery 08: Forward Defensive / Push",
    folder: "08_Theace1_2026-08-17_cam1_d84_cam2_d78",
    hitFrame: 54,
    groundTruth: {
      shot: "Forward Defensive / Push",
      footwork: "Front-foot",
      elevation: "Grounded",
      speed: "26.2 km/h",
      launchElevation: "-3.6°",
      azimuth: "+1.0°"
    },
    posePrediction: {
      primaryShot: "Front-foot drive",
      secondaryShot: "Forward defensive / push",
      footwork: "Front-foot",
      elevation: "Grounded",
      confidence: "80.0%",
      strideRatio: 0.15,
      frontKneeAngle: "140.4°",
      torsoLean: "19.6°",
      armExtension: 0.85,
      shotMatch: false,
      footworkMatch: true
    },
    targetEvaluation: {
      targetClassified: "Main Striker Batsman",
      boxArea: "535,900 px²",
      boxLocation: "At batting crease (x: 582-1109, y: 1904-2921)",
      confidence: "0.976",
      bowlerFiltered: "Bowler non-striker filtered",
      trackingStability: "100% across all 121 frames"
    },
    edgeDetection: {
      swingAzimuth: "+1.5°",
      ballExitAzimuth: "+1.0°",
      angularDiscrepancy: "0.5°",
      edgeStatus: "Middled Straight Push",
      edgeProbability: "1.2%",
      reasoning: "Ball exits straight back down the pitch (+1.0°). Low exit speed (26.2 km/h) confirms a firm push/block."
    },
    phases: {
      stance: "Frames 0 - 14",
      backswing: "Frame 15",
      stride: "Frames 15 - 45",
      execution: "Frames 46 - 52",
      impact: "Frames 53 - 55",
      followThrough: "Frames 56 - 120"
    },
    analyticalReason: "Checked follow-through and straight bat presentation. Distinguishable from a full drive by moderate exit speed and tight arm extension (0.85)."
  },
  "09": {
    id: "09",
    title: "Delivery 09: Lofted On-Drive",
    folder: "09_Theace1_2026-07-02_cam1_d10_cam2_d9",
    hitFrame: 50,
    groundTruth: {
      shot: "Lofted On-Drive",
      footwork: "Front-foot",
      elevation: "Lofted",
      speed: "46.0 km/h",
      launchElevation: "+37.3°",
      azimuth: "-5.8°"
    },
    posePrediction: {
      primaryShot: "Lofted On-Drive",
      secondaryShot: "Front-foot drive",
      footwork: "Front-foot",
      elevation: "Lofted",
      confidence: "90.0%",
      strideRatio: 0.74,
      frontKneeAngle: "177.3°",
      torsoLean: "13.0°",
      armExtension: 1.25,
      shotMatch: true,
      footworkMatch: true
    },
    targetEvaluation: {
      targetClassified: "Main Striker Batsman",
      boxArea: "623,800 px²",
      boxLocation: "At batting crease (x: 576-1187, y: 1273-2294)",
      confidence: "0.971",
      bowlerFiltered: "Bowler release filtered",
      trackingStability: "100% across all 121 frames"
    },
    edgeDetection: {
      swingAzimuth: "-5.7°",
      ballExitAzimuth: "-5.8°",
      angularDiscrepancy: "0.1°",
      edgeStatus: "Clean Middle (Lofted Six)",
      edgeProbability: "0.3%",
      reasoning: "High launch elevation (+37.3°) and speed (46.0 km/h) match pose upward follow-through (arm extension 1.25), confirming a clean lofted drive over the infield."
    },
    phases: {
      stance: "Frames 0 - 14",
      backswing: "Frame 15",
      stride: "Frames 15 - 41",
      execution: "Frames 42 - 48",
      impact: "Frames 49 - 51",
      followThrough: "Frames 52 - 120"
    },
    analyticalReason: "Distinct upward arm arc and spine backward extension at impact cleanly isolate this lofted shot from grounded drives."
  },
  "10": {
    id: "10",
    title: "Delivery 10: On-Drive / Flick",
    folder: "10_Theace2_2026-07-02_cam1_d2_cam2_d3",
    hitFrame: 52,
    groundTruth: {
      shot: "On-Drive / Flick",
      footwork: "Front-foot",
      elevation: "Grounded / Flat",
      speed: "32.4 km/h",
      launchElevation: "+1.2°",
      azimuth: "-16.6°"
    },
    posePrediction: {
      primaryShot: "On-Drive / Flick",
      secondaryShot: "Front-foot push",
      footwork: "Front-foot",
      elevation: "Grounded",
      confidence: "84.0%",
      strideRatio: 1.08,
      frontKneeAngle: "176.2°",
      torsoLean: "16.1°",
      armExtension: 0.98,
      shotMatch: true,
      footworkMatch: true
    },
    targetEvaluation: {
      targetClassified: "Main Striker Batsman",
      boxArea: "657,900 px²",
      boxLocation: "At batting crease (x: 547-1180, y: 1252-2291)",
      confidence: "0.970",
      bowlerFiltered: "Bowler release filtered",
      trackingStability: "100% across all 121 frames"
    },
    edgeDetection: {
      swingAzimuth: "-12.3°",
      ballExitAzimuth: "-16.6°",
      angularDiscrepancy: "4.3°",
      edgeStatus: "Middled Leg-Side Stroke",
      edgeProbability: "2.4%",
      reasoning: "Torso rotation and leg-side azimuth (-16.6°) confirm a wristy on-drive/flick through mid-wicket."
    },
    phases: {
      stance: "Frames 0 - 14",
      backswing: "Frame 15",
      stride: "Frames 15 - 43",
      execution: "Frames 44 - 50",
      impact: "Frames 51 - 53",
      followThrough: "Frames 54 - 120"
    },
    analyticalReason: "Torso rotation of 16.1° and wide stride (1.08) capture the batsman rotating wrists through mid-wicket."
  }
};

export default function PoseStudyTab() {
  const [selectedId, setSelectedId] = useState("01");
  const [activeSubTab, setActiveSubTab] = useState("video"); // 'video' | 'kinematics' | 'eval' | 'fusion'
  
  const current = DELIVERIES_DATA[selectedId];

  return (
    <div className="flex-1 flex flex-col h-full bg-[#0b0f19] text-slate-100 overflow-y-auto">
      {/* Top Banner Header */}
      <div className="bg-slate-900/90 border-b border-slate-800 p-5 px-8 flex flex-col md:flex-row md:items-center justify-between gap-4 backdrop-blur-md sticky top-0 z-20">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              YOLOv9 Pose v1.3 Evaluation
            </span>
            <span className="text-xs text-slate-400 font-mono">
              3d_hits_10_deliveries Benchmark
            </span>
          </div>
          <h1 className="text-xl md:text-2xl font-black tracking-tight text-white mt-1">
            Batter Pose & Shot Biomechanics Visualizer
          </h1>
        </div>

        {/* Global Summary Metrics */}
        <div className="flex items-center gap-3">
          <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl px-4 py-2">
            <div className="text-[11px] text-slate-400 uppercase tracking-wider font-bold">Batter Tracking</div>
            <div className="text-base font-mono font-bold text-emerald-400">100% (1,210 frames)</div>
          </div>
          <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl px-4 py-2">
            <div className="text-[11px] text-slate-400 uppercase tracking-wider font-bold">Footwork Acc</div>
            <div className="text-base font-mono font-bold text-emerald-400">90.0% (9/10)</div>
          </div>
          <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl px-4 py-2">
            <div className="text-[11px] text-slate-400 uppercase tracking-wider font-bold">Shot Acc (Pose Only)</div>
            <div className="text-base font-mono font-bold text-amber-400">60.0% (6/10)</div>
          </div>
        </div>
      </div>

      <div className="p-6 md:p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Delivery Selector Pills */}
        <div className="space-y-2">
          <label className="text-xs uppercase tracking-wider font-bold text-slate-400">
            Select Match Delivery (All 10 Real-World Deliveries):
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-5 lg:grid-cols-10 gap-2">
            {Object.keys(DELIVERIES_DATA).map((id) => {
              const item = DELIVERIES_DATA[id];
              const isSelected = id === selectedId;
              const isMatch = item.posePrediction.shotMatch;
              return (
                <button
                  key={id}
                  onClick={() => setSelectedId(id)}
                  className={`p-2.5 rounded-xl border text-center transition-all ${
                    isSelected
                      ? 'bg-emerald-600 text-white border-emerald-400 shadow-lg shadow-emerald-500/20 scale-[1.02]'
                      : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:bg-slate-800/70 hover:border-slate-700'
                  }`}
                >
                  <div className="text-xs font-mono font-bold">DEL #{id}</div>
                  <div className="text-[10px] truncate opacity-80 mt-0.5">
                    {item.groundTruth.speed}
                  </div>
                  <div className="mt-1 flex items-center justify-center">
                    {isMatch ? (
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                    ) : (
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Delivery Title & Badges */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono px-2 py-0.5 bg-slate-800 text-slate-300 rounded border border-slate-700">
                Hit Frame: #{current.hitFrame}
              </span>
              <span className="text-xs font-mono text-slate-400 truncate max-w-md">
                {current.folder}
              </span>
            </div>
            <h2 className="text-xl font-bold text-white mt-1">
              {current.title}
            </h2>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            <div className="px-3 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700">
              <span className="text-[11px] text-slate-400 block">Ground Truth:</span>
              <span className="text-sm font-semibold text-white">{current.groundTruth.shot}</span>
            </div>
            <div className="px-3 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700">
              <span className="text-[11px] text-slate-400 block">Pose Predicted:</span>
              <span className={`text-sm font-semibold ${current.posePrediction.shotMatch ? 'text-emerald-400' : 'text-amber-400'}`}>
                {current.posePrediction.primaryShot}
              </span>
            </div>
            <div className="px-3 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700">
              <span className="text-[11px] text-slate-400 block">Footwork:</span>
              <span className="text-sm font-semibold text-emerald-400">{current.posePrediction.footwork}</span>
            </div>
          </div>
        </div>

        {/* View Mode Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
          <button
            onClick={() => setActiveSubTab('video')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
              activeSubTab === 'video'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <Play className="w-3.5 h-3.5" />
            Annotated Broadcast Video
          </button>
          <button
            onClick={() => setActiveSubTab('kinematics')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
              activeSubTab === 'kinematics'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <BarChart2 className="w-3.5 h-3.5" />
            Kinematics Movement Graphs
          </button>
          <button
            onClick={() => setActiveSubTab('eval')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
              activeSubTab === 'eval'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <UserCheck className="w-3.5 h-3.5" />
            Batter vs Bowler Evaluation
          </button>
          <button
            onClick={() => setActiveSubTab('fusion')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
              activeSubTab === 'fusion'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <Zap className="w-3.5 h-3.5" />
            Cross-Signal Trajectory & Edge Detection
          </button>
        </div>

        {/* Content by Sub-Tab */}
        {activeSubTab === 'video' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Video Player */}
            <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl relative">
              <div className="aspect-[9/16] max-h-[640px] mx-auto bg-black flex items-center justify-center">
                <video
                  key={current.id}
                  src={`/assets/pose_study/annotated_shot_del${current.id}.mp4`}
                  controls
                  autoPlay
                  loop
                  muted
                  playsInline
                  className="w-full h-full object-contain"
                />
              </div>
              <div className="p-3 bg-slate-950/80 border-t border-slate-800/80 text-[11px] font-mono text-slate-400 flex items-center justify-between">
                <span>📹 Overlay: 17 Keypoint Skeleton + Class HUD + Phase Tracker</span>
                <span>Frame Rate: 30.0 fps (121 frames)</span>
              </div>
            </div>

            {/* Live Metrics & Calculations Sidebar */}
            <div className="lg:col-span-5 space-y-4">
              {/* Calculations Box */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 space-y-3">
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-emerald-400" />
                  Biomechanical Feature Calculations
                </h3>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/50">
                    <span className="text-slate-400 block text-[11px]">Base Stride Ratio:</span>
                    <span className="font-mono text-base font-bold text-white">{current.posePrediction.strideRatio}x</span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">Stance base: ~0.35x</span>
                  </div>
                  <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/50">
                    <span className="text-slate-400 block text-[11px]">Front Knee Flexion:</span>
                    <span className="font-mono text-base font-bold text-emerald-400">{current.posePrediction.frontKneeAngle}</span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">Deep bend &lt; 140°</span>
                  </div>
                  <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/50">
                    <span className="text-slate-400 block text-[11px]">Torso Inclination:</span>
                    <span className="font-mono text-base font-bold text-white">{current.posePrediction.torsoLean}</span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">Forward lean angle</span>
                  </div>
                  <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/50">
                    <span className="text-slate-400 block text-[11px]">Arm Extension Ratio:</span>
                    <span className="font-mono text-base font-bold text-emerald-400">{current.posePrediction.armExtension}x</span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">Wrist to shoulder</span>
                  </div>
                </div>

                {/* Analytical Reason */}
                <div className="p-3.5 bg-slate-800/40 rounded-xl border border-slate-700/40 text-xs text-slate-300 space-y-1">
                  <span className="font-bold text-slate-200 block flex items-center gap-1.5">
                    <Info className="w-3.5 h-3.5 text-sky-400" />
                    Classification Rationale:
                  </span>
                  <p className="leading-relaxed text-slate-300">
                    {current.analyticalReason}
                  </p>
                </div>
              </div>

              {/* Temporal Phase Breakdown */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 space-y-2.5">
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300">
                  Detected Temporal Shot Phases
                </h3>
                <div className="space-y-1.5 text-xs font-mono">
                  <div className="flex items-center justify-between p-2 rounded-lg bg-slate-800/40 border border-slate-800">
                    <span className="text-slate-400">1. Stance</span>
                    <span className="text-slate-300">{current.phases.stance}</span>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded-lg bg-slate-800/40 border border-slate-800">
                    <span className="text-amber-400">2. Backswing</span>
                    <span className="text-slate-300">{current.phases.backswing}</span>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded-lg bg-slate-800/40 border border-slate-800">
                    <span className="text-sky-400">3. Stride</span>
                    <span className="text-slate-300">{current.phases.stride}</span>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded-lg bg-slate-800/40 border border-slate-800">
                    <span className="text-orange-400">4. Execution</span>
                    <span className="text-slate-300">{current.phases.execution}</span>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded-lg bg-red-500/10 border border-red-500/30">
                    <span className="text-red-400 font-bold">5. Impact Window</span>
                    <span className="text-white font-bold">{current.phases.impact}</span>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded-lg bg-slate-800/40 border border-slate-800">
                    <span className="text-emerald-400">6. Follow-Through</span>
                    <span className="text-slate-300">{current.phases.followThrough}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeSubTab === 'kinematics' && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <BarChart2 className="w-5 h-5 text-emerald-400" />
                  Multi-Panel Kinematic Movement Analysis (121 Frames @ 30 FPS)
                </h3>
                <p className="text-xs text-slate-400">
                  Panel 1: Base Stride Ratio | Panel 2: Lead vs Trailing Knee Flexion | Panel 3: Shoulder & Torso Angles | Panel 4: Wrist Kinetic Speed
                </p>
              </div>
              <a
                href={`/assets/pose_study/kinematics_del${current.id}.png`}
                target="_blank"
                rel="noreferrer"
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-mono text-emerald-400 border border-slate-700 self-start"
              >
                Open Full Resolution
              </a>
            </div>

            <div className="rounded-xl overflow-hidden border border-slate-800 bg-slate-950 p-2">
              <img
                src={`/assets/pose_study/kinematics_del${current.id}.png`}
                alt={`Kinematics Delivery ${current.id}`}
                className="w-full h-auto object-contain rounded-lg"
              />
            </div>
          </div>
        )}

        {activeSubTab === 'eval' && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
            <div className="flex items-center gap-2.5">
              <UserCheck className="w-5 h-5 text-emerald-400" />
              <h3 className="text-base font-bold text-white">
                Detector Target Evaluation: Striker Batsman vs. Bowler
              </h3>
            </div>
            
            <p className="text-xs text-slate-300 leading-relaxed">
              To verify that the pose estimator reliably detects the <strong>main batsman playing the shot</strong> rather than the bowler or non-striker in the video, we evaluate spatial area, crease proximity, and temporal IoU tracking across all 121 frames:
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Tracked Batsman Card */}
              <div className="bg-emerald-950/20 border border-emerald-500/30 rounded-xl p-5 space-y-3">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  <span className="font-bold text-sm text-emerald-300">
                    Primary Target: Main Batsman (Striker)
                  </span>
                </div>
                <div className="space-y-1.5 text-xs text-slate-300 font-mono">
                  <div>• <strong>Bounding Box Area:</strong> {current.targetEvaluation.boxArea} (Foreground)</div>
                  <div>• <strong>Crease Proximity:</strong> {current.targetEvaluation.boxLocation}</div>
                  <div>• <strong>Detection Confidence:</strong> {current.targetEvaluation.confidence}</div>
                  <div>• <strong>Keypoints Active:</strong> 14 / 17 findable joints (helmet ears tracked)</div>
                  <div className="text-emerald-400 font-bold">• <strong>Tracking Result:</strong> {current.targetEvaluation.trackingStability}</div>
                </div>
              </div>

              {/* Filtered Non-Striker Card */}
              <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 space-y-3">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-amber-400" />
                  <span className="font-bold text-sm text-amber-300">
                    Background Player Filter (Bowler / Non-Striker)
                  </span>
                </div>
                <div className="space-y-1.5 text-xs text-slate-300 font-mono">
                  <div>• <strong>Bounding Box Area:</strong> ~87,000 px² (10x smaller in background)</div>
                  <div>• <strong>Location:</strong> Pitch opposite end (x &gt; 1500 px)</div>
                  <div>• <strong>Filter Criterion:</strong> Area &lt; 120,000 px² rejected</div>
                  <div>• <strong>False Identity Switch Rate:</strong> 0.0% (Zero leaks)</div>
                  <div className="text-slate-400">• {current.targetEvaluation.bowlerFiltered}</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeSubTab === 'fusion' && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
            <div className="flex items-center gap-2.5">
              <Zap className="w-5 h-5 text-amber-400" />
              <h3 className="text-base font-bold text-white">
                Kinematic-Pose Cross-Signal Fusion & Edge Detection
              </h3>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              When a batsman <strong>edges the ball</strong>, body pose reflects the intended shot (e.g. forward drive straight down the pitch), but the ball trajectory deflects sharply (e.g. +45° towards slips or gully). By computing the <strong>angular discrepancy</strong> between wrist swing presentation and ball launch azimuth, the engine reliably detects thick edges, glances, and deflections:
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-4">
                <span className="text-[11px] text-slate-400 uppercase font-bold block">Wrist Swing Azimuth</span>
                <span className="text-lg font-mono font-bold text-white">{current.edgeDetection.swingAzimuth}</span>
                <span className="text-[10px] text-slate-400 block mt-1">Bat presentation direction</span>
              </div>
              <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-4">
                <span className="text-[11px] text-slate-400 uppercase font-bold block">Ball Exit Azimuth</span>
                <span className="text-lg font-mono font-bold text-emerald-400">{current.edgeDetection.ballExitAzimuth}</span>
                <span className="text-[10px] text-slate-400 block mt-1">Stereo tracking launch azimuth</span>
              </div>
              <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-4">
                <span className="text-[11px] text-slate-400 uppercase font-bold block">Angular Discrepancy |Δφ|</span>
                <span className="text-lg font-mono font-bold text-sky-400">{current.edgeDetection.angularDiscrepancy}</span>
                <span className="text-[10px] text-slate-400 block mt-1">Edge threshold: &gt; 30.0°</span>
              </div>
            </div>

            {/* Edge Status Banner */}
            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 flex items-center justify-between">
              <div>
                <span className="text-xs text-slate-400 block">Classified Edge Status:</span>
                <span className="text-base font-bold text-emerald-400 font-mono">
                  {current.edgeDetection.edgeStatus}
                </span>
              </div>
              <div className="text-right">
                <span className="text-xs text-slate-400 block">Edge Probability:</span>
                <span className="text-base font-bold text-white font-mono">
                  {current.edgeDetection.edgeProbability}
                </span>
              </div>
            </div>

            <p className="text-xs text-slate-400 italic">
              Reasoning: {current.edgeDetection.reasoning}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
