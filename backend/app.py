import os
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from models import db, User, Session, SessionError
from auth import create_token, login_required, decode_token
from data.poses import POSES
from pose_engine import PoseEvaluator
from report_agent import generate_report
from session_stats import aggregate_session, get_pose_history
from latency_monitor import record_latency, get_latency_stats

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'yoga.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
CORS(app, resources={r"/*": {"origins": os.environ.get("CORS_ORIGIN", "*")}})
socketio = SocketIO(app, cors_allowed_origins=os.environ.get("CORS_ORIGIN", "*"))
db.init_app(app)

with app.app_context():
    db.create_all()
    # Run migration for avg_score column if the DB already exists
    try:
        import migrate_add_avg_score
        migrate_add_avg_score.run()
    except Exception:
        pass  # New DB — column already created by create_all()

# sid → PoseEvaluator instance
active_evaluators: dict = {}
# sid → {pose_name, user_id, started_at, correct_frames, total_frames,
#         error_log, frame_scores, voice_mode}
active_sessions: dict = {}

# Voice cooldown seconds per mode
VOICE_COOLDOWN = {"beginner": 4.0, "advanced": 8.0, "default": 2.5}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@app.post("/api/auth/signup")
def signup():
    data = request.get_json(force=True)
    name, email, password = data.get("name"), data.get("email"), data.get("password")
    if not all([name, email, password]):
        return jsonify({"error": "name, email and password are required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists"}), 409
    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"token": create_token(user.id), "user": user.to_dict()}), 201


@app.post("/api/auth/login")
def login():
    data = request.get_json(force=True)
    user = User.query.filter_by(email=data.get("email")).first()
    if not user or not user.check_password(data.get("password", "")):
        return jsonify({"error": "Incorrect email or password"}), 401
    return jsonify({"token": create_token(user.id), "user": user.to_dict()})


@app.get("/api/auth/me")
@login_required
def me():
    user = User.query.get_or_404(request.user_id)
    return jsonify(user.to_dict())


# ---------------------------------------------------------------------------
# Poses
# ---------------------------------------------------------------------------

@app.get("/api/poses")
def list_poses():
    return jsonify([
        {"id": key, "label": p["label"], "instructions": p["instructions"],
         "hold_time_target": p["hold_time_target"]}
        for key, p in POSES.items()
    ])


# ---------------------------------------------------------------------------
# Sessions (history + dashboard)
# ---------------------------------------------------------------------------

@app.get("/api/sessions")
@login_required
def list_sessions():
    sessions = (Session.query.filter_by(user_id=request.user_id)
                .order_by(Session.started_at.desc()).limit(50).all())
    return jsonify([s.to_dict() for s in sessions])


@app.get("/api/sessions/<int:session_id>")
@login_required
def get_session(session_id):
    s = Session.query.filter_by(id=session_id, user_id=request.user_id).first_or_404()
    return jsonify(s.to_dict())


@app.get("/api/dashboard")
@login_required
def dashboard():
    sessions = Session.query.filter_by(user_id=request.user_id).order_by(Session.started_at).all()
    by_pose = {}
    for s in sessions:
        by_pose.setdefault(s.pose_name, []).append(s.accuracy_pct)
    trend = [{"date": s.started_at.isoformat(), "pose": s.pose_name,
               "accuracy": s.accuracy_pct, "avg_score": s.avg_score}
             for s in sessions]
    most_improved, best_delta = None, -999
    for pose, accs in by_pose.items():
        if len(accs) >= 2:
            delta = accs[-1] - accs[0]
            if delta > best_delta:
                best_delta, most_improved = delta, pose
    return jsonify({"trend": trend, "most_improved_pose": most_improved,
                     "total_sessions": len(sessions)})


# ---------------------------------------------------------------------------
# Debug (dev-only)
# ---------------------------------------------------------------------------

@app.get("/debug/latency")
def debug_latency():
    if not app.debug and not os.environ.get("ENABLE_DEBUG_ENDPOINTS"):
        return jsonify({"error": "Not available in production"}), 403
    stats = get_latency_stats()
    if not stats:
        return jsonify({"message": "No latency data yet — run a session first."})
    return jsonify(stats)


# ---------------------------------------------------------------------------
# Realtime WebSocket: keypoints → rule engine → feedback
# ---------------------------------------------------------------------------

_socket_users: dict = {}   # sid → user_id


@socketio.on("connect")
def on_connect(auth=None):
    """Read JWT from the Socket.IO auth handshake and persist user_id."""
    token = None
    if auth and isinstance(auth, dict):
        token = auth.get("token")
    if not token:
        token = request.args.get("token")
    if token:
        try:
            payload = decode_token(token)
            _socket_users[request.sid] = payload["user_id"]
        except Exception:
            _socket_users[request.sid] = None
    else:
        _socket_users[request.sid] = None


@socketio.on("disconnect")
def on_disconnect():
    _socket_users.pop(request.sid, None)
    active_evaluators.pop(request.sid, None)
    active_sessions.pop(request.sid, None)


@socketio.on("start_session")
def on_start_session(data):
    sid = request.sid
    user_id = _socket_users.get(sid)
    if not isinstance(data, dict):
        emit("session_error", {"message": "Malformed start_session payload"})
        return

    pose_name  = data.get("pose_name")
    voice_mode = data.get("voice_mode", "default")   # "beginner" | "advanced" | "default"

    if not pose_name or pose_name not in POSES:
        emit("session_error", {"message": "Unknown pose"})
        return

    cooldown = VOICE_COOLDOWN.get(voice_mode, VOICE_COOLDOWN["default"])
    active_evaluators[sid] = PoseEvaluator(voice_cooldown=cooldown)
    active_sessions[sid] = {
        "user_id":       user_id,
        "pose_name":     pose_name,
        "started_at":    datetime.utcnow(),
        "correct_frames": 0,
        "total_frames":   0,
        "error_log":      [],
        "frame_scores":   [],    # Phase 1: per-frame weighted scores
    }
    emit("session_started", {"pose": POSES[pose_name]})


@socketio.on("frame")
def on_frame(data):
    sid        = request.sid
    received_at = time.time() * 1000   # Phase 4: timestamp on arrival

    evaluator = active_evaluators.get(sid)
    state     = active_sessions.get(sid)
    if not evaluator or not state:
        emit("session_error", {"message": "No active session — call start_session first"})
        return

    if not isinstance(data, dict):
        return
    landmarks   = data.get("landmarks", [])
    captured_at = data.get("capturedAt")   # Phase 4: frontend timestamp (ms)

    # Validate landmark structure
    if (not isinstance(landmarks, list) or len(landmarks) < 29
            or not all(isinstance(lm, dict) and "x" in lm and "y" in lm
                       for lm in landmarks[:29])):
        return  # silently drop malformed frames

    enable_physgnn = data.get("enable_physgnn", True)
    result = evaluator.evaluate(state["pose_name"], landmarks, enable_physgnn=enable_physgnn)
    evaluated_at = time.time() * 1000   # Phase 4

    state["total_frames"] += 1
    if result["status"] == "correct":
        state["correct_frames"] += 1

    # Track per-frame weighted score (Phase 1)
    if result.get("score") is not None:
        state["frame_scores"].append(result["score"])

    for e in result["errors"]:
        state["error_log"].append(e)

    # Phase 4: record latency
    sent_at = time.time() * 1000
    if captured_at is not None:
        try:
            record_latency(float(captured_at), sent_at)
        except (TypeError, ValueError):
            pass

    # Attach timing info to the response
    result["timing"] = {
        "received_at":  round(received_at, 1),
        "evaluated_at": round(evaluated_at, 1),
        "sent_at":      round(sent_at, 1),
    }

    emit("feedback", result)


@socketio.on("end_session")
def on_end_session(data=None):
    sid   = request.sid
    state = active_sessions.pop(sid, None)
    active_evaluators.pop(sid, None)

    if not state:
        emit("session_error", {"message": "No active session to end"})
        return

    total    = state["total_frames"]
    accuracy = 100.0 * state["correct_frames"] / max(total, 1) if total > 0 else 0.0
    hold_time = (datetime.utcnow() - state["started_at"]).total_seconds()
    pose_cfg  = POSES[state["pose_name"]]

    # Persist session to DB first (needed for aggregate_session FK lookup)
    session_record = None
    s_stats  = None
    history  = []

    if state["user_id"]:
        avg_score_val = (
            round(sum(state["frame_scores"]) / len(state["frame_scores"]), 1)
            if state["frame_scores"] else 0.0
        )
        session_record = Session(
            user_id=state["user_id"], pose_name=state["pose_name"],
            started_at=state["started_at"], ended_at=datetime.utcnow(),
            hold_time_seconds=hold_time, accuracy_pct=round(accuracy, 1),
            avg_score=avg_score_val,
            summary_text="", tips="",
        )
        db.session.add(session_record)
        db.session.flush()   # get session_record.id without full commit

        # Write error aggregates
        counts: dict = {}
        for e in state["error_log"]:
            key = (e["joint"], e.get("feedback", e.get("direction", "")), e["severity"])
            counts[key] = counts.get(key, 0) + 1
        for (joint, direction, severity), count in counts.items():
            db.session.add(SessionError(
                session_id=session_record.id, joint=joint,
                direction=direction, severity=severity, count=count,
            ))
        db.session.commit()

        # Phase 3: stats + trend history
        s_stats = aggregate_session(session_record.id, state["frame_scores"])
        history = get_pose_history(state["user_id"], state["pose_name"], limit=10)

    # Generate AI report (Phase 3: pass stats + history)
    report = generate_report(
        state["pose_name"], accuracy, hold_time,
        pose_cfg["hold_time_target"], state["error_log"],
        session_stats=s_stats,
        history=history,
    )

    emit("session_summary", {
        "accuracy_pct":         round(accuracy, 1),
        "avg_score":            s_stats["avg_score"] if s_stats else 0.0,
        "score_trend":          s_stats["score_trend"] if s_stats else None,
        "hold_time_seconds":    round(hold_time, 1),
        "target_hold_seconds":  pose_cfg["hold_time_target"],
        "summary":              report["summary"],
        "tips":                 report["tips"],
        "caveat":               report.get("caveat", ""),
        "session_id":           session_record.id if session_record else None,
    })


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, debug=True, allow_unsafe_werkzeug=True)
