# 39 more deliveries with 3D after the bat hit

Companion to `/h3/Harshit/3d_hits_10_deliveries` (same files, columns and methods; see its README). **None of these 39 is in that folder.**

Each delivery folder has, for both phones (cam1, cam2): `clip_cam1.mp4`, `clip_cam2.mp4` (QA delivery clip, unedited), `3d_frame_by_frame_cam*.csv`,
`3d_pre/post/bat_cam*.csv`, `depth_graph.png`, `bat_hit_speed_fit_y.csv`. `summary.csv` has the numbers below, bounce / hit frames, clip status;
`clips_status.csv` the clip download result per phone.

## How these 39 were picked (looser than the 10)
The 10 used: >= 20 after-bat 3D frames, after-bat depth line R² >= 0.99, path >= 4 m, no gap > 7 frames, <= 13 missing. Only 3 more deliveries pass
that, so these use: **>= 8 after-bat 3D frames, R² >= 0.95, path >= 2 m**, no gap rule. Ranked by how straight the after-bat depth is (RMS).
The lower ranks are much rougher than the 10 (fewer after-bat frames, RMS up to ~74 cm).

Sources (`source` column):
- `pool` (24): the 14 stereo sessions of the original review, minus the 10.
- `new39` (15): 39 more triangulated stereo sessions, run through the same post-hit steps on 19 Nov (`/h3/Harshit/stereo_posthit_review/new39/`):
  chained detections after the tracker ends (raw detections copied read-only from aimdev), v5 bounce / bat hit, the pipeline's triangulation with
  the after-hit points as one segment. For 4 older runs without a per-delivery sync offset, it was computed with the stereo pipeline's own
  `own_offset` (ray sweep) into a shadow copy; the stored runs were not changed.
Both phones' bat hits agree within 2 frames in every delivery, as in the 10.

| # | Delivery | Source | 3D frames pre / post / bat | Chained after hit | Depth line RMS | R² | Path along Y | Bat-hit fit-y speed |
|---|---|---|---|---|---|---|---|---|
| 1 | Theace6_2026-07-06_cam1_d1_cam2_d1 | new39 | 24 / 15 / 9 | 0 | 0.6 cm | 0.9999 | 2.2 m | 30.5 km/h |
| 2 | Thebpca1_2026-08-19_cam1_d36_cam2_d36 | pool | 23 / 0 / 8 | 0 | 2.3 cm | 0.9993 | 2.6 m | 41.0 km/h |
| 3 | Theace1_2026-08-17_cam1_d4_cam2_d3 | pool | 17 / 4 / 8 | 8 | 2.4 cm | 0.9993 | 2.5 m | 24.8 km/h |
| 4 | Thebcs7_2026-07-06_cam1_d1_cam2_d1 | new39 | 14 / 0 / 12 | 0 | 2.7 cm | 0.9998 | 7.5 m | 56.9 km/h |
| 5 | Theace1_2026-08-17_cam1_d60_cam2_d56 | pool | 28 / 0 / 15 | 15 | 3.0 cm | 0.9995 | 4.5 m | 34.1 km/h |
| 6 | Theace1_2026-08-26_cam1_d184_cam2_d182 | pool | 22 / 0 / 11 | 0 | 3.4 cm | 0.9999 | 10.4 m | 112.1 km/h |
| 7 | Theace7_2026-07-02_cam1_d9_cam2_d10 | pool | 20 / 0 / 18 | 17 | 4.5 cm | 0.9991 | 5.1 m | 29.6 km/h |
| 8 | Thebpca2_2026-07-07_cam1_d10_cam2_d10 | new39 | 23 / 0 / 10 | 0 | 5.3 cm | 0.9981 | 3.9 m | 44.5 km/h |
| 9 | Thesls1_2026-08-21_cam1_d23_cam2_d26 | pool | 21 / 0 / 12 | 0 | 5.3 cm | 0.9992 | 6.2 m | 60.3 km/h |
| 10 | Theace2_2026-07-02_cam1_d4_cam2_d5 | pool | 24 / 0 / 10 | 0 | 5.3 cm | 0.9988 | 4.7 m | 58.8 km/h |
| 11 | Theace1_2026-08-26_cam1_d20_cam2_d21 | pool | 24 / 0 / 9 | 0 | 5.5 cm | 0.9993 | 6.1 m | 83.4 km/h |
| 12 | Thesls1_2026-08-21_cam1_d33_cam2_d35 | pool | 17 / 0 / 14 | 0 | 5.7 cm | 0.9973 | 3.7 m | 29.1 km/h |
| 13 | Theace1_2026-08-26_cam1_d103_cam2_d104 | pool | 12 / 0 / 10 | 10 | 5.9 cm | 0.9960 | 2.9 m | 35.1 km/h |
| 14 | Theace2_2026-08-24_cam1_d14_cam2_d12 | new39 | 22 / 0 / 19 | 0 | 6.2 cm | 0.9948 | 2.7 m | 17.0 km/h |
| 15 | Thebpca5_2026-07-07_cam1_d5_cam2_d4 | new39 | 27 / 5 / 18 | 18 | 6.4 cm | 0.9989 | 6.4 m | 32.4 km/h |
| 16 | Theace1_2026-08-17_cam1_d115_cam2_d109 | pool | 20 / 0 / 13 | 0 | 6.5 cm | 0.9939 | 2.5 m | 24.7 km/h |
| 17 | Thebcs2_2026-07-06_cam1_d3_cam2_d2 | new39 | 19 / 0 / 31 | 22 | 7.8 cm | 0.9979 | 5.5 m | 19.7 km/h |
| 18 | Theace1_2026-08-26_cam1_d80_cam2_d81 | pool | 11 / 4 / 14 | 0 | 8.6 cm | 0.9922 | 3.2 m | 26.3 km/h |
| 19 | Theace5_2026-07-02_cam1_d11_cam2_d10 | new39 | 11 / 0 / 16 | 0 | 9.0 cm | 0.9910 | 2.9 m | 23.5 km/h |
| 20 | new_Thebcs4_2026-10-27_cam1_d19_cam2_d9 | new39 | 5 / 0 / 11 | 0 | 9.4 cm | 0.9934 | 3.5 m | 41.6 km/h |
| 21 | Theace1_2026-08-26_cam1_d181_cam2_d179 | pool | 20 / 0 / 21 | 21 | 9.8 cm | 0.9985 | 8.2 m | 45.0 km/h |
| 22 | Theace1_2026-08-26_cam1_d85_cam2_d86 | pool | 16 / 10 / 10 | 0 | 10.0 cm | 0.9966 | 5.6 m | 64.2 km/h |
| 23 | Theace1_2026-08-26_cam1_d183_cam2_d181 | pool | 21 / 0 / 17 | 0 | 10.2 cm | 0.9990 | 10.7 m | 71.8 km/h |
| 24 | Theace1_2026-08-26_cam1_d99_cam2_d100 | pool | 12 / 0 / 12 | 0 | 10.2 cm | 0.9989 | 10.0 m | 93.9 km/h |
| 25 | Thesls1_2026-08-21_cam1_d41_cam2_d43 | pool | 18 / 0 / 8 | 0 | 12.8 cm | 0.9884 | 3.8 m | 56.0 km/h |
| 26 | Thesls1_2026-08-21_cam1_d8_cam2_d9 | pool | 16 / 5 / 16 | 0 | 12.9 cm | 0.9894 | 4.1 m | 29.2 km/h |
| 27 | Theace1_2026-08-26_cam1_d208_cam2_d205 | pool | 11 / 8 / 14 | 0 | 13.2 cm | 0.9973 | 8.0 m | 53.7 km/h |
| 28 | Theace2_2026-08-24_cam1_d8_cam2_d6 | new39 | 14 / 8 / 17 | 1 | 13.6 cm | 0.9711 | 2.8 m | 15.0 km/h |
| 29 | Theace1_2026-08-26_cam1_d164_cam2_d160 | pool | 21 / 0 / 14 | 1 | 13.7 cm | 0.9735 | 2.7 m | 22.2 km/h |
| 30 | Thebpca2_2026-07-07_cam1_d8_cam2_d9 | new39 | 10 / 5 / 20 | 0 | 16.5 cm | 0.9850 | 4.6 m | 22.2 km/h |
| 31 | Thesls1_2026-08-21_cam1_d97_cam2_d97 | pool | 12 / 1 / 9 | 0 | 16.6 cm | 0.9884 | 5.0 m | 64.1 km/h |
| 32 | Theace3_2026-07-02_cam1_d3_cam2_d3 | pool | 14 / 0 / 39 | 39 | 16.8 cm | 0.9982 | 12.1 m | 25.0 km/h |
| 33 | Thebpca2_2026-07-07_cam1_d6_cam2_d7 | new39 | 6 / 8 / 12 | 0 | 17.1 cm | 0.9948 | 7.4 m | 61.9 km/h |
| 34 | Thebcs6_2026-07-06_cam1_d5_cam2_d7 | new39 | 23 / 0 / 18 | 10 | 18.0 cm | 0.9545 | 2.9 m | 13.7 km/h |
| 35 | Theace6_2026-07-06_cam1_d6_cam2_d4 | new39 | 16 / 0 / 21 | 0 | 22.2 cm | 0.9972 | 13.6 m | 74.6 km/h |
| 36 | Theace1_2026-08-26_cam1_d36_cam2_d37 | pool | 11 / 11 / 62 | 44 | 33.8 cm | 0.9942 | 15.0 m | 25.2 km/h |
| 37 | Thebpca5_2026-07-07_cam1_d2_cam2_d1 | new39 | 11 / 0 / 36 | 35 | 35.0 cm | 0.9557 | 5.9 m | 16.6 km/h |
| 38 | Theace8_2026-07-02_cam1_d7_cam2_d9 | pool | 8 / 0 / 11 | 0 | 52.3 cm | 0.9906 | 16.8 m | 152.3 km/h |
| 39 | Thebcs7_2026-06-03_cam1_d14_cam2_d14 | new39 | 16 / 8 / 32 | 1 | 73.8 cm | 0.9792 | 16.7 m | 50.4 km/h |

## Clips
- 75 of 78 present. 74 from the QA API, checked as for the 10 (frame count = delivery window; a saved pipeline frame matches, corr >= 0.99).
  13 had no saved pipeline frame to compare, so only the frame count was checked. Clips are 121 frames (91 for some July sessions).
- `20_new_Thebcs4..._cam1`: this pair was run from local videos (no QA clip); cut from `inputs/cam1/source.mp4`, shifted +2 frames, anchor corr 0.9999.
- **Missing:** 14_Theace2_2026-08-24_cam1_d14_cam2_d12 (cam1); 20_new_Thebcs4_2026-10-27_cam1_d19_cam2_d9 (cam2); 28_Theace2_2026-08-24_cam1_d8_cam2_d6 (cam1).
  Theace2 2026-08-24 cam1: the QA clip has 122 frames for a 121-frame window and there is no saved frame to check alignment, so it was not kept.
  Thebcs4 2026-10-27 cam2: no QA clip, and the local source video never matched the pipeline frame (best 0.95).
