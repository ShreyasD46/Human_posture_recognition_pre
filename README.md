# Sthira — Industry-Grade AI Fitness Coaching Kiosk

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/React-18-61dafb.svg)](https://reactjs.org/)
[![FastAPI / Flask-SocketIO](https://img.shields.io/badge/Flask--SocketIO-WebSocket-green.svg)](https://flask-socketio.readthedocs.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%204B%20%7C%20x86-lightgrey.svg)]()

> **Sthira** (*Sanskrit: स्थिर — steady, stable, resolute*) is a commercial, edge-native AI fitness coaching
> kiosk that runs fully on a **Raspberry Pi 4B** with a camera and display. It covers both
> **Gym** (rep-counting, tempo, form scoring) and **Yoga** (hold timer, alignment, breathing)
> in a single unified platform sold to gyms and training institutes.

---

## 🌟 Key Highlights

| Feature | Detail |
|---|---|
| 🏋️ **Gym + Yoga** | 10 exercises across both categories, fully extensible via YAML plugins |
| 👻 **Ghost Skeleton** | Translucent reference form retargeted to the user's own body proportions |
| 🎨 **Color-Coded Joints** | Green / Amber / Red live bone overlay — readable from 3 m |
| 🧮 **Rep FSM + Form Scorer** | Hysteresis state machine, 0–100 form score, per-rep records |
| 👥 **Multi-User Kiosk** | PIN / QR login, Argon2id hashing, Role RBAC (Member / Trainer / Admin) |
| 📊 **AI Session Summary** | Offline deterministic + optional cloud LLM bridge |
| 🔒 **Privacy-First** | No video stored; only 33 landmark coordinates sent over WebSocket |
| ⚡ **Pi 4B Optimised** | TFLite + XNNPACK, threaded pipeline, <150 ms latency, 20+ FPS target |

---

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────────────────┐
│              CLIENT  (React 18 + Vite + TypeScript)           │
│  Webcam → MediaPipe BlazePose WASM → 33 landmarks             │
│  Canvas: User skeleton (color-coded) + Ghost skeleton (dashed)│
│  HUD: Reps · Sets · Phase · Form Score ring · Hold Timer      │
└──────────────────────────┬────────────────────────────────────┘
                           │  WebSocket (landmarks + metadata)
┌──────────────────────────▼────────────────────────────────────┐
│              BACKEND  (Flask-SocketIO, Python 3.11)           │
│  PoseEvaluator ──► ExerciseRegistry (YAML plugins)            │
│  RepFSM ──► FormScorer ──► GhostRetargeter                    │
│  SessionStats ──► ReportAgent (offline ± LLM)                 │
│  SQLAlchemy (SQLite WAL) ──► User / Session / RepRecord       │
└──────────────────────────┬────────────────────────────────────┘
                           │
┌──────────────────────────▼────────────────────────────────────┐
│              CORE ENGINE  (pure Python, Pi 4B ready)          │
│  core/math/angles.py      · core/filters/one_euro.py         │
│  core/engine/fsm.py       · core/engine/hold_timer.py        │
│  core/scoring/form_scorer.py · core/ghost/retargeting.py     │
│  core/camera/pipeline.py  · core/pose/base.py (TFLite stub)  │
└───────────────────────────────────────────────────────────────┘
```

---

## 🏋️ Exercise Library

### Gym Category
| Exercise | Tracking |
|---|---|
| Push-Up | Elbow angle FSM, half-rep detection |
| Bench Press | Bilateral elbow angle |
| Bicep Curl | Elbow 150°→40° phases, break detection |
| Lateral Raise | Shoulder abduction 10°→80° |
| Sitting Posture | Isometric hold with spine alignment |

### Yoga Category
| Pose | Tracking |
|---|---|
| Tadasana | Spine verticality, knee extension |
| Vrikshasana | Standing-leg stability, raised-knee abduction |
| Trikonasana | Lateral torso flexion, arm alignment |
| Virabhadrasana II | Front knee flexion, horizontal arms |
| Utkatasana | Bilateral knee bend, arm elevation |

> Add new exercises by dropping a YAML file in `exercises/gym/` or `exercises/yoga/` — no Python required.
> See [`docs/ADDING_NEW_EXERCISES.md`](docs/ADDING_NEW_EXERCISES.md).

---

## 🚀 Quick Start (Development)

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Webcam

### 1 · Backend

```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

pip install -r requirements.txt
python app.py          # → http://localhost:5001
```

### 2 · Frontend

```bash
npm --prefix frontend install
npm --prefix frontend run dev  # → http://localhost:5173
```

### 3 · Open

Navigate to **http://localhost:5173** → Sign up → Pick Gym or Yoga → Start training.

---

## 🧪 Tests

```bash
# Full suite (25 tests)
backend/venv/Scripts/python.exe -m pytest tests/ backend/tests/ -v

# Benchmark (FPS, latency, CPU, RAM, temperature)
make benchmark
```

---

## 📁 Repository Structure

```
yoga-app/
├── core/                        # Pi 4B–ready inference engine
│   ├── math/angles.py
│   ├── filters/                 # One-Euro landmark smoother
│   ├── engine/                  # RepFSM + HoldTimer
│   ├── scoring/form_scorer.py
│   ├── ghost/retargeting.py     # Ghost skeleton generator
│   ├── camera/pipeline.py       # Threaded zero-lag camera pipeline
│   └── pose/base.py             # PoseEstimator ABC + TFLite stub
│
├── exercises/
│   ├── registry.py              # YAML plugin loader
│   ├── gym/                     # push_up, bench_press, bicep_curl …
│   └── yoga/                    # tadasana, vrikshasana, trikonasana …
│
├── backend/
│   ├── app.py                   # Flask-SocketIO entrypoint
│   ├── auth.py                  # JWT + Argon2id + RBAC
│   ├── models.py                # User / Session / RepRecord / ExerciseSet
│   ├── pose_engine.py           # PoseEvaluator (dual yoga+gym paths)
│   ├── report_agent.py          # Offline summary + optional LLM bridge
│   └── session_stats.py        # Telemetry aggregator
│
├── frontend/src/
│   ├── components/
│   │   ├── Landing.jsx          # Product landing (Gym + Yoga)
│   │   ├── AuthPage.jsx         # Password + PIN login
│   │   ├── PosePicker.jsx       # Exercise catalog with category filter
│   │   ├── SessionView.jsx      # Live HUD (reps / hold / form score)
│   │   ├── CameraView.jsx       # Dual skeleton canvas (user + ghost)
│   │   └── Dashboard.jsx        # Progress with gym/yoga filter
│   └── services/api.js
│
├── tests/
│   ├── regression/              # Exercise plugin regression tests
│   └── replay/                  # Video replay tests
│
├── deploy/
│   ├── install.sh               # One-line Pi installer
│   ├── systemd/                 # ai-coach-backend.service + kiosk.service
│   └── scripts/benchmark.py     # make benchmark
│
├── docs/
│   ├── AUDIT.md
│   ├── ARCHITECTURE.md
│   ├── HARDWARE_BOM.md
│   ├── USER_GUIDE.md
│   ├── ADMIN_GUIDE.md
│   ├── ROADMAP.md
│   └── ADDING_NEW_EXERCISES.md
│
└── vendor/gym_legacy/           # Original AI_Gym_trainer repo (reference)
```

---

## 🍓 Raspberry Pi 4B Deployment

```bash
# On Pi OS 64-bit (Bookworm), Python 3.11
curl -fsSL https://raw.githubusercontent.com/YOUR_ORG/sthira/main/deploy/install.sh | bash

# Then visit the first-boot wizard at http://<pi-ip>:5001/setup
```

See [`docs/HARDWARE_BOM.md`](docs/HARDWARE_BOM.md) for the full camera/mount/lighting bill of materials.

Production stack:
- Backend: Flask-SocketIO behind **Gunicorn + eventlet** (systemd)
- Frontend: **Chromium kiosk mode** at 720p (systemd)
- Inference: **TFLite + XNNPACK** via MediaPipe Pose Lite (ARM64 wheel)
- Camera: **Picamera2** (CSI) or OpenCV V4L2 (USB webcam)

---

## 🔐 Security

- Passwords & PINs: **Argon2id** hashing (`argon2-cffi`)
- Sessions: **JWT** (HS256), stored in `localStorage`
- CORS: configurable via `CORS_ORIGIN` env var
- Admin panel: local-network-only by default
- No hardcoded secrets — use `.env`

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

## 🗺️ Roadmap

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for planned features:
multi-camera support, wearable integration, cloud sync dashboard,
per-rep video clip opt-in, leaderboard/challenges, and more.
