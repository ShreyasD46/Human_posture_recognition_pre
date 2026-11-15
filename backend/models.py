"""
SQLAlchemy Database Models for Multi-User Kiosk Fitness Coaching Appliance.
Supports Admin, Trainer, and Member roles, Workout Routines, Sets, Reps, and Privacy.
"""
from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

try:
    from argon2 import PasswordHasher
    _ph = PasswordHasher()
    def hash_password(password: str) -> str:
        return _ph.hash(password)
    def verify_password(hashed: str, password: str) -> bool:
        try:
            return _ph.verify(hashed, password)
        except Exception:
            return check_password_hash(hashed, password)
except ImportError:
    def hash_password(password: str) -> str:
        return generate_password_hash(password)
    def verify_password(hashed: str, password: str) -> bool:
        return check_password_hash(hashed, password)


db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), default="member")  # admin | trainer | member
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    pin_hash = db.Column(db.String(255), nullable=True)  # For quick 4-6 digit PIN login
    qr_token = db.Column(db.String(64), unique=True, nullable=True)  # For QR badge camera scan
    trainer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # Anthropometric profile
    height_cm = db.Column(db.Float, default=175.0)
    weight_kg = db.Column(db.Float, default=70.0)
    fitness_level = db.Column(db.String(20), default="beginner")  # beginner | intermediate | advanced
    injuries = db.Column(db.Text, default="[]")  # JSON list of injured joints to protect

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sessions = db.relationship("Session", backref="user", cascade="all, delete-orphan", lazy="dynamic")

    def set_password(self, password: str):
        self.password_hash = hash_password(password)

    def check_password(self, password: str) -> bool:
        return verify_password(self.password_hash, password)

    def set_pin(self, pin: str):
        self.pin_hash = hash_password(pin)

    def check_pin(self, pin: str) -> bool:
        if not self.pin_hash:
            return False
        return verify_password(self.pin_hash, pin)

    def to_dict(self):
        return {
            "id": self.id,
            "role": self.role,
            "name": self.name,
            "email": self.email,
            "has_pin": bool(self.pin_hash),
            "qr_token": self.qr_token,
            "trainer_id": self.trainer_id,
            "height_cm": self.height_cm,
            "weight_kg": self.weight_kg,
            "fitness_level": self.fitness_level,
            "injuries": json.loads(self.injuries) if self.injuries else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WorkoutRoutine(db.Model):
    """Trainer-assigned or custom routine with exercise sequences, sets, and reps."""
    __tablename__ = "routines"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default="")
    category = db.Column(db.String(20), default="gym")  # gym | yoga
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    exercises_json = db.Column(db.Text, default="[]")  # List of {exercise_id, sets, target_reps, rest_seconds}
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "created_by_id": self.created_by_id,
            "assigned_to_id": self.assigned_to_id,
            "exercises": json.loads(self.exercises_json) if self.exercises_json else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category = db.Column(db.String(20), default="yoga")  # gym | yoga
    pose_name = db.Column(db.String(80), nullable=False)  # or exercise_id
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)

    # Metrics
    total_reps = db.Column(db.Integer, default=0)
    hold_time_seconds = db.Column(db.Float, default=0.0)
    accuracy_pct = db.Column(db.Float, default=0.0)
    avg_score = db.Column(db.Float, default=0.0)
    tempo_score = db.Column(db.Float, default=0.0)

    # Narrative feedback
    summary_text = db.Column(db.Text, default="")
    tips = db.Column(db.Text, default="")  # Pipe-delimited or JSON string

    # Relationships
    errors = db.relationship("SessionError", backref="session", cascade="all, delete-orphan")
    sets = db.relationship("ExerciseSet", backref="session", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category": self.category,
            "pose_name": self.pose_name,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "total_reps": self.total_reps,
            "hold_time_seconds": round(self.hold_time_seconds, 1),
            "accuracy_pct": round(self.accuracy_pct, 1),
            "avg_score": round(self.avg_score, 1),
            "tempo_score": round(self.tempo_score, 1),
            "summary_text": self.summary_text,
            "tips": self.tips.split("|") if self.tips and "|" in self.tips else (json.loads(self.tips) if self.tips and self.tips.startswith("[") else [self.tips] if self.tips else []),
            "errors": [e.to_dict() for e in self.errors],
            "sets": [s.to_dict() for s in self.sets],
        }


class ExerciseSet(db.Model):
    __tablename__ = "exercise_sets"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("sessions.id"), nullable=False)
    set_number = db.Column(db.Integer, default=1)
    completed_reps = db.Column(db.Integer, default=0)
    set_form_score = db.Column(db.Float, default=0.0)
    tempo_consistency = db.Column(db.Float, default=0.0)

    reps = db.relationship("RepRecord", backref="set_record", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "set_number": self.set_number,
            "completed_reps": self.completed_reps,
            "set_form_score": round(self.set_form_score, 1),
            "tempo_consistency": round(self.tempo_consistency, 1),
            "reps": [r.to_dict() for r in self.reps]
        }


class RepRecord(db.Model):
    __tablename__ = "rep_records"

    id = db.Column(db.Integer, primary_key=True)
    set_id = db.Column(db.Integer, db.ForeignKey("exercise_sets.id"), nullable=False)
    rep_number = db.Column(db.Integer, default=1)
    duration_seconds = db.Column(db.Float, default=0.0)
    form_score = db.Column(db.Float, default=0.0)
    eccentric_seconds = db.Column(db.Float, default=0.0)
    pause_seconds = db.Column(db.Float, default=0.0)
    concentric_seconds = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            "rep_number": self.rep_number,
            "duration_seconds": round(self.duration_seconds, 2),
            "form_score": round(self.form_score, 1),
            "tempo": {
                "eccentric": round(self.eccentric_seconds, 2),
                "pause": round(self.pause_seconds, 2),
                "concentric": round(self.concentric_seconds, 2),
            }
        }


class SessionError(db.Model):
    __tablename__ = "session_errors"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("sessions.id"), nullable=False)
    joint = db.Column(db.String(80))
    direction = db.Column(db.String(255))
    severity = db.Column(db.String(20))
    count = db.Column(db.Integer, default=1)

    def to_dict(self):
        return {
            "joint": self.joint,
            "direction": self.direction,
            "severity": self.severity,
            "count": self.count
        }
