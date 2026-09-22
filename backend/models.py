from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email}


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    pose_name = db.Column(db.String(80), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    hold_time_seconds = db.Column(db.Float, default=0)
    accuracy_pct = db.Column(db.Float, default=0)
    avg_score = db.Column(db.Float, default=0)          # Phase 1: weighted composite score average
    summary_text = db.Column(db.Text)                   # AI agent report
    tips = db.Column(db.Text)                           # AI agent tips (joined by |)

    errors = db.relationship("SessionError", backref="session", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "pose_name": self.pose_name,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "hold_time_seconds": self.hold_time_seconds,
            "accuracy_pct": self.accuracy_pct,
            "avg_score": self.avg_score,
            "summary_text": self.summary_text,
            "tips": self.tips.split("|") if self.tips else [],
            "errors": [e.to_dict() for e in self.errors],
        }


class SessionError(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("session.id"), nullable=False)
    joint = db.Column(db.String(80))
    direction = db.Column(db.String(255))
    severity = db.Column(db.String(20))
    count = db.Column(db.Integer, default=1)

    def to_dict(self):
        return {"joint": self.joint, "direction": self.direction,
                "severity": self.severity, "count": self.count}
