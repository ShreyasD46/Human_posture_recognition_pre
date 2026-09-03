# Sthira — Real-Time Yoga Posture Recognition

A full-stack app that watches your webcam, evaluates 5 standing yoga poses against
reference joint angles in real time, speaks corrections, and generates an
AI session report. Built per the project brief: real-time voice feedback,
final report, accurate recognition on a limited pose set, and a minimal,
awwwards-style frontend.

## Architecture

```
Browser (React)                    Server (Flask)
─────────────────                  ─────────────────
Webcam → MediaPipe BlazePose  →    WebSocket: keypoints in
(33 keypoints, client-side,        Deterministic rule engine:
 nothing leaves the browser)       angle math + tolerance check
        │                                  │
        ▼                                  ▼
Skeleton overlay + voice      ←    {status, errors, speak}
(Web Speech API)

On "end session"          →        AI agent (LLM or templated
                                    fallback) → session report
                                    → stored in SQLite
```

**Why this split:** pose *estimation* runs client-side (MediaPipe/BlazePose
in-browser, no video ever hits the server). Pose *evaluation* (angle math
against reference tolerances) is a deterministic rule engine on the
backend — fast, explainable, and testable, not an ML black box, which
matters for a safety-relevant correction loop. The LLM only runs once,
after a session ends, on aggregated stats — never per-frame — to keep
real-time feedback cheap and predictable.

This mirrors the approach in the referenced literature: BlazePose /
MediaPipe / MoveNet for keypoint extraction, angle-based comparison for
correctness (as opposed to end-to-end classifiers) is what keeps latency
low enough for live correction — heavier classifiers (CNN/LSTM/GNN/YOLOv5,
~90-98% accuracy in the cited papers) are better suited to the
post-session, non-real-time report, which is where the AI agent layer
sits here (`report_agent.py`, pluggable with a real LLM call).

## Pose set (MVP)
Tadasana, Vrikshasana, Trikonasana, Virabhadrasana II, Utkatasana —
front-facing, standing only. Reference angles live in
`backend/data/poses.py`; extend that file to add more poses.

## Run it

### Backend
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit JWT_SECRET; ANTHROPIC_API_KEY is optional
python app.py          # runs on http://localhost:5001
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev            # runs on http://localhost:5173
```

Open http://localhost:5173, sign up, pick a pose, and allow camera access.
Stand back until your shoulders/hips/knees/ankles are all visible —
calibration auto-starts the session once you're fully in frame.

## What's deterministic vs. AI
- **Deterministic (backend rule engine):** joint-angle calculation, tolerance
  checks, error debouncing (an error must persist 4 frames before it's
  surfaced) and a voice cooldown (4s) so cues don't spam.
- **AI agent (post-session only):** `report_agent.py` — if `ANTHROPIC_API_KEY`
  is set it calls Claude for a natural-language summary + tips; otherwise a
  templated fallback keeps the app fully functional with zero API cost.

## Notes / next steps
- SQLite is used for simplicity; swap `SQLALCHEMY_DATABASE_URI` for Postgres
  in production.
- The rule engine's reference angles in `poses.py` are reasonable starting
  points, not clinically validated — refine per the cited biomechanics
  literature before real deployment.
- Stretch ideas from the original build plan (offline mode, injury-risk
  pattern flagging across sessions, a heavier post-session classifier) are
  not implemented here but the data model (`SessionError` table) already
  logs what's needed to build them later.
