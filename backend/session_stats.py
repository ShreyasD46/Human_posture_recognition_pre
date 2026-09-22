"""
Session statistics aggregation and cross-session trend queries.

Used by app.py at session-end before generating the AI report.
"""
from collections import Counter
from models import db, Session, SessionError


# ---------------------------------------------------------------------------
# Per-session aggregation
# ---------------------------------------------------------------------------

def aggregate_session(session_id: int, frame_scores: list[float]) -> dict:
    """
    Compute summary stats for a completed session.

    Parameters
    ----------
    session_id  : int   – DB Session.id (already committed)
    frame_scores: list  – weighted composite score (0-100) for each evaluated frame

    Returns
    -------
    dict with keys: avg_score, score_trend, error_frequency, worst_joint
    """
    errors = SessionError.query.filter_by(session_id=session_id).all()
    error_counts = Counter(e.joint for e in errors)

    avg_score = round(sum(frame_scores) / len(frame_scores), 1) if frame_scores else 0.0

    # Trend: compare mean of first third vs last third of frames
    if len(frame_scores) >= 6:
        third = max(1, len(frame_scores) // 3)
        early_avg = sum(frame_scores[:third]) / third
        late_avg  = sum(frame_scores[-third:]) / third
        score_trend = round(late_avg - early_avg, 1)
    else:
        score_trend = None

    worst_joint = error_counts.most_common(1)[0][0] if error_counts else None

    return {
        "avg_score":       avg_score,
        "score_trend":     score_trend,   # positive = improving, negative = fatiguing
        "error_frequency": dict(error_counts),
        "worst_joint":     worst_joint,
    }


# ---------------------------------------------------------------------------
# Cross-session history
# ---------------------------------------------------------------------------

def get_pose_history(user_id: int, pose_name: str, limit: int = 10) -> list[dict]:
    """
    Return the last `limit` sessions for this user+pose, ordered most-recent-first.
    Used to build the trend narrative in the AI report.
    """
    sessions = (
        Session.query
        .filter_by(user_id=user_id, pose_name=pose_name)
        .filter(Session.avg_score.isnot(None))
        .order_by(Session.started_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "date":      s.started_at.isoformat() if s.started_at else None,
            "avg_score": s.avg_score,
        }
        for s in reversed(sessions)   # chronological order for the LLM
    ]
