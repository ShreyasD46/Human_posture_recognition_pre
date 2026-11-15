import os
import sys
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# Ensure repo root is on sys.path
_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from models import db, User, Session, SessionError, ExerciseSet, RepRecord
from auth import create_token, login_required, decode_token, role_required
from data.poses import POSES
from exercises.registry import registry
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


# sid → PoseEvaluator instance
active_evaluators: dict = {}
# sid → session state
active_sessions: dict = {}

# Voice cooldown seconds per mode
VOICE_COOLDOWN = {"beginner": 4.0, "advanced": 8.0, "default": 2.5}


# ---------------------------------------------------------------------------
# Health & Diagnostics
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "app": "Industry-Grade Edge AI Fitness Coach",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "registered_exercises": len(registry.list_all()),
    })


# ---------------------------------------------------------------------------
# Auth (Password, PIN, QR Badge & RBAC)
# ---------------------------------------------------------------------------

@app.post("/api/auth/signup")
def signup():
    data = request.get_json(force=True)
    name, email, password = data.get("name"), data.get("email"), data.get("password")
    role = data.get("role", "member")
    if not all([name, email, password]):
        return jsonify({"error": "name, email and password are required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists"}), 409
    
    user = User(name=name, email=email, role=role)
    user.set_password(password)
    pin = data.get("pin")
    if pin:
        user.set_pin(str(pin))
    
    db.session.add(user)
    db.session.commit()
    return jsonify({"token": create_token(user.id, user.role), "user": user.to_dict()}), 201


@app.post("/api/auth/login")
def login():
    data = request.get_json(force=True)
    user = User.query.filter_by(email=data.get("email")).first()
    if not user or not user.check_password(data.get("password", "")):
        return jsonify({"error": "Incorrect email or password"}), 401
    return jsonify({"token": create_token(user.id, user.role), "user": user.to_dict()})


@app.post("/api/auth/pin-login")
def pin_login():
    """Fast touch PIN login for shared gym kiosk."""
    data = request.get_json(force=True)
    email = data.get("email")
    pin = str(data.get("pin", ""))
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_pin(pin):
        return jsonify({"error": "Invalid PIN or email"}), 401
    return jsonify({"token": create_token(user.id, user.role), "user": user.to_dict()})


@app.post("/api/auth/qr-login")
def qr_login():
    """Instant camera badge login via scanned QR token."""
    data = request.get_json(force=True)
    qr_token = data.get("qr_token")
    if not qr_token:
        return jsonify({"error": "Missing QR badge token"}), 400
    user = User.query.filter_by(qr_token=qr_token).first()
    if not user:
        return jsonify({"error": "Unrecognized gym badge"}), 404
    return jsonify({"token": create_token(user.id, user.role), "user": user.to_dict()})


@app.post("/api/auth/set-pin")
@login_required
def set_pin():
    data = request.get_json(force=True)
    pin = str(data.get("pin", ""))
    if len(pin) < 4:
        return jsonify({"error": "PIN must be at least 4 digits"}), 400
    user = User.query.get_or_404(request.user_id)
    user.set_pin(pin)
    db.session.commit()
    return jsonify({"message": "PIN updated successfully"})


@app.get("/api/auth/me")
@login_required
def me():
    user = User.query.get_or_404(request.user_id)
    return jsonify(user.to_dict())


# ---------------------------------------------------------------------------
# Exercise Catalog & Plugin Discovery (Gym & Yoga)
# ---------------------------------------------------------------------------

@app.get("/api/exercises")
def list_exercises():
    category = request.args.get("category")
    specs = registry.list_all(category=category)
    return jsonify([
        {
            "id": s.id,
            "name": s.name,
            "category": s.category,
            "muscle_groups": s.muscle_groups,
            "difficulty": s.difficulty,
            "camera_view": s.camera_view,
            "instructions": s.instructions,
            "hold_time_target": s.hold_rules.hold_time_target_seconds if s.hold_rules else 0,
            "required_joints": s.required_joints,
        }
        for s in specs
    ])


@app.get("/api/exercises/<exercise_id>")
def get_exercise_detail(exercise_id):
    spec = registry.get(exercise_id)
    if not spec:
        # Check fallback legacy POSES
        if exercise_id in POSES:
            p = POSES[exercise_id]
            return jsonify({
                "id": exercise_id,
                "name": p["label"],
                "category": "yoga",
                "instructions": p["instructions"],
                "hold_time_target": p["hold_time_target"],
                "camera_view": "front",
            })
        return jsonify({"error": "Exercise not found"}), 404
    return jsonify(spec.dict())


@app.get("/api/poses")
def legacy_list_poses():
    """Backward-compatible endpoint for existing yoga views."""
    specs = registry.list_all(category="yoga")
    return jsonify([
        {
            "id": s.id,
            "label": s.name,
            "instructions": s.instructions,
            "hold_time_target": s.hold_rules.hold_time_target_seconds if s.hold_rules else 15,
        }
        for s in specs
    ])


# ---------------------------------------------------------------------------
# Multi-User Sessions (Isolation & Dashboards)
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
    total_reps_count = 0
    for s in sessions:
        by_pose.setdefault(s.pose_name, []).append(s.accuracy_pct)
        total_reps_count += (s.total_reps or 0)
    
    trend = [{"date": s.started_at.isoformat(), "pose": s.pose_name,
               "category": s.category, "total_reps": s.total_reps,
               "accuracy": s.accuracy_pct, "avg_score": s.avg_score}
             for s in sessions]
    
    most_improved, best_delta = None, -999
    for pose, accs in by_pose.items():
        if len(accs) >= 2:
            delta = accs[-1] - accs[0]
            if delta > best_delta:
                best_delta, most_improved = delta, pose

    return jsonify({
        "trend": trend,
        "most_improved_pose": most_improved,
        "total_sessions": len(sessions),
        "total_reps": total_reps_count,
    })


# ---------------------------------------------------------------------------
# Admin & Trainer Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/admin/members")
@role_required("admin", "trainer")
def list_members():
    if request.user_role == "admin":
        members = User.query.filter_by(role="member").all()
    else:
        # Trainer sees assigned members or general members
        members = User.query.filter((User.trainer_id == request.user_id) | (User.role == "member")).all()
    return jsonify([m.to_dict() for m in members])


@app.get("/api/admin/system")
@role_required("admin")
def system_diagnostics():
    from deploy.scripts.benchmark import get_soc_temperature
    temp = get_soc_temperature()
    return jsonify({
        "soc_temperature_c": temp,
        "active_sessions_count": len(active_sessions),
        "platform": sys.platform,
    })


# ---------------------------------------------------------------------------
# Real-Time WebSocket Streaming (High-Frequency Hot Path)
# ---------------------------------------------------------------------------

_socket_users: dict = {}


@socketio.on("connect")
def on_connect(auth=None):
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

    exercise_name = data.get("pose_name") or data.get("exercise_id")
    voice_mode = data.get("voice_mode", "default")

    spec = registry.get(exercise_name)
    if not spec and exercise_name not in POSES:
        emit("session_error", {"message": f"Unknown exercise/pose: {exercise_name}"})
        return

    cooldown = VOICE_COOLDOWN.get(voice_mode, VOICE_COOLDOWN["default"])
    active_evaluators[sid] = PoseEvaluator(voice_cooldown=cooldown)
    active_sessions[sid] = {
        "user_id": user_id,
        "pose_name": exercise_name,
        "category": spec.category if spec else "yoga",
        "started_at": datetime.utcnow(),
        "correct_frames": 0,
        "total_frames": 0,
        "max_reps": 0,
        "error_log": [],
        "frame_scores": [],
        "angles_history": [],
    }

    info_payload = spec.dict() if spec else POSES[exercise_name]
    emit("session_started", {"pose": info_payload, "category": active_sessions[sid]["category"]})


@socketio.on("frame")
def on_frame(data):
    sid = request.sid
    received_at = time.time() * 1000.0

    evaluator = active_evaluators.get(sid)
    state = active_sessions.get(sid)
    if not evaluator or not state:
        emit("session_error", {"message": "No active session — call start_session first"})
        return

    if not isinstance(data, dict):
        return
    landmarks = data.get("landmarks", [])
    captured_at = data.get("capturedAt")

    if not isinstance(landmarks, list) or len(landmarks) < 25:
        return

    enable_physgnn = data.get("enable_physgnn", True)
    result = evaluator.evaluate(state["pose_name"], landmarks, enable_physgnn=enable_physgnn)
    evaluated_at = time.time() * 1000.0

    state["total_frames"] += 1
    if result["status"] == "correct":
        state["correct_frames"] += 1

    if result.get("score") is not None:
        state["frame_scores"].append(result["score"])

    if "rep_count" in result:
        state["max_reps"] = max(state["max_reps"], int(result["rep_count"]))

    for e in result.get("errors", []):
        state["error_log"].append(e)

    sent_at = time.time() * 1000.0
    if captured_at is not None:
        try:
            record_latency(float(captured_at), sent_at)
        except Exception:
            pass

    result["timing"] = {
        "received_at": round(received_at, 1),
        "evaluated_at": round(evaluated_at, 1),
        "sent_at": round(sent_at, 1),
    }

    emit("feedback", result)


@socketio.on("end_session")
def on_end_session(data=None):
    sid = request.sid
    state = active_sessions.pop(sid, None)
    active_evaluators.pop(sid, None)

    if not state:
        emit("session_error", {"message": "No active session to end"})
        return

    total = state["total_frames"]
    accuracy = 100.0 * state["correct_frames"] / max(total, 1) if total > 0 else 0.0
    hold_time = (datetime.utcnow() - state["started_at"]).total_seconds()
    total_reps = state.get("max_reps", 0)

    spec = registry.get(state["pose_name"])
    target_hold = spec.hold_rules.hold_time_target_seconds if spec and spec.hold_rules else 15.0

    session_record = None
    s_stats = None
    history = []

    if state["user_id"]:
        avg_score_val = (
            round(sum(state["frame_scores"]) / len(state["frame_scores"]), 1)
            if state["frame_scores"] else 0.0
        )
        session_record = Session(
            user_id=state["user_id"],
            category=state.get("category", "gym"),
            pose_name=state["pose_name"],
            started_at=state["started_at"],
            ended_at=datetime.utcnow(),
            total_reps=total_reps,
            hold_time_seconds=hold_time,
            accuracy_pct=round(accuracy, 1),
            avg_score=avg_score_val,
            summary_text="",
            tips="",
        )
        db.session.add(session_record)
        db.session.flush()

        counts = {}
        for e in state["error_log"]:
            joint = e.get("joint", "body")
            feedback = e.get("feedback", "")
            severity = e.get("severity", "moderate")
            key = (joint, feedback, severity)
            counts[key] = counts.get(key, 0) + 1

        for (joint, direction, severity), count in counts.items():
            db.session.add(SessionError(
                session_id=session_record.id,
                joint=joint,
                direction=direction,
                severity=severity,
                count=count
            ))
        db.session.commit()

        s_stats = aggregate_session(session_record.id, state["frame_scores"], angles_history=state.get("angles_history"))
        history = get_pose_history(state["user_id"], state["pose_name"], limit=10)

    report = generate_report(
        exercise_name=state["pose_name"],
        category=state.get("category", "gym"),
        total_reps=total_reps,
        accuracy=accuracy,
        hold_time=hold_time,
        target_hold=target_hold,
        errors=state["error_log"],
        session_stats=s_stats,
        history=history
    )

    if session_record:
        session_record.summary_text = report["summary"]
        session_record.tips = "|".join(report["tips"])
        db.session.commit()

    emit("session_summary", {
        "accuracy_pct": round(accuracy, 1),
        "total_reps": total_reps,
        "avg_score": s_stats["avg_score"] if s_stats else 0.0,
        "score_trend": s_stats["score_trend"] if s_stats else None,
        "hold_time_seconds": round(hold_time, 1),
        "target_hold_seconds": target_hold,
        "summary": report["summary"],
        "tips": report["tips"],
        "caveat": report.get("caveat", ""),
        "category": state.get("category", "gym"),
        "session_id": session_record.id if session_record else None,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    socketio.run(app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True)
