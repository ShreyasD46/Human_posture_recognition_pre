"""
Continuous 0–100 Biomechanical Form Scorer with Debouncing and Rate-Limited Voice Cues.
"""
import time
from typing import Dict, List, Optional, Any, Tuple
from core.models.exercise_spec import ExerciseSpec, FormRule, TargetAngle
from core.engine.fsm import safe_eval_condition


class FormScorer:
    """
    Evaluates joint deviations, calculates weighted continuous form scores (0–100),
    debounces transient glitches, and triggers rate-limited audio coaching cues.
    """

    def __init__(
        self,
        spec: ExerciseSpec,
        debounce_frames: int = 3,
        voice_cooldown_seconds: float = 2.5
    ):
        self.spec = spec
        self.debounce_frames = debounce_frames
        self.voice_cooldown_seconds = voice_cooldown_seconds

        # Error tracking
        self.error_streaks: Dict[str, int] = {}       # rule_id -> frame count
        self.last_voice_times: Dict[str, float] = {}   # rule_id -> last spoken timestamp

        # Positive reinforcement
        self.correct_hold_frames: int = 0
        self.positive_cue_index: int = 0
        self.positive_cues = [
            "Great form, keep it up!",
            "Excellent control, stay steady.",
            "Perfect alignment, breathe through it.",
            "Strong work, maintain this tempo.",
        ]

    def reset(self):
        self.error_streaks.clear()
        self.last_voice_times.clear()
        self.correct_hold_frames = 0
        self.positive_cue_index = 0

    def evaluate(
        self,
        angles: Dict[str, float],
        current_phase_id: Optional[str] = None,
        now: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluates current angles against declarative target angles and form rules.
        """
        if now is None:
            now = time.time()

        total_score = 0.0
        total_weight = 0.0
        per_joint_scores: Dict[str, Optional[float]] = {}
        active_errors: List[Dict[str, Any]] = []
        cues_to_speak: List[str] = []
        problem_joints: Dict[str, Dict[str, Any]] = {}

        # 1. Evaluate phase target angles (if available for current phase)
        target_angles: Dict[str, TargetAngle] = {}
        for phase in self.spec.phases:
            if phase.id == current_phase_id and phase.target_angles:
                target_angles = phase.target_angles
                break

        for joint_name, target in target_angles.items():
            angle_val = angles.get(joint_name)
            if angle_val is None:
                per_joint_scores[joint_name] = None
                continue

            deviation = abs(angle_val - target.ideal)
            tol = target.tolerance
            weight = target.weight

            # Continuous falloff: 0 deviation -> 1.0, deviation >= 2*tol -> 0.0
            joint_score_01 = max(0.0, 1.0 - deviation / (2.0 * tol))
            joint_score_100 = round(joint_score_01 * 100.0, 1)

            per_joint_scores[joint_name] = joint_score_100
            total_score += joint_score_01 * weight
            total_weight += weight

            if deviation > tol:
                severity = "minor" if deviation < 1.5 * tol else ("moderate" if deviation < 2.5 * tol else "major")
                problem_joints[joint_name] = {
                    "measured": round(angle_val, 1),
                    "ideal": target.ideal,
                    "deviation": round(deviation, 1),
                    "severity": severity,
                }

        # 2. Evaluate Form Rules
        active_rule_ids = set()
        for rule in self.spec.form_rules:
            # Check if rule applies to this phase
            if rule.phase and rule.phase != current_phase_id:
                continue

            # Evaluate rule condition
            is_violation = safe_eval_condition(rule.condition, angles)
            if is_violation:
                active_rule_ids.add(rule.id)
                self.error_streaks[rule.id] = self.error_streaks.get(rule.id, 0) + 1

                error_item = {
                    "rule_id": rule.id,
                    "joint": rule.joint,
                    "severity": rule.severity,
                    "feedback": rule.feedback,
                    "weight": rule.weight,
                }
                active_errors.append(error_item)

                # Penalize overall score for active form violation
                penalty = 15.0 if rule.severity == "minor" else (30.0 if rule.severity == "moderate" else 50.0)
                total_score = max(0.0, total_score - (penalty / 100.0) * rule.weight)
                total_weight += rule.weight

                # Check debounce and voice cooldown
                if self.error_streaks[rule.id] >= self.debounce_frames:
                    last_time = self.last_voice_times.get(rule.id, 0.0)
                    if now - last_time >= self.voice_cooldown_seconds:
                        cues_to_speak.append(rule.feedback)
                        self.last_voice_times[rule.id] = now
            else:
                self.error_streaks[rule.id] = 0

        # Normalization
        if total_weight > 0:
            final_score = round(min(100.0, max(0.0, (total_score / total_weight) * 100.0)), 1)
        else:
            final_score = 100.0 if not active_errors else 50.0

        is_correct = len(active_errors) == 0 and final_score >= 70.0
        if is_correct:
            self.correct_hold_frames += 1
            if self.correct_hold_frames % 75 == 0:  # ~5 seconds at 15 FPS
                p_cue = self.positive_cues[self.positive_cue_index % len(self.positive_cues)]
                self.positive_cue_index += 1
                cues_to_speak.append(p_cue)
        else:
            self.correct_hold_frames = 0

        # Build color map for joints: "green", "amber", "red", "gray"
        joint_colors: Dict[str, str] = {}
        for joint, score in per_joint_scores.items():
            if score is None:
                joint_colors[joint] = "gray"
            elif score >= 80.0:
                joint_colors[joint] = "green"
            elif score >= 50.0:
                joint_colors[joint] = "amber"
            else:
                joint_colors[joint] = "red"

        # Override for problem joints from rules
        for err in active_errors:
            j = err["joint"]
            if err["severity"] == "major":
                joint_colors[j] = "red"
            elif err["severity"] == "moderate" and joint_colors.get(j) != "red":
                joint_colors[j] = "amber"

        return {
            "score": final_score,
            "status": "correct" if is_correct else "incorrect",
            "per_joint_scores": per_joint_scores,
            "joint_colors": joint_colors,
            "problem_joints": problem_joints,
            "errors": active_errors,
            "speak": cues_to_speak,
            "correct_streak": self.correct_hold_frames,
        }
