# Long-Term Product Roadmap (Phase 9)
**AI Fitness Coaching Kiosk Appliance**

---

## 1. Near-Term Enhancements (Q1–Q2 2027)

### 1.1 Opt-In Rep-by-Rep Video Clips
- **Feature:** Buffer the last 3 reps in circular memory; allow the member to review a slow-motion instant replay side-by-side with the Ghost Reference Skeleton.
- **Privacy Safeguard:** Explicit toggle required; clips auto-deleted upon session exit unless member saves to mobile via one-time QR transfer.

### 1.2 Wearable Integration (Heart Rate & RPE)
- **Feature:** Bluetooth Low Energy (BLE) integration with standard HR chest straps (Polar H10, Garmin HRM-Pro) and smartwatches.
- **Metric:** Combine biomechanical form score with heart rate recovery and estimated Rate of Perceived Exertion (RPE).

---

## 2. Mid-Term Innovations (Q3–Q4 2027)

### 2.1 Multi-Camera Synchronized Capture
- **Feature:** Support dual CSI/USB cameras (one anterior front view, one sagittal side view) synchronized via hardware timestamps.
- **Capability:** True 3D markerless motion capture eliminating all occlusions during complex compound lifts (Squat, Deadlift, Clean & Jerk).

### 2.2 Gym-Wide Community Leaderboards
- **Feature:** Optional opted-in gym leaderboards ranking members by Form Score consistency and streaks rather than raw weight, incentivizing safe lifting technique.

---

## 3. Hardware Evolution: Raspberry Pi 5 + AI HAT

### 3.1 Hardware Architecture Shift
- **Host SoC:** Raspberry Pi 5 (Quad-core Cortex-A76 @ 2.4 GHz, 2–3x CPU performance of Pi 4B).
- **Neural Coprocessor:** Raspberry Pi AI HAT+ with Hailo-8L / Hailo-8 NPU (13 to 26 TOPS INT8 compute).
- **Target Metrics:**
  - 60+ FPS pose estimation at full 1080p resolution.
  - Sub-15 ms latency end-to-end.
  - Multi-person tracking in wide-angle frame with automatic active user isolation.
