"""
AI agent layer — runs only once, after a session ends (not per-frame),
so latency/cost don't matter here. Sends aggregated, anonymised session
stats (never raw video/keypoints) to an LLM for natural-language coaching.

If ANTHROPIC_API_KEY is not set, falls back to a deterministic templated
report so the app runs end-to-end without any API key.

Phase 3: accepts session_stats dict (with avg_score, score_trend, worst_joint)
         and history list for cross-session trend narrative.
"""
import os
import json
from collections import Counter

POSE_LABELS = {
    "tadasana": "Tadasana", "vrikshasana": "Vrikshasana", "trikonasana": "Trikonasana",
    "virabhadrasana_ii": "Warrior II", "utkatasana": "Utkatasana",
}

CLINICAL_CAVEAT = (
    "This feedback is generated automatically from joint-angle measurements and is not "
    "clinically validated — please consult a qualified yoga teacher or physiotherapist "
    "for injury concerns."
)


# ---------------------------------------------------------------------------
# Templated fallback (no API key required)
# ---------------------------------------------------------------------------

def _trend_sentence(history: list[dict]) -> str:
    """Build a trend sentence from the last N session avg_scores."""
    if len(history) < 2:
        return ""
    first_score = history[0]["avg_score"] or 0
    last_score  = history[-1]["avg_score"] or 0
    delta = last_score - first_score
    if delta >= 5:
        return f"Your score has improved by roughly {delta:.0f} points over the last {len(history)} sessions — keep at it."
    if delta <= -5:
        return f"Your composite score has dipped {abs(delta):.0f} points recently — try shorter holds and focus on form."
    return f"Your score has been consistent across the last {len(history)} sessions — a stable foundation to build from."


def _templated_report(pose_name, accuracy, hold_time, target_hold, error_counts,
                      session_stats=None, history=None):
    label = POSE_LABELS.get(pose_name, pose_name)
    avg_score = (session_stats or {}).get("avg_score")
    score_trend = (session_stats or {}).get("score_trend")

    if accuracy >= 90:
        opener = f"Strong {label} — your alignment held steady through most of the session."
    elif accuracy >= 70:
        opener = f"Solid effort on {label}, with a few recurring alignment slips worth tightening up."
    else:
        opener = f"{label} is still finding its shape — that's normal this early, keep at it."

    tips = []
    if error_counts:
        top_joint, count = error_counts.most_common(1)[0]
        tips.append(
            f"Your most frequent cue was on the {top_joint.replace('_', ' ')} — "
            f"slow down and check that alignment before you settle into the hold."
        )
    if hold_time < target_hold:
        tips.append(
            f"You held for {hold_time:.0f}s of a {target_hold}s target — "
            f"build hold time gradually rather than chasing it in one session."
        )
    if score_trend is not None and abs(score_trend) >= 5:
        if score_trend > 0:
            tips.append(f"Your form improved within this session (+{score_trend:.0f} pts) — you're warming up well.")
        else:
            tips.append(f"Your alignment drifted as the session went on ({score_trend:.0f} pts) — try shorter holds.")

    if not tips:
        tips.append("Keep this consistency and start extending your hold time.")

    # Cross-session trend sentence
    trend_note = _trend_sentence(history or [])
    if trend_note:
        tips.append(trend_note)

    return opener, tips[:3]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_report(pose_name, accuracy, hold_time, target_hold, errors,
                    session_stats=None, history=None):
    """
    Parameters
    ----------
    errors        : list of {joint, direction, severity} dicts
    session_stats : dict from session_stats.aggregate_session()  (optional)
    history       : list from session_stats.get_pose_history()   (optional)

    Returns
    -------
    dict {"summary": str, "tips": [str, ...]}
    """
    error_counts = Counter(e["joint"] for e in errors)
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        summary, tips = _templated_report(
            pose_name, accuracy, hold_time, target_hold, error_counts,
            session_stats=session_stats, history=history,
        )
        return {"summary": summary, "tips": tips, "caveat": CLINICAL_CAVEAT}

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        stats_payload = {
            "pose":                POSE_LABELS.get(pose_name, pose_name),
            "accuracy_pct":        round(accuracy, 1),
            "hold_time_seconds":   round(hold_time, 1),
            "target_hold_seconds": target_hold,
            "most_common_errors":  error_counts.most_common(3),
        }
        if session_stats:
            stats_payload["avg_score"]   = session_stats.get("avg_score")
            stats_payload["score_trend"] = session_stats.get("score_trend")
            stats_payload["worst_joint"] = session_stats.get("worst_joint")
        if history and len(history) >= 2:
            stats_payload["session_history"] = [
                {"date": h["date"], "avg_score": h["avg_score"]} for h in history[-5:]
            ]

        prompt = f"""Session stats: {json.dumps(stats_payload)}

Write a warm, concise coaching response:
1. A 1-2 sentence summary assessing this session.
2. Up to 2 short, specific, actionable tips tied to the most frequent error joint.
3. If session_history has 2+ entries, include ONE sentence noting improvement or regression.
4. Do NOT include any clinical claims — accuracy notes are fine.

Respond ONLY as JSON: {{"summary": str, "tips": [str, ...]}}"""

        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=(
                "You are a warm, concise yoga coach. Given aggregated session stats "
                "(no images or personal data), write coaching feedback. "
                "Respond ONLY as valid JSON with keys 'summary' and 'tips'."
            ),
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in msg.content if b.type == "text")
        result = json.loads(text.strip().strip("`").removeprefix("json"))
        result["caveat"] = CLINICAL_CAVEAT
        return result

    except Exception:
        summary, tips = _templated_report(
            pose_name, accuracy, hold_time, target_hold, error_counts,
            session_stats=session_stats, history=history,
        )
        return {"summary": summary, "tips": tips, "caveat": CLINICAL_CAVEAT}
