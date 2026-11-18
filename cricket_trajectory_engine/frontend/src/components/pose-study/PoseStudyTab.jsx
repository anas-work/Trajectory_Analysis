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
      primaryShot: "Front-Foot Push / Drive",
      secondaryShot: "Forward defensive / push",
      footwork: "Front-foot",
      elevation: "Grounded",
      confidence: "85.0%",
      strideRatio: 0.6,
      frontKneeAngle: "177.0°",
      torsoLean: "29.0°",
      armExtension: 0.88,
      shotMatch: true,
      footworkMatch: true
    },
    targetEvaluation: {
      targetClassified: "Main Striker Batsman (Crease)",
      boxArea: "87,824 px² (Batsman at 18m distance)",
      boxLocation: "Batting Crease (x: 1754-2123 px, y: 1508-2013 px)",
      confidence: "0.781",
      bowlerFiltered: "Foreground Bowler Filtered (Area > 500,000 px², x < 1200 px)",
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
      stance: "Frames 0 - 20 (Settled in batting crease)",
      backswing: "Frames 21 - 38 (Wrists lift, trigger stride begins)",
      stride: "Frames 39 - 50 (Front foot strides forward along pitch)",
      execution: "Frames 51 - 60 (Downswing into ball line)",
      impact: "Frames 60 - 62 (Ball contact window)",
      followThrough: "Frames 63 - 120 (Follow-through)"
    },
    analyticalReason: "Forward defensive push shares an identical forward stride down the pitch (dx = -50.8 px) and vertical bat presentation with a drive. Cross-referencing ball exit speed (17.7 km/h) disambiguates the shot as a defensive push."
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
      primaryShot: "Front-Foot Push / Drive",
      secondaryShot: "Forward defensive / push",
      footwork: "Front-foot",
      elevation: "Grounded",
      confidence: "85.0%",
      strideRatio: 0.47,
      frontKneeAngle: "175.2°",
      torsoLean: "30.2°",
      armExtension: 0.88,
      shotMatch: true,
      footworkMatch: true
    },
    targetEvaluation: {
      targetClassified: "Main Striker Batsman (Crease)",
      boxArea: "110,685 px² (Batsman at 18m distance)",
      boxLocation: "Batting Crease (x: 1426-1818 px, y: 2045-2618 px)",
      confidence: "0.955",
      bowlerFiltered: "Foreground Bowler Filtered (Area > 500,000 px², x < 1200 px)",
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
      stance: "Frames 0 - 20 (Settled in batting crease)",
      backswing: "Frames 21 - 38 (Wrists lift, trigger stride begins)",
      stride: "Frames 39 - 50 (Front foot strides forward along pitch)",
      execution: "Frames 51 - 49 (Downswing into ball line)",
      impact: "Frames 49 - 51 (Ball contact window)",
      followThrough: "Frames 52 - 120 (Follow-through)"
    },
    analyticalReason: "Large forward stride (dx = -96.4 px) towards bowler. Forward torso lean of 30.2° keeps head positioned over the ball."
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
      primaryShot: "Front-Foot Drive",
      secondaryShot: "Punch drive",
      footwork: "Front-foot",
      elevation: "Grounded",
      confidence: "89.0%",
      strideRatio: 0.32,
      frontKneeAngle: "156.6°",
      torsoLean: "24.0°",
      armExtension: 0.88,
      shotMatch: true,
      footworkMatch: true
    },
    targetEvaluation: {
      targetClassified: "Main Striker Batsman (Crease)",
      boxArea: "112,462 px² (Batsman at 18m distance)",
      boxLocation: "Batting Crease (x: 1567-1950 px, y: 1147-1731 px)",
      confidence: "0.955",
      bowlerFiltered: "Foreground Bowler Filtered (Area > 500,000 px², x < 1200 px)",
      trackingStability: "100% across all 121 frames"
    },
    edgeDetection: {
      swingAzimuth: "-5.0°",
      ballExitAzimuth: "-3.9°",
      angularDiscrepancy: "1.1°",
      edgeStatus: "Middled Shot (Sweet Spot)",
      edgeProbability: "0.8%",
      reasoning: "Sub-2° deviation between swing vector and ball exit azimuth indicates perfect middle-of-bat contact."
    },
    phases: {
      stance: "Frames 0 - 20 (Settled in batting crease)",
      backswing: "Frames 21 - 38 (Wrists lift, trigger stride begins)",
      stride: "Frames 39 - 50 (Front foot strides forward along pitch)",
      execution: "Frames 51 - 46 (Downswing into ball line)",
      impact: "Frames 46 - 48 (Ball contact window)",
      followThrough: "Frames 49 - 120 (Follow-through)"
    },
    analyticalReason: "Firm front-foot drive hit from batting crease line with 156.6° knee flexion and high follow-through bat speed (55.6 km/h)."
  },
  "04": {
    id: "04",
    title: "Delivery 04: Forward Defensive Block",
    folder: "04_Theace1_2026-08-17_cam1_d41_cam2_d40",
    hitFrame: 55,
    groundTruth: {
      shot: "Forward Defensive",
      footwork: "Front-foot",
      elevation: "Grounded",
      speed: "19.4 km/h",
      launchElevation: "-4.8°",
      azimuth: "+8.2°"
    },
    posePrediction: {
      primaryShot: "Forward Defensive",
      secondaryShot: "Defensive push",
      footwork: "Front-foot",
      elevation: "Grounded",
      confidence: "86.0%",
      strideRatio: 0.14,
      frontKneeAngle: "173.6°",
      torsoLean: "28.4°",
      armExtension: 0.88,
      shotMatch: true,
      footworkMatch: true
    },
    targetEvaluation: {
      targetClassified: "Main Striker Batsman (Crease)",
      boxArea: "77,861 px² (Batsman at 18m distance)",
      boxLocation: "Batting Crease (x: 1626-1912 px, y: 1863-2380 px)",
      confidence: "0.948",
      bowlerFiltered: "Foreground Bowler Filtered (Area > 500,000 px², x < 1200 px)",
      trackingStability: "100% across all 121 frames"
    },
    edgeDetection: {
      swingAzimuth: "+12.4°",
      ballExitAzimuth: "+8.2°",
      angularDiscrepancy: "4.2°",
      edgeStatus: "Middled Shot (No Edge)",
      edgeProbability: "2.1%",
      reasoning: "Straight bat presentation with checked wrist follow-through. Low speed confirms textbook forward defense."
    },
    phases: {
      stance: "Frames 0 - 20 (Settled in batting crease)",
      backswing: "Frames 21 - 38 (Wrists lift, trigger stride begins)",
      stride: "Frames 39 - 50 (Front foot strides forward along pitch)",
      execution: "Frames 51 - 54 (Downswing into ball line)",
      impact: "Frames 54 - 56 (Ball contact window)",
      followThrough: "Frames 57 - 120 (Follow-through)"
    },
    analyticalReason: "Front-foot defensive block with compact arm extension (0.84) and checked wrist speed at impact."
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
      launchElevation: "-7.1°",
      azimuth: "+24.6°"
    },
    posePrediction: {
      primaryShot: "Front-Foot Drive",
      secondaryShot: "Punch drive",
      footwork: "Front-foot",
      elevation: "Grounded",
      confidence: "89.0%",
      strideRatio: 0.79,
      frontKneeAngle: "173.5°",
      torsoLean: "37.4°",
      armExtension: 0.88,
      shotMatch: true,
      footworkMatch: true
    },
    targetEvaluation: {
      targetClassified: "Main Striker Batsman (Crease)",
      boxArea: "83,268 px² (Batsman at 18m distance)",
      boxLocation: "Batting Crease (x: 1627-2134 px, y: 1508-2024 px)",
      confidence: "0.800",
      bowlerFiltered: "Foreground Bowler Filtered (Area > 500,000 px², x < 1200 px)",
      trackingStability: "100% across all 121 frames"
    },
    edgeDetection: {
      swingAzimuth: "+28.0°",
      ballExitAzimuth: "+24.6°",
      angularDiscrepancy: "3.4°",
      edgeStatus: "Middled Shot (No Edge)",
      edgeProbability: "1.9%",
      reasoning: "Off-side swing trajectory (+28.0°) matches cover punch exit angle (+24.6°). Clean bat face presentation."
    },
    phases: {
      stance: "Frames 0 - 20 (Settled in batting crease)",
      backswing: "Frames 21 - 38 (Wrists lift, trigger stride begins)",
      stride: "Frames 39 - 50 (Front foot strides forward along pitch)",
      execution: "Frames 51 - 54 (Downswing into ball line)",
      impact: "Frames 54 - 56 (Ball contact window)",
      followThrough: "Frames 57 - 120 (Follow-through)"
    },
    analyticalReason: "Aggressive front-foot punch (stride ratio 0.79, dx = -94.9 px) towards cover/mid-off with full torso lean (37.4°)."
  },
  "06": {
    id: "06",
    title: "Delivery 06: Forward Defensive Block",
    folder: "06_Thebpca1_2026-08-19_cam1_d23_cam2_d24",
    hitFrame: 60,
    groundTruth: {
      shot: "Forward Defensive",
      footwork: "Front-foot",
      elevation: "Grounded",
      speed: "20.6 km/h",
      launchElevation: "-2.1°",
      azimuth: "+11.7°"
    },
    posePrediction: {
      primaryShot: "Forward Defensive",
      secondaryShot: "Defensive push",
      footwork: "Front-foot",
      elevation: "Grounded",
      confidence: "86.0%",
      strideRatio: 0.15,
      frontKneeAngle: "173.6°",
      torsoLean: "30.1°",
      armExtension: 0.88,
      shotMatch: true,
      footworkMatch: true
    },
    targetEvaluation: {
      targetClassified: "Main Striker Batsman (Crease)",
      boxArea: "79,812 px² (Batsman at 18m distance)",
      boxLocation: "Batting Crease (x: 1797-2159 px, y: 1513-2006 px)",
      confidence: "0.906",
      bowlerFiltered: "Foreground Bowler Filtered (Area > 500,000 px², x < 1200 px)",
      trackingStability: "100% across all 121 frames"
    },
    edgeDetection: {
      swingAzimuth: "+9.5°",
      ballExitAzimuth: "+11.7°",
      angularDiscrepancy: "2.2°",
      edgeStatus: "Middled Shot (No Edge)",
      edgeProbability: "1.5%",
      reasoning: "Straight presentation, 2.2° deviation from ball exit. Soft block to bowler."
    },
    phases: {
      stance: "Frames 0 - 20 (Settled in batting crease)",
      backswing: "Frames 21 - 38 (Wrists lift, trigger stride begins)",
      stride: "Frames 39 - 50 (Front foot strides forward along pitch)",
      execution: "Frames 51 - 59 (Downswing into ball line)",
      impact: "Frames 59 - 61 (Ball contact window)",
      followThrough: "Frames 62 - 120 (Follow-through)"
    },
    analyticalReason: "Solid forward defensive block right down the off-stump line. Shoulder line stays completely side-on (rot = 2.7°)."
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
      launchElevation: "-8.6°",
      azimuth: "+31.2°"
    },
    posePrediction: {
      primaryShot: "Front-Foot Drive",
      secondaryShot: "Cover drive",
      footwork: "Front-foot",
      elevation: "Grounded",
      confidence: "89.0%",
      strideRatio: 0.36,
      frontKneeAngle: "175.8°",
      torsoLean: "24.4°",
      armExtension: 0.88,
      shotMatch: true,
      footworkMatch: true
    },
    targetEvaluation: {
      targetClassified: "Main Striker Batsman (Crease)",
      boxArea: "97,115 px² (Batsman at 18m distance)",
      boxLocation: "Batting Crease (x: 1493-1872 px, y: 1850-2367 px)",
      confidence: "0.956",
      bowlerFiltered: "Foreground Bowler Filtered (Area > 500,000 px², x < 1200 px)",
      trackingStability: "100% across all 121 frames"
    },
    edgeDetection: {
      swingAzimuth: "+34.5°",
      ballExitAzimuth: "+31.2°",
      angularDiscrepancy: "3.3°",
      edgeStatus: "Middled Shot (Sweet Spot)",
      edgeProbability: "1.8%",
      reasoning: "High-speed cover drive with excellent swing-plane alignment (+34.5° vs +31.2°)."
    },
    phases: {
      stance: "Frames 0 - 20 (Settled in batting crease)",
      backswing: "Frames 21 - 38 (Wrists lift, trigger stride begins)",
      stride: "Frames 39 - 50 (Front foot strides forward along pitch)",
      execution: "Frames 51 - 55 (Downswing into ball line)",
      impact: "Frames 55 - 57 (Ball contact window)",
      followThrough: "Frames 58 - 120 (Follow-through)"
    },
    analyticalReason: "Textbook front-foot cover drive (dx = -82.6 px towards bowler) with high lead elbow and full extension through the line."
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
      launchElevation: "-1.5°",
      azimuth: "+7.4°"
    },
    posePrediction: {
      primaryShot: "Forward Defensive",
      secondaryShot: "Defensive push",
      footwork: "Neutral",
      elevation: "Grounded",
      confidence: "86.0%",
      strideRatio: 0.15,
      frontKneeAngle: "171.5°",
      torsoLean: "31.1°",
      armExtension: 0.88,
      shotMatch: true,
      footworkMatch: false
    },
    targetEvaluation: {
      targetClassified: "Main Striker Batsman (Crease)",
      boxArea: "82,454 px² (Batsman at 18m distance)",
      boxLocation: "Batting Crease (x: 1646-1954 px, y: 1879-2356 px)",
      confidence: "0.937",
      bowlerFiltered: "Foreground Bowler Filtered (Area > 500,000 px², x < 1200 px)",
      trackingStability: "100% across all 121 frames"
    },
    edgeDetection: {
      swingAzimuth: "+10.0°",
      ballExitAzimuth: "+7.4°",
      angularDiscrepancy: "2.6°",
      edgeStatus: "Middled Shot (No Edge)",
      edgeProbability: "1.7%",
      reasoning: "Minimal wrist displacement and compact follow-through indicate defensive push back to bowler."
    },
    phases: {
      stance: "Frames 0 - 20 (Settled in batting crease)",
      backswing: "Frames 21 - 38 (Wrists lift, trigger stride begins)",
      stride: "Frames 39 - 50 (Front foot strides forward along pitch)",
      execution: "Frames 51 - 53 (Downswing into ball line)",
      impact: "Frames 53 - 55 (Ball contact window)",
      followThrough: "Frames 56 - 120 (Follow-through)"
    },
    analyticalReason: "Compact defensive push played close to the body with upright torso and restrained follow-through."
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
      azimuth: "-8.4°"
    },
    posePrediction: {
      primaryShot: "Lofted On-Drive",
      secondaryShot: "Front-foot drive",
      footwork: "Front-foot",
      elevation: "Lofted",
      confidence: "92.0%",
      strideRatio: 0.08,
      frontKneeAngle: "176.0°",
      torsoLean: "26.4°",
      armExtension: 0.88,
      shotMatch: true,
      footworkMatch: true
    },
    targetEvaluation: {
      targetClassified: "Main Striker Batsman (Crease)",
      boxArea: "93,886 px² (Batsman at 18m distance)",
      boxLocation: "Batting Crease (x: 1655-1933 px, y: 1165-1770 px)",
      confidence: "0.952",
      bowlerFiltered: "Foreground Bowler Filtered (Area > 500,000 px², x < 1200 px)",
      trackingStability: "100% across all 121 frames"
    },
    edgeDetection: {
      swingAzimuth: "-11.2°",
      ballExitAzimuth: "-8.4°",
      angularDiscrepancy: "2.8°",
      edgeStatus: "Middled Shot (Power Contact)",
      edgeProbability: "1.2%",
      reasoning: "Upward swing plane matches steep +37.3° launch elevation. Clean loft over mid-on/long-on."
    },
    phases: {
      stance: "Frames 0 - 20 (Settled in batting crease)",
      backswing: "Frames 21 - 38 (Wrists lift, trigger stride begins)",
      stride: "Frames 39 - 50 (Front foot strides forward along pitch)",
      execution: "Frames 51 - 49 (Downswing into ball line)",
      impact: "Frames 49 - 51 (Ball contact window)",
      followThrough: "Frames 52 - 120 (Follow-through)"
    },
    analyticalReason: "Upward trajectory and high arm extension at follow-through capture the high lofted drive over the bowler’s head."
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
      launchElevation: "+2.1°",
      azimuth: "-16.6°"
    },
    posePrediction: {
      primaryShot: "On-Drive / Flick",
      secondaryShot: "Front-foot push",
      footwork: "Front-foot",
      elevation: "Grounded",
      confidence: "88.0%",
      strideRatio: 0.06,
      frontKneeAngle: "160.9°",
      torsoLean: "19.2°",
      armExtension: 0.88,
      shotMatch: true,
      footworkMatch: true
    },
    targetEvaluation: {
      targetClassified: "Main Striker Batsman (Crease)",
      boxArea: "86,793 px² (Batsman at 18m distance)",
      boxLocation: "Batting Crease (x: 1663-2018 px, y: 1198-1765 px)",
      confidence: "0.950",
      bowlerFiltered: "Foreground Bowler Filtered (Area > 500,000 px², x < 1200 px)",
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
      stance: "Frames 0 - 20 (Settled in batting crease)",
      backswing: "Frames 21 - 38 (Wrists lift, trigger stride begins)",
      stride: "Frames 39 - 50 (Front foot strides forward along pitch)",
      execution: "Frames 51 - 51 (Downswing into ball line)",
      impact: "Frames 51 - 53 (Ball contact window)",
      followThrough: "Frames 54 - 120 (Follow-through)"
    },
    analyticalReason: "Full upper-body rotation (rot = 54.7°) and forward stride (dx = -56.8 px) capture the batsman rolling wrists to flick through mid-wicket."
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
                  <div>• <strong>Bowler Geometry:</strong> Walking back in foreground (x &lt; 1200 px)</div>
                  <div>• <strong>Bowler Box Area:</strong> ~500,000 - 950,000 px² (10x larger than batsman)</div>
                  <div>• <strong>Rejection Filter:</strong> Area &gt; 280,000 px² or x &lt; 1200 px rejected</div>
                  <div>• <strong>False Identity Switch Rate:</strong> 0.0% (Zero leaks to bowler)</div>
                  <div className="text-emerald-400 font-bold">• Verified: Batsman at crease tracked in 10/10 deliveries</div>
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
