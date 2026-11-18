import React, { useState } from 'react';
import { 
  Play, 
  Activity, 
  UserCheck, 
  Compass, 
  Zap, 
  BarChart2, 
  Info, 
  ChevronRight,
  TrendingUp,
  ShieldCheck,
  Target,
  Layers,
  Eye
} from 'lucide-react';

const DELIVERIES_DATA = {
  "01": {
    "id": "01",
    "title": "Delivery 01: Forward Defence",
    "folder": "01_Thebpca1_2026-08-19_cam1_d26_cam2_d27",
    "hitFrame": 61,
    "shotType": "Forward Defence",
    "alternativeShot": "Forward Defensive Push",
    "footwork": "Front-foot",
    "trajectoryCategory": "Grounded",
    "shotDirection": "Off side (In front of square)",
    "batterAzimuth": 5.2,
    "ballSpeed": 19.8,
    "ballElevation": -36.0,
    "sectorName": "Straight down the pitch (Long-off / Long-on)",
    "confidence": "88%",
    "strideRatio": 0.6,
    "leadDispPitch": 51.1,
    "torsoLean": "29.0\u00b0",
    "shoulderRot": "55.5\u00b0",
    "leadElbow": "22.7\u00b0",
    "supportingEvidence": "[Signal A: Trajectory] Ball exit azimuth +5.2\u00b0 (Straight down the pitch (Long-off / Long-on)), launch speed 19.8 km/h, elevation -36.0\u00b0 (Grounded). [Signal B: Pose] Front-foot posture (pitch stride +51.1 px, ratio 0.60), torso lean 29.0\u00b0, shoulder rotation 55.5\u00b0, lead elbow 22.7\u00b0. Textbook forward stride (+51.1 px) with checked wrists and soft exit speed (19.8 km/h).",
    "phasesStr": "Stance:0-19, Backswing:20-45, Stride:46-52, Exec:53-59, Impact:60-62, FT:63-120",
    "targetEvaluation": {
      "targetClassified": "Main Striker Batsman at Crease",
      "boxArea": "87,824 px\u00b2 (18m distance)",
      "boxLocation": "Batting Crease (x: 1754-2123 px, y: 1508-2013 px)",
      "confidence": "0.781",
      "bowlerFiltered": "Foreground Bowler Filtered (Area > 500,000 px\u00b2, x < 1200 px)",
      "trackingStability": "100% across all 121 frames"
    }
  },
  "02": {
    "id": "02",
    "title": "Delivery 02: Forward Defence",
    "folder": "02_Theace1_2026-08-26_cam1_d35_cam2_d36",
    "hitFrame": 50,
    "shotType": "Forward Defence",
    "alternativeShot": "Forward Defensive Push",
    "footwork": "Front-foot",
    "trajectoryCategory": "Grounded",
    "shotDirection": "Off side (In front of square)",
    "batterAzimuth": 23.9,
    "ballSpeed": 20.3,
    "ballElevation": -24.1,
    "sectorName": "Through mid-off",
    "confidence": "88%",
    "strideRatio": 0.47,
    "leadDispPitch": 93.5,
    "torsoLean": "30.2\u00b0",
    "shoulderRot": "160.7\u00b0",
    "leadElbow": "98.3\u00b0",
    "supportingEvidence": "[Signal A: Trajectory] Ball exit azimuth +23.9\u00b0 (Through mid-off), launch speed 20.3 km/h, elevation -24.1\u00b0 (Grounded). [Signal B: Pose] Front-foot posture (pitch stride +93.5 px, ratio 0.47), torso lean 30.2\u00b0, shoulder rotation 160.7\u00b0, lead elbow 98.3\u00b0. Textbook forward stride (+93.5 px) with checked wrists and soft exit speed (20.3 km/h).",
    "phasesStr": "Stance:0-17, Backswing:18-35, Stride:36-41, Exec:42-48, Impact:49-51, FT:52-120",
    "targetEvaluation": {
      "targetClassified": "Main Striker Batsman at Crease",
      "boxArea": "110,685 px\u00b2 (18m distance)",
      "boxLocation": "Batting Crease (x: 1426-1818 px, y: 2045-2618 px)",
      "confidence": "0.955",
      "bowlerFiltered": "Foreground Bowler Filtered (Area > 500,000 px\u00b2, x < 1200 px)",
      "trackingStability": "100% across all 121 frames"
    }
  },
  "03": {
    "id": "03",
    "title": "Delivery 03: Straight Drive",
    "folder": "03_Theace9_2026-07-02_cam1_d5_cam2_d6",
    "hitFrame": 47,
    "shotType": "Straight Drive",
    "alternativeShot": "On Drive",
    "footwork": "Neutral",
    "trajectoryCategory": "Grounded",
    "shotDirection": "Leg side (In front of square)",
    "batterAzimuth": -5.1,
    "ballSpeed": 52.7,
    "ballElevation": -0.9,
    "sectorName": "Straight down the pitch (Long-off / Long-on)",
    "confidence": "88%",
    "strideRatio": 0.32,
    "leadDispPitch": -5.8,
    "torsoLean": "24.0\u00b0",
    "shoulderRot": "26.7\u00b0",
    "leadElbow": "125.4\u00b0",
    "supportingEvidence": "[Signal A: Trajectory] Ball exit azimuth -5.1\u00b0 (Straight down the pitch (Long-off / Long-on)), launch speed 52.7 km/h, elevation -0.9\u00b0 (Grounded). [Signal B: Pose] Neutral posture (pitch stride -5.8 px, ratio 0.32), torso lean 24.0\u00b0, shoulder rotation 26.7\u00b0, lead elbow 125.4\u00b0. Bat swing aligned straight in the 'V' downfield (-5.1\u00b0 azimuth) past bowler.",
    "phasesStr": "Stance:0-14, Backswing:15-27, Stride:28-38, Exec:39-45, Impact:46-48, FT:49-120",
    "targetEvaluation": {
      "targetClassified": "Main Striker Batsman at Crease",
      "boxArea": "112,462 px\u00b2 (18m distance)",
      "boxLocation": "Batting Crease (x: 1567-1950 px, y: 1147-1731 px)",
      "confidence": "0.955",
      "bowlerFiltered": "Foreground Bowler Filtered (Area > 500,000 px\u00b2, x < 1200 px)",
      "trackingStability": "100% across all 121 frames"
    }
  },
  "04": {
    "id": "04",
    "title": "Delivery 04: Forward Defence",
    "folder": "04_Theace1_2026-08-17_cam1_d41_cam2_d40",
    "hitFrame": 55,
    "shotType": "Forward Defence",
    "alternativeShot": "Forward Defensive Push",
    "footwork": "Front-foot",
    "trajectoryCategory": "Grounded",
    "shotDirection": "Leg side (In front of square)",
    "batterAzimuth": -16.9,
    "ballSpeed": 18.0,
    "ballElevation": -58.5,
    "sectorName": "Through mid-on",
    "confidence": "88%",
    "strideRatio": 0.14,
    "leadDispPitch": 32.1,
    "torsoLean": "28.4\u00b0",
    "shoulderRot": "39.9\u00b0",
    "leadElbow": "113.4\u00b0",
    "supportingEvidence": "[Signal A: Trajectory] Ball exit azimuth -16.9\u00b0 (Through mid-on), launch speed 18.0 km/h, elevation -58.5\u00b0 (Grounded). [Signal B: Pose] Front-foot posture (pitch stride +32.1 px, ratio 0.14), torso lean 28.4\u00b0, shoulder rotation 39.9\u00b0, lead elbow 113.4\u00b0. Textbook forward stride (+32.1 px) with checked wrists and soft exit speed (18.0 km/h).",
    "phasesStr": "Stance:0-19, Backswing:20-32, Stride:33-46, Exec:47-53, Impact:54-56, FT:57-120",
    "targetEvaluation": {
      "targetClassified": "Main Striker Batsman at Crease",
      "boxArea": "77,861 px\u00b2 (18m distance)",
      "boxLocation": "Batting Crease (x: 1626-1912 px, y: 1863-2380 px)",
      "confidence": "0.948",
      "bowlerFiltered": "Foreground Bowler Filtered (Area > 500,000 px\u00b2, x < 1200 px)",
      "trackingStability": "100% across all 121 frames"
    }
  },
  "05": {
    "id": "05",
    "title": "Delivery 05: Straight Drive",
    "folder": "05_Thebpca1_2026-08-19_cam1_d31_cam2_d32",
    "hitFrame": 55,
    "shotType": "Straight Drive",
    "alternativeShot": "On Drive",
    "footwork": "Front-foot",
    "trajectoryCategory": "Grounded",
    "shotDirection": "Leg side (In front of square)",
    "batterAzimuth": -6.9,
    "ballSpeed": 34.4,
    "ballElevation": -5.4,
    "sectorName": "Straight down the pitch (Long-off / Long-on)",
    "confidence": "88%",
    "strideRatio": 0.79,
    "leadDispPitch": 95.3,
    "torsoLean": "37.4\u00b0",
    "shoulderRot": "2.0\u00b0",
    "leadElbow": "46.4\u00b0",
    "supportingEvidence": "[Signal A: Trajectory] Ball exit azimuth -6.9\u00b0 (Straight down the pitch (Long-off / Long-on)), launch speed 34.4 km/h, elevation -5.4\u00b0 (Grounded). [Signal B: Pose] Front-foot posture (pitch stride +95.3 px, ratio 0.79), torso lean 37.4\u00b0, shoulder rotation 2.0\u00b0, lead elbow 46.4\u00b0. Bat swing aligned straight in the 'V' downfield (-6.9\u00b0 azimuth) past bowler.",
    "phasesStr": "Stance:0-14, Backswing:15-43, Stride:44-48, Exec:49-53, Impact:54-56, FT:57-120",
    "targetEvaluation": {
      "targetClassified": "Main Striker Batsman at Crease",
      "boxArea": "83,268 px\u00b2 (18m distance)",
      "boxLocation": "Batting Crease (x: 1627-2134 px, y: 1508-2024 px)",
      "confidence": "0.800",
      "bowlerFiltered": "Foreground Bowler Filtered (Area > 500,000 px\u00b2, x < 1200 px)",
      "trackingStability": "100% across all 121 frames"
    }
  },
  "06": {
    "id": "06",
    "title": "Delivery 06: Forward Defence",
    "folder": "06_Thebpca1_2026-08-19_cam1_d23_cam2_d24",
    "hitFrame": 60,
    "shotType": "Forward Defence",
    "alternativeShot": "Forward Defensive Push",
    "footwork": "Front-foot",
    "trajectoryCategory": "Grounded",
    "shotDirection": "Off side (In front of square)",
    "batterAzimuth": 9.7,
    "ballSpeed": 21.1,
    "ballElevation": -9.5,
    "sectorName": "Straight down the pitch (Long-off / Long-on)",
    "confidence": "88%",
    "strideRatio": 0.15,
    "leadDispPitch": 42.9,
    "torsoLean": "30.1\u00b0",
    "shoulderRot": "29.0\u00b0",
    "leadElbow": "43.7\u00b0",
    "supportingEvidence": "[Signal A: Trajectory] Ball exit azimuth +9.7\u00b0 (Straight down the pitch (Long-off / Long-on)), launch speed 21.1 km/h, elevation -9.5\u00b0 (Grounded). [Signal B: Pose] Front-foot posture (pitch stride +42.9 px, ratio 0.15), torso lean 30.1\u00b0, shoulder rotation 29.0\u00b0, lead elbow 43.7\u00b0. Textbook forward stride (+42.9 px) with checked wrists and soft exit speed (21.1 km/h).",
    "phasesStr": "Stance:0-19, Backswing:20-38, Stride:39-51, Exec:52-58, Impact:59-61, FT:62-120",
    "targetEvaluation": {
      "targetClassified": "Main Striker Batsman at Crease",
      "boxArea": "79,812 px\u00b2 (18m distance)",
      "boxLocation": "Batting Crease (x: 1797-2159 px, y: 1513-2006 px)",
      "confidence": "0.906",
      "bowlerFiltered": "Foreground Bowler Filtered (Area > 500,000 px\u00b2, x < 1200 px)",
      "trackingStability": "100% across all 121 frames"
    }
  },
  "07": {
    "id": "07",
    "title": "Delivery 07: Off Drive",
    "folder": "07_Theace1_2026-08-17_cam1_d12_cam2_d9",
    "hitFrame": 56,
    "shotType": "Off Drive",
    "alternativeShot": "Cover Drive",
    "footwork": "Front-foot",
    "trajectoryCategory": "Grounded",
    "shotDirection": "Off side (In front of square)",
    "batterAzimuth": 17.1,
    "ballSpeed": 39.2,
    "ballElevation": -14.0,
    "sectorName": "Through mid-off",
    "confidence": "86%",
    "strideRatio": 0.36,
    "leadDispPitch": 83.4,
    "torsoLean": "24.4\u00b0",
    "shoulderRot": "23.8\u00b0",
    "leadElbow": "38.3\u00b0",
    "supportingEvidence": "[Signal A: Trajectory] Ball exit azimuth +17.1\u00b0 (Through mid-off), launch speed 39.2 km/h, elevation -14.0\u00b0 (Grounded). [Signal B: Pose] Front-foot posture (pitch stride +83.4 px, ratio 0.36), torso lean 24.4\u00b0, shoulder rotation 23.8\u00b0, lead elbow 38.3\u00b0. Off-side presentation directed through mid-off (+17.1\u00b0).",
    "phasesStr": "Stance:0-19, Backswing:20-26, Stride:27-47, Exec:48-54, Impact:55-57, FT:58-120",
    "targetEvaluation": {
      "targetClassified": "Main Striker Batsman at Crease",
      "boxArea": "97,115 px\u00b2 (18m distance)",
      "boxLocation": "Batting Crease (x: 1493-1872 px, y: 1850-2367 px)",
      "confidence": "0.956",
      "bowlerFiltered": "Foreground Bowler Filtered (Area > 500,000 px\u00b2, x < 1200 px)",
      "trackingStability": "100% across all 121 frames"
    }
  },
  "08": {
    "id": "08",
    "title": "Delivery 08: Straight Drive",
    "folder": "08_Theace1_2026-08-17_cam1_d84_cam2_d78",
    "hitFrame": 54,
    "shotType": "Straight Drive",
    "alternativeShot": "Off Drive",
    "footwork": "Neutral",
    "trajectoryCategory": "Grounded",
    "shotDirection": "Straight (In front of square)",
    "batterAzimuth": 1.0,
    "ballSpeed": 28.0,
    "ballElevation": -40.4,
    "sectorName": "Straight down the pitch (Long-off / Long-on)",
    "confidence": "88%",
    "strideRatio": 0.15,
    "leadDispPitch": 13.4,
    "torsoLean": "31.1\u00b0",
    "shoulderRot": "40.2\u00b0",
    "leadElbow": "1.7\u00b0",
    "supportingEvidence": "[Signal A: Trajectory] Ball exit azimuth +1.0\u00b0 (Straight down the pitch (Long-off / Long-on)), launch speed 28.0 km/h, elevation -40.4\u00b0 (Grounded). [Signal B: Pose] Neutral posture (pitch stride +13.4 px, ratio 0.15), torso lean 31.1\u00b0, shoulder rotation 40.2\u00b0, lead elbow 1.7\u00b0. Bat swing aligned straight in the 'V' downfield (+1.0\u00b0 azimuth) past bowler.",
    "phasesStr": "Stance:0-19, Backswing:20-29, Stride:30-45, Exec:46-52, Impact:53-55, FT:56-120",
    "targetEvaluation": {
      "targetClassified": "Main Striker Batsman at Crease",
      "boxArea": "82,454 px\u00b2 (18m distance)",
      "boxLocation": "Batting Crease (x: 1646-1954 px, y: 1879-2356 px)",
      "confidence": "0.937",
      "bowlerFiltered": "Foreground Bowler Filtered (Area > 500,000 px\u00b2, x < 1200 px)",
      "trackingStability": "100% across all 121 frames"
    }
  },
  "09": {
    "id": "09",
    "title": "Delivery 09: Lofted Straight Drive",
    "folder": "09_Theace1_2026-07-02_cam1_d10_cam2_d9",
    "hitFrame": 50,
    "shotType": "Lofted Straight Drive",
    "alternativeShot": "Lofted On-Drive",
    "footwork": "Front-foot",
    "trajectoryCategory": "Lofted",
    "shotDirection": "Leg side (In front of square)",
    "batterAzimuth": -5.6,
    "ballSpeed": 50.2,
    "ballElevation": 39.4,
    "sectorName": "Straight down the pitch (Long-off / Long-on)",
    "confidence": "92%",
    "strideRatio": 0.08,
    "leadDispPitch": 42.9,
    "torsoLean": "26.4\u00b0",
    "shoulderRot": "39.8\u00b0",
    "leadElbow": "108.6\u00b0",
    "supportingEvidence": "[Signal A: Trajectory] Ball exit azimuth -5.6\u00b0 (Straight down the pitch (Long-off / Long-on)), launch speed 50.2 km/h, elevation +39.4\u00b0 (Lofted). [Signal B: Pose] Front-foot posture (pitch stride +42.9 px, ratio 0.08), torso lean 26.4\u00b0, shoulder rotation 39.8\u00b0, lead elbow 108.6\u00b0. High launch elevation (+39.4\u00b0) and aerial follow-through extension (0.35).",
    "phasesStr": "Stance:0-19, Backswing:20-30, Stride:31-41, Exec:42-48, Impact:49-51, FT:52-120",
    "targetEvaluation": {
      "targetClassified": "Main Striker Batsman at Crease",
      "boxArea": "93,886 px\u00b2 (18m distance)",
      "boxLocation": "Batting Crease (x: 1655-1933 px, y: 1165-1770 px)",
      "confidence": "0.952",
      "bowlerFiltered": "Foreground Bowler Filtered (Area > 500,000 px\u00b2, x < 1200 px)",
      "trackingStability": "100% across all 121 frames"
    }
  },
  "10": {
    "id": "10",
    "title": "Delivery 10: On Drive",
    "folder": "10_Theace2_2026-07-02_cam1_d2_cam2_d3",
    "hitFrame": 52,
    "shotType": "On Drive",
    "alternativeShot": "Flick",
    "footwork": "Front-foot",
    "trajectoryCategory": "Grounded",
    "shotDirection": "Leg side (In front of square)",
    "batterAzimuth": -13.8,
    "ballSpeed": 30.8,
    "ballElevation": -25.3,
    "sectorName": "Through mid-on",
    "confidence": "87%",
    "strideRatio": 0.06,
    "leadDispPitch": 58.3,
    "torsoLean": "19.2\u00b0",
    "shoulderRot": "42.7\u00b0",
    "leadElbow": "115.6\u00b0",
    "supportingEvidence": "[Signal A: Trajectory] Ball exit azimuth -13.8\u00b0 (Through mid-on), launch speed 30.8 km/h, elevation -25.3\u00b0 (Grounded). [Signal B: Pose] Front-foot posture (pitch stride +58.3 px, ratio 0.06), torso lean 19.2\u00b0, shoulder rotation 42.7\u00b0, lead elbow 115.6\u00b0. Straight vertical presentation playing the ball through mid-on (-13.8\u00b0).",
    "phasesStr": "Stance:0-19, Backswing:20-25, Stride:26-43, Exec:44-50, Impact:51-53, FT:54-120",
    "targetEvaluation": {
      "targetClassified": "Main Striker Batsman at Crease",
      "boxArea": "86,793 px\u00b2 (18m distance)",
      "boxLocation": "Batting Crease (x: 1663-2018 px, y: 1198-1765 px)",
      "confidence": "0.950",
      "bowlerFiltered": "Foreground Bowler Filtered (Area > 500,000 px\u00b2, x < 1200 px)",
      "trackingStability": "100% across all 121 frames"
    }
  }
};

export default function PoseStudyTab() {
  const [selectedId, setSelectedId] = useState("01");
  const [activeSubTab, setActiveSubTab] = useState("video"); // 'video' | 'kinematics' | 'eval' | 'fusion'
  const [videoDims, setVideoDims] = useState({ width: 1080, height: 1920, isPortrait: true, aspectRatio: 9/16 });
  
  const current = DELIVERIES_DATA[selectedId];

  const handleVideoMetadata = (e) => {
    const { videoWidth, videoHeight } = e.target;
    if (videoWidth && videoHeight) {
      setVideoDims({
        width: videoWidth,
        height: videoHeight,
        isPortrait: videoHeight > videoWidth,
        aspectRatio: videoWidth / videoHeight,
      });
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 border border-slate-700/60 rounded-3xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-semibold tracking-wide uppercase">
              <Zap className="w-3.5 h-3.5" /> Multi-Signal Trajectory & Pose Fusion
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Cricket Shot Classifier: Ball Trajectory + Batter Pose
            </h1>
            <p className="text-sm text-slate-300 leading-relaxed">
              Fusing <strong>Signal A (Ball Launch Azimuth, Speed & Elevation)</strong> with <strong>Signal B (17-Keypoint Batter Biomechanics)</strong> to produce explainable cricket batting stroke classifications across 27+ stroke categories without relying on pose alone.
            </p>
          </div>

          {/* Overview Pill Badges */}
          <div className="flex flex-wrap sm:flex-nowrap gap-3 flex-shrink-0">
            <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-3.5 text-center min-w-[105px]">
              <span className="block text-xl font-black text-emerald-400">10 / 10</span>
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Classified</span>
            </div>
            <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-3.5 text-center min-w-[105px]">
              <span className="block text-xl font-black text-cyan-400">0.0%</span>
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Bowler Leaks</span>
            </div>
            <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-3.5 text-center min-w-[105px]">
              <span className="block text-xl font-black text-amber-400">Web H.264</span>
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">1080p Stream</span>
            </div>
          </div>
        </div>
      </div>

      {/* Delivery Selector Carousel */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-3 shadow-lg">
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-thin scrollbar-thumb-slate-700">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400 px-3 whitespace-nowrap flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-emerald-400" /> Deliveries:
          </span>
          {Object.values(DELIVERIES_DATA).map((d) => {
            const isSelected = d.id === selectedId;
            return (
              <button
                key={d.id}
                onClick={() => setSelectedId(d.id)}
                className={`px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all duration-200 flex items-center gap-2 ${
                  isSelected
                    ? 'bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20 font-bold scale-[1.02]'
                    : 'bg-slate-800/70 hover:bg-slate-700/70 text-slate-300 hover:text-white border border-slate-700/50'
                }`}
              >
                <span>Delivery {d.id}</span>
                <span className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-mono ${
                  isSelected ? 'bg-slate-950/20 text-slate-950' : 'bg-slate-900/60 text-slate-400'
                }`}>
                  {d.shotType.split(' ')[0]}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Analysis Grid */}
      <div className="space-y-6">
        {/* Delivery Title Bar with 4 Separated Outputs */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
            <div>
              <div className="text-xs font-mono text-emerald-400 uppercase tracking-widest flex items-center gap-2">
                <span>{current.folder}</span>
                <span>•</span>
                <span>Ball Impact: Frame {current.hitFrame}</span>
              </div>
              <h2 className="text-xl sm:text-2xl font-black text-white mt-1">
                {current.title}
              </h2>
            </div>
            
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-800/90 border border-slate-700 text-xs">
              <span className="text-slate-400">Alternative Hypothesis:</span>
              <span className="font-semibold text-cyan-300">{current.alternativeShot || 'None'}</span>
            </div>
          </div>

          {/* The 4 Separated Outputs */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5 pt-4">
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-3.5">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1 flex items-center gap-1.5">
                <Target className="w-3.5 h-3.5 text-emerald-400" /> Shot Type
              </span>
              <span className="text-base sm:text-lg font-black text-emerald-300 block">
                {current.shotType}
              </span>
              <span className="text-[10px] text-slate-400 font-mono mt-0.5 block">
                Confidence: {current.confidence}
              </span>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-3.5">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1 flex items-center gap-1.5">
                <TrendingUp className="w-3.5 h-3.5 text-cyan-400" /> Footwork
              </span>
              <span className="text-base sm:text-lg font-black text-white block">
                {current.footwork}
              </span>
              <span className="text-[10px] text-slate-400 font-mono mt-0.5 block">
                Pitch Stride: {current.leadDispPitch > 0 ? `+${current.leadDispPitch}` : current.leadDispPitch} px
              </span>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-3.5">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-amber-400" /> Trajectory Category
              </span>
              <span className={`text-base sm:text-lg font-black block ${
                current.trajectoryCategory === 'Lofted' ? 'text-amber-400' : 'text-slate-200'
              }`}>
                {current.trajectoryCategory}
              </span>
              <span className="text-[10px] text-slate-400 font-mono mt-0.5 block">
                Elevation: {current.ballElevation > 0 ? `+${current.ballElevation}` : current.ballElevation}°
              </span>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-3.5">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1 flex items-center gap-1.5">
                <Compass className="w-3.5 h-3.5 text-purple-400" /> Shot Direction
              </span>
              <span className="text-base sm:text-lg font-black text-purple-300 block">
                {current.shotDirection}
              </span>
              <span className="text-[10px] text-slate-400 font-mono mt-0.5 block truncate" title={current.sectorName}>
                Azimuth: {current.batterAzimuth > 0 ? `+${current.batterAzimuth}` : current.batterAzimuth}°
              </span>
            </div>
          </div>
        </div>

        {/* Sub-Navigation Tabs */}
        <div className="flex border-b border-slate-800 gap-2">
          <button
            onClick={() => setActiveSubTab('video')}
            className={`pb-3 px-4 text-xs font-bold uppercase tracking-wider transition-colors flex items-center gap-2 border-b-2 ${
              activeSubTab === 'video'
                ? 'border-emerald-400 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            <Play className="w-4 h-4" /> Native Aspect Video & HUD
          </button>
          <button
            onClick={() => setActiveSubTab('kinematics')}
            className={`pb-3 px-4 text-xs font-bold uppercase tracking-wider transition-colors flex items-center gap-2 border-b-2 ${
              activeSubTab === 'kinematics'
                ? 'border-emerald-400 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            <BarChart2 className="w-4 h-4" /> Movement Kinematics
          </button>
          <button
            onClick={() => setActiveSubTab('fusion')}
            className={`pb-3 px-4 text-xs font-bold uppercase tracking-wider transition-colors flex items-center gap-2 border-b-2 ${
              activeSubTab === 'fusion'
                ? 'border-emerald-400 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            <Compass className="w-4 h-4" /> Azimuth & Evidence Breakdown
          </button>
          <button
            onClick={() => setActiveSubTab('eval')}
            className={`pb-3 px-4 text-xs font-bold uppercase tracking-wider transition-colors flex items-center gap-2 border-b-2 ${
              activeSubTab === 'eval'
                ? 'border-emerald-400 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            <UserCheck className="w-4 h-4" /> Batsman vs. Bowler Target Separation
          </button>
        </div>

        {/* Sub-Tab 1: Video with Adaptive Native Aspect Ratio */}
        {activeSubTab === 'video' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Dynamic Adaptive Video Container */}
            <div className={`bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl relative flex flex-col items-center justify-center p-3 ${
              videoDims.isPortrait ? "lg:col-span-5" : "lg:col-span-7"
            }`}>
              <div 
                className="w-full flex items-center justify-center bg-black rounded-xl overflow-hidden shadow-inner"
                style={{ 
                  maxHeight: "680px", 
                  aspectRatio: videoDims.aspectRatio ? `${videoDims.aspectRatio}` : "9/16" 
                }}
              >
                <video
                  key={current.id}
                  controls
                  autoPlay
                  loop
                  muted
                  playsInline
                  preload="auto"
                  onLoadedMetadata={handleVideoMetadata}
                  className="w-full h-full object-contain"
                >
                  <source src={`/assets/pose_study/annotated_shot_del${current.id}.mp4`} type="video/mp4" />
                  Your browser does not support HTML5 video playback.
                </video>
              </div>

              <div className="w-full mt-2.5 px-3 py-2 bg-slate-950/80 rounded-lg text-[11px] font-mono text-slate-400 flex items-center justify-between">
                <span>📹 Native Aspect: {videoDims.isPortrait ? "Vertical (9:16)" : "Landscape (16:9)"} ({videoDims.width}x{videoDims.height})</span>
                <span className="text-emerald-400 font-semibold">Web H.264 (avc1)</span>
              </div>
            </div>

            {/* Sidebar Metrics & Biomechanical Details */}
            <div className={videoDims.isPortrait ? "lg:col-span-7 space-y-4" : "lg:col-span-5 space-y-4"}>
              {/* Biomechanical Feature Calculations */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 space-y-4">
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-emerald-400" />
                  Signal B: Measured Biomechanical Parameters
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                  <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/50">
                    <span className="text-slate-400 block text-[11px]">Forward Stride:</span>
                    <span className="font-mono text-base font-bold text-emerald-400">
                      {current.leadDispPitch > 0 ? `+${current.leadDispPitch}` : current.leadDispPitch} px
                    </span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">Ratio: {current.strideRatio}x torso</span>
                  </div>
                  <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/50">
                    <span className="text-slate-400 block text-[11px]">Torso Inclination:</span>
                    <span className="font-mono text-base font-bold text-white">{current.torsoLean}</span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">Forward spine lean</span>
                  </div>
                  <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/50">
                    <span className="text-slate-400 block text-[11px]">Shoulder Rotation:</span>
                    <span className="font-mono text-base font-bold text-cyan-400">{current.shoulderRot}</span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">Relative to stance</span>
                  </div>
                  <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/50">
                    <span className="text-slate-400 block text-[11px]">Lead Elbow Flexion:</span>
                    <span className="font-mono text-base font-bold text-amber-400">{current.leadElbow}</span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">High elbow in drives</span>
                  </div>
                  <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/50">
                    <span className="text-slate-400 block text-[11px]">Exit Ball Speed:</span>
                    <span className="font-mono text-base font-bold text-white">{current.ballSpeed} km/h</span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">Off bat face</span>
                  </div>
                  <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/50">
                    <span className="text-slate-400 block text-[11px]">Launch Elevation:</span>
                    <span className="font-mono text-base font-bold text-purple-400">
                      {current.ballElevation > 0 ? `+${current.ballElevation}` : current.ballElevation}°
                    </span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">{current.trajectoryCategory}</span>
                  </div>
                </div>
              </div>

              {/* Complete Technical Evidence Card */}
              <div className="bg-gradient-to-br from-slate-900 to-indigo-950/40 border border-slate-800 rounded-2xl p-5 space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Combined Classification Justification (Signal A + Signal B)
                </h3>
                <p className="text-xs text-slate-200 leading-relaxed font-sans bg-slate-950/60 p-3.5 rounded-xl border border-slate-800">
                  {current.supportingEvidence}
                </p>
              </div>

              {/* Temporal Phase Intervals */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Batting Movement Timeline
                </h3>
                <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/80 font-mono text-xs text-slate-300 space-y-1">
                  <div>• {current.phasesStr.split(', ')[0]}</div>
                  <div>• {current.phasesStr.split(', ')[1]}</div>
                  <div>• {current.phasesStr.split(', ')[2]}</div>
                  <div>• {current.phasesStr.split(', ')[3]}</div>
                  <div className="text-emerald-400 font-bold">• {current.phasesStr.split(', ')[4]}</div>
                  <div>• {current.phasesStr.split(', ')[5]}</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Sub-Tab 2: Movement Kinematics Graphs */}
        {activeSubTab === 'kinematics' && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <BarChart2 className="w-5 h-5 text-emerald-400" />
                Delivery {current.id}: 4-Panel Biomechanical Kinematics Time-Series
              </h3>
              <span className="text-xs font-mono text-slate-400">30 fps High-Speed Video Tracking (121 Frames)</span>
            </div>
            <p className="text-xs text-slate-300">
              The graph below depicts: <strong>(1) Stride Ratio</strong> over time, <strong>(2) Knee Flexion Angles</strong> (front vs back), <strong>(3) Shoulder & Torso Orientation</strong>, and <strong>(4) Kinetic Wrist Speed & Arm Extension</strong>, with color-shaded shot phase intervals.
            </p>
            <div className="bg-slate-950 rounded-xl p-2 border border-slate-800 overflow-hidden flex items-center justify-center">
              <img
                src={`/assets/pose_study/kinematics_del${current.id}.png`}
                alt={`Kinematics graph for delivery ${current.id}`}
                className="w-full max-h-[820px] object-contain rounded-lg shadow-lg"
              />
            </div>
          </div>
        )}

        {/* Sub-Tab 3: Azimuth & Evidence Breakdown */}
        {activeSubTab === 'fusion' && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
            <div className="flex items-center gap-2.5">
              <Compass className="w-5 h-5 text-purple-400" />
              <h3 className="text-base font-bold text-white">
                Signal A (Ball Trajectory Direction) vs. Signal B (Batter Pose Technique)
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Signal A: Directional Analysis */}
              <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 space-y-3">
                <span className="text-xs font-bold uppercase tracking-wider text-purple-300 block">
                  Signal A: Ball Trajectory Direction
                </span>
                <div className="space-y-2 text-xs font-mono text-slate-300">
                  <div>• <strong>Batter-Relative Azimuth:</strong> {current.batterAzimuth > 0 ? `+${current.batterAzimuth}` : current.batterAzimuth}°</div>
                  <div>• <strong>Fielding Sector:</strong> {current.sectorName}</div>
                  <div>• <strong>Side / Depth:</strong> {current.shotDirection}</div>
                  <div>• <strong>Off-Side vs Leg-Side:</strong> {current.batterAzimuth > 0 ? "Off-Side (> 0°)" : "Leg-Side (< 0°)"}</div>
                  <div>• <strong>Launch Speed:</strong> {current.ballSpeed} km/h</div>
                  <div>• <strong>Elevation Angle:</strong> {current.ballElevation > 0 ? `+${current.ballElevation}` : current.ballElevation}° ({current.trajectoryCategory})</div>
                </div>
              </div>

              {/* Signal B: Biomechanical Posture */}
              <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 space-y-3">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-300 block">
                  Signal B: Batter Pose & Technique
                </span>
                <div className="space-y-2 text-xs font-mono text-slate-300">
                  <div>• <strong>Technique Category:</strong> {current.footwork} Stride</div>
                  <div>• <strong>Forward Stride:</strong> {current.leadDispPitch > 0 ? `+${current.leadDispPitch}` : current.leadDispPitch} px towards bowler</div>
                  <div>• <strong>Stride-to-Torso Ratio:</strong> {current.strideRatio}x</div>
                  <div>• <strong>Torso Lean:</strong> {current.torsoLean} from vertical</div>
                  <div>• <strong>Relative Shoulder Rotation:</strong> {current.shoulderRot} from stance</div>
                  <div>• <strong>Lead Elbow:</strong> {current.leadElbow}</div>
                </div>
              </div>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 text-xs text-slate-300 space-y-2">
              <span className="font-bold text-emerald-400 block text-sm">Classification Decision Summary:</span>
              <p className="leading-relaxed">
                {current.supportingEvidence}
              </p>
            </div>
          </div>
        )}

        {/* Sub-Tab 4: Detector Target Separation (Batsman vs. Bowler) */}
        {activeSubTab === 'eval' && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
            <div className="flex items-center gap-2.5">
              <UserCheck className="w-5 h-5 text-emerald-400" />
              <h3 className="text-base font-bold text-white">
                Detector Target Separation: Striker Batsman vs. Foreground Bowler
              </h3>
            </div>
            
            <p className="text-xs text-slate-300 leading-relaxed">
              In broadcast cam2 (bowler-end perspective), the bowler walks in the immediate foreground while the striker batsman is 18 meters down the pitch. Our dual spatial filter ensures the detector locks onto the batsman and rejects the bowler across 100% of frames:
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Tracked Batsman Card */}
              <div className="bg-emerald-950/20 border border-emerald-500/30 rounded-xl p-5 space-y-3">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-emerald-400" />
                  <span className="font-bold text-sm text-emerald-300">
                    Primary Target: Main Batsman at Batting Crease
                  </span>
                </div>
                <div className="space-y-1.5 text-xs text-slate-300 font-mono">
                  <div>• <strong>Bounding Box Area:</strong> {current.targetEvaluation.boxArea}</div>
                  <div>• <strong>Crease Proximity:</strong> {current.targetEvaluation.boxLocation}</div>
                  <div>• <strong>Detection Confidence:</strong> {current.targetEvaluation.confidence}</div>
                  <div>• <strong>Keypoints Active:</strong> 15 / 17 joints tracked with high confidence</div>
                  <div className="text-emerald-400 font-bold">• <strong>Tracking Result:</strong> {current.targetEvaluation.trackingStability}</div>
                </div>
              </div>

              {/* Filtered Bowler Card */}
              <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 space-y-3">
                <div className="flex items-center gap-2">
                  <Eye className="w-5 h-5 text-amber-400" />
                  <span className="font-bold text-sm text-amber-300">
                    Foreground Bowler Rejection Filter
                  </span>
                </div>
                <div className="space-y-1.5 text-xs text-slate-300 font-mono">
                  <div>• <strong>Bowler Geometry:</strong> Walking in foreground (x &lt; 1200 px)</div>
                  <div>• <strong>Bowler Box Area:</strong> ~500,000 - 950,000 px² (10x larger than batsman)</div>
                  <div>• <strong>Rejection Filter:</strong> Area &gt; 280,000 px² or x &lt; 1200 px rejected</div>
                  <div>• <strong>Identity Switch Rate:</strong> 0.0% (Zero leaks to bowler)</div>
                  <div className="text-emerald-400 font-bold">• Verified: Batsman at crease tracked in 10/10 deliveries</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
