# Sthira — Real-Time AI Yoga Posture Recognition & Biomechanical Correction

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.0+-646cff.svg)](https://vitejs.dev/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **Sthira** (*Sanskrit: स्थिर - steady, stable, resolute*) is an intelligent, privacy-preserving yoga posture evaluation platform. It couples edge-computed 33-keypoint pose estimation with **Sthira-PhysGNN**—a Physics-Informed Spatio-Temporal Graph Neural Network—and an explainable biomechanical rule engine to deliver real-time voice coaching, joint-angle alignment, and automated post-session analytics.

---

## 🌟 Key Highlights

- **🔒 Privacy-First Edge Estimation:** Raw video frames never leave the client browser. Video is processed locally via MediaPipe BlazePose, streaming only lightweight coordinate vectors (33 keypoints) to the backend.
- **🧠 Sthira-PhysGNN Refinement:** Novel hybrid architecture combining Spatial-Temporal Graph Convolutional Networks (ST-GCN), dynamic self-attention, and biomechanical physics loss constraints (bone-length invariance, orthopedic Range of Motion limits, temporal jerk regularization).
- **⚡ Sub-25ms End-to-End Latency:** High-throughput WebSocket pipeline delivering live feedback at 30+ FPS.
- **🗣️ Natural Voice Coaching:** Real-time, debounced voice corrections with positive reinforcement cues using the browser's Web Speech API.
- **📊 Comprehensive Session Reports:** Post-session clinical breakdown powered by an AI agent (Claude with deterministic fallback) plus automated vector PDF export.
- **✨ Awwwards-Inspired Interface:** Minimalist dark-mode design with interactive canvas skeleton overlays, real-time angle gauges, progress analytics, and animated pose demos.

---

## 🔬 Benchmark Results (Sthira-PhysGNN vs. BlazePose)

Evaluated across multi-view sequence replays with synthetic noise and joint occlusions:

| Metric | Stock MediaPipe BlazePose | **Sthira-PhysGNN (Ours)** | Relative Improvement |
| :--- | :---: | :---: | :---: |
| **MPJPE (Mean Per-Joint Pos. Error)** | 42.1 mm | **28.4 mm** | **+32.6%** |
| **Temporal Jitter ($\times 10^{-4}$)** | 13.31 | **3.07** | **+76.9%** |
| **Bone Length Variation Error** | 6.7% | **4.5%** | **+32.0%** |
| **Occlusion Error (Partial Dropout)** | 112.2 mm | **48.1 mm** | **+57.1%** |

*(Detailed LaTeX publication tables and methodology are available in [`backend/ml/benchmark_results.tex`](backend/ml/benchmark_results.tex) and [`Sthira_PhysGNN_Technical_Report.pdf`](Sthira_PhysGNN_Technical_Report.pdf)).*

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────┐
│                   CLIENT (React + Vite)                │
│  Webcam Stream (60 FPS)                                │
│       │                                                │
│       ▼                                                │
│  MediaPipe BlazePose (Client-side 33 landmarks)        │
│       │                                                │
│       ├─► Local Skeleton Canvas Overlay (Instant UI)   │
│       └─► WebSocket: {landmarks, pose, timestamp}      │
└──────────────────────────┬─────────────────────────────┘
                           │  WebSocket (<15ms transit)
┌──────────────────────────▼─────────────────────────────┐
│                   SERVER (Flask + PyTorch)             │
│                                                        │
│  1. Sthira-PhysGNN Neural Filter                       │
│     ├── ST-GCN Spatial Convolutions (Bone Adjacency)   │
│     ├── Dynamic Attention Adjacency                    │
│     └── Physics Loss Refinement (Kinematic Limits)     │
│                                                        │
│  2. Deterministic Biomechanical Rule Engine            │
│     ├── 3D Vector Angle Computation                    │
│     ├── Tolerances & Per-Pose Target Check             │
│     └── Temporal Debouncing & Voice Cooldown           │
│                                                        │
│  3. Real-Time Feedback Dispatch                        │
│     └── WebSocket Out: {status, score, errors, speak}  │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│                 POST-SESSION REPORTING                 │
│  • Aggregated Biomechanical Telemetry                  │
│  • AI Summary & Injury Risk Analysis (Claude / Fallback)│
│  • Exportable Vector PDF Report                        │
│  • SQLite / SQLAlchemy Persistent History              │
└────────────────────────────────────────────────────────┘
```

---

## 🧘 Supported Pose Library

| Pose (Sanskrit) | Common Name | Key Evaluated Joints & Biomechanics |
| :--- | :--- | :--- |
| **Tadasana** | Mountain Pose | Spine alignment, knee extension ($170^{\circ}-180^{\circ}$), shoulder leveling |
| **Vrikshasana** | Tree Pose | Standing leg stability, bent knee abduction ($60^{\circ}-110^{\circ}$), hands overhead |
| **Trikonasana** | Triangle Pose | Front leg extension, torso lateral flexion, vertical arm alignment ($170^{\circ}-180^{\circ}$) |
| **Virabhadrasana II** | Warrior II | Front knee flexion ($85^{\circ}-105^{\circ}$), horizontal arm extension, torso verticality |
| **Utkatasana** | Chair Pose | Bilateral knee flexion ($80^{\circ}-110^{\circ}$), hip hinge, arm elevation ($150^{\circ}-180^{\circ}$) |

*Reference configurations and joint tolerance angles are located in [`backend/data/poses.py`](backend/data/poses.py).*

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & `npm`
- Webcam for real-time video capture

---

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
# On macOS/Linux:
source venv/bin/activate
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Optional: add your ANTHROPIC_API_KEY for Claude-powered session reports

# Launch Flask-SocketIO backend (runs on http://localhost:5001)
python app.py
```

---

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env

# Start Vite development server (runs on http://localhost:5173)
npm run dev
```

---

### 3. Usage Flow

1. Open **`http://localhost:5173`** in your browser.
2. Sign up or log in with your credentials.
3. Select a pose from the **Practice Library**.
4. Allow webcam access. Stand back until your full body (shoulders to feet) is visible in the frame.
5. Auto-calibration will lock onto your form and begin real-time posture tracking and audio guidance.
6. Click **End Session** to review your posture score, stability metrics, joint accuracy breakdowns, and download your clinical session PDF.

---

## 🧪 Testing & Benchmarks

Run the test and evaluation suites from the `backend/` directory:

```bash
cd backend

# Run rule engine validation tests
python -m unittest tests/test_rule_engine.py

# Run PhysGNN ablation benchmark comparison
python tests/benchmark_ablation.py

# Run temporal replay evaluation
python tests/replay_eval.py
```

---

## 📁 Repository Structure

```
yoga-app/
├── Sthira_PhysGNN_Technical_Report.pdf  # Comprehensive technical and research report
├── backend/
│   ├── app.py                          # Flask & WebSocket application entrypoint
│   ├── auth.py                         # JWT user authentication & session routes
│   ├── models.py                       # SQLAlchemy database models
│   ├── pose_engine.py                  # Real-time stateful pose evaluator
│   ├── scoring.py                      # Joint angle math & tolerance scoring
│   ├── session_stats.py                # Telemetry aggregator
│   ├── report_agent.py                 # Post-session LLM analysis agent
│   ├── generate_report_pdf.py          # PDF generation engine
│   ├── sthira_physgnn_best.pt          # Pretrained Sthira-PhysGNN PyTorch weights
│   ├── data/
│   │   ├── poses.py                    # Target angles, tolerances & audio cues
│   │   └── landmark_map.py             # MediaPipe 33 keypoint definitions
│   ├── ml/
│   │   ├── biomechanics.py             # Anatomical bone trees & orthopedic ROM bounds
│   │   ├── pytorch_model.py            # ST-GCN + Attention PhysGNN architecture
│   │   ├── pytorch_losses.py           # Physics-informed loss formulation
│   │   ├── pytorch_train.py            # Training loop with biomechanical regularization
│   │   └── benchmark_results.tex       # LaTeX ablation table
│   └── tests/
│       ├── test_rule_engine.py         # Unit tests for scoring & edge cases
│       └── benchmark_ablation.py       # Ablation evaluation scripts
│
└── frontend/
    ├── src/
    │   ├── App.jsx                     # Route definitions & navigation
    │   ├── components/
    │   │   ├── CameraView.jsx          # MediaPipe camera capture & canvas overlay
    │   │   ├── SessionView.jsx         # Live HUD, feedback counters & controls
    │   │   ├── PosePicker.jsx          # Visual pose catalog
    │   │   ├── PoseDemo.jsx            # Interactive pose reference visualizer
    │   │   ├── Dashboard.jsx           # Analytics, session history & metrics
    │   │   ├── AuthPage.jsx            # Authentication interface
    │   │   └── Landing.jsx             # Product landing experience
    │   ├── hooks/
    │   │   ├── usePoseDetection.js     # MediaPipe lifecycle hook
    │   │   └── useVoiceFeedback.js     # Web Speech synthesis hook
    │   └── services/
    │       ├── socket.js               # WebSocket client connection
    │       └── api.js                  # Axios HTTP client
    └── package.json
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
