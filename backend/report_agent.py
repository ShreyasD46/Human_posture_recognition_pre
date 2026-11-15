"""
Hybrid AI Session Summary Generator.
Runs 100% offline via deterministic template engine on Raspberry Pi 4B.
Optionally enhances narrative via external LLM (Anthropic / OpenAI / Gemini)
if API key and internet connectivity are configured.
"""
import os
import json
from collections import Counter
from typing import Dict, List, Any, Tuple, Optional

SAFETY_DISCLAIMER = (
    "Disclaimer: This feedback is generated automatically from computer-vision joint-angle measurements "
    "for athletic coaching only and is not medical diagnosis or advice. If you experience pain or joint "
    "discomfort, please stop immediately and consult a certified trainer or physiotherapist."
)


def _offline_deterministic_summary(
    exercise_name: str,
    category: str,
    accuracy: float,
    total_reps: int,
    hold_time: float,
    target_hold: float,
    errors: list,
    session_stats: Optional[dict] = None,
    history: Optional[list] = None
) -> Tuple[str, List[str], str]:
    """Generates deterministic, high-quality coaching feedback offline on Pi 4B."""
    stats = session_stats or {}
    avg_score = stats.get("avg_score", accuracy)
    score_trend = stats.get("score_trend", 0.0)
    worst_joint = stats.get("worst_joint")
    asymmetry = stats.get("asymmetry_delta_deg", 0.0)

    # 1. What went well (Opening narrative)
    if category == "gym":
        if total_reps > 0 and avg_score >= 80:
            narrative = f"Solid workout on {exercise_name}! You completed {total_reps} reps with strong biomechanical control and clean range of motion."
        elif total_reps > 0:
            narrative = f"Good grit on {exercise_name} completing {total_reps} reps. Focusing on form stability will unlock even greater power and safety."
        else:
            narrative = f"Completed practice session on {exercise_name}. Building movement patterns takes repetition — stay consistent."
    else:
        if avg_score >= 85 and hold_time >= target_hold:
            narrative = f"Superb alignment on {exercise_name}! You held the posture for {hold_time:.0f}s with steady balance and strong joint stability."
        elif hold_time >= target_hold * 0.7:
            narrative = f"Solid effort on {exercise_name} with {hold_time:.0f}s hold time. A few minor alignment adjustments will make this posture effortless."
        else:
            narrative = f"Good practice on {exercise_name}. Hold time ({hold_time:.0f}s) will naturally lengthen as balance and neuromuscular stability deepen."

    # 2. Top 3 Things to Fix (Actionable tips)
    tips = []
    if worst_joint:
        j_clean = worst_joint.replace("_", " ")
        tips.append(f"Primary focus joint: {j_clean}. Slow down your eccentric transition and stabilize this area first.")

    if asymmetry > 15.0:
        tips.append(f"Noticeable left/right asymmetry ({asymmetry:.0f}° delta). Focus on unilateral balance drills or dumbbell presses.")

    if score_trend < -5.0:
        tips.append("Form fatigue detected in later reps/seconds. Consider adding 15 seconds to your rest intervals.")
    elif score_trend > 5.0:
        tips.append("Great warmup effect: your alignment improved significantly as the session progressed.")

    if category == "gym" and total_reps >= 10 and avg_score >= 88:
        tips.append("Ready for progression: consider increasing weight by 2.5 kg or slowing your eccentric tempo to 3 seconds.")

    if not tips:
        tips.append("Maintain your consistent tempo and focus on deep breathing throughout every repetition.")

    # Cross-session trend comparison
    if history and len(history) >= 2:
        prev = history[-2].get("avg_score", 0)
        curr = avg_score
        diff = curr - prev
        if diff >= 3:
            tips.append(f"Progress: Your form score improved by +{diff:.1f} points compared to your last session!")
        elif diff <= -5:
            tips.append(f"Score dipped by {abs(diff):.1f} points — ensure adequate sleep and hydration before your next session.")

    return narrative, tips[:3], SAFETY_DISCLAIMER


def generate_report(
    exercise_name: str,
    accuracy: float,
    hold_time: float,
    target_hold: float,
    errors: list,
    category: str = "yoga",
    total_reps: int = 0,
    session_stats: Optional[dict] = None,
    history: Optional[list] = None
) -> Dict[str, Any]:
    """
    Public entrypoint for session report generation.
    Always produces a valid result offline.
    """
    narrative, tips, disclaimer = _offline_deterministic_summary(
        exercise_name=exercise_name,
        category=category,
        accuracy=accuracy,
        total_reps=total_reps,
        hold_time=hold_time,
        target_hold=target_hold,
        errors=errors,
        session_stats=session_stats,
        history=history
    )

    # Check for optional Anthropic / OpenAI / Gemini cloud LLM key if online
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key and os.environ.get("ENABLE_CLOUD_AI_REPORT"):
        try:
            import urllib.request
            # Send only anonymized metrics (no video, no names, no images)
            payload = json.dumps({
                "model": "claude-3-haiku-20240307",
                "max_tokens": 300,
                "messages": [{
                    "role": "user",
                    "content": f"You are an encouraging gym & yoga coach. Summarize workout metrics: Exercise: {exercise_name}, Category: {category}, Score: {accuracy}%, Reps: {total_reps}, Errors: {len(errors)}. Give 1 summary sentence and 3 bullet tips. Keep under 100 words."
                }]
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=payload,
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["content"][0]["text"]
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                if lines:
                    narrative = lines[0]
                    tips = [l.lstrip("-•*0123456789. ") for l in lines[1:4]]
        except Exception:
            # Fallback gracefully to offline template
            pass

    return {
        "summary": narrative,
        "tips": tips,
        "caveat": disclaimer,
        "avg_score": (session_stats or {}).get("avg_score", accuracy),
        "total_reps": total_reps,
        "hold_time_seconds": hold_time,
    }
