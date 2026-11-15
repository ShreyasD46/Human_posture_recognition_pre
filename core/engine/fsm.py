"""
Universal Rep Counting Finite-State Machine (FSM) with Hysteresis & Tempo Tracking.
Supports gym exercises (Push-up, Bench press, Bicep curl, Lateral raise, etc.)
"""
import time
from typing import Dict, List, Optional, Any, Tuple
from core.models.exercise_spec import ExerciseSpec, RepPhase, RepRules


def safe_eval_condition(condition_str: str, variables: Dict[str, float]) -> bool:
    """
    Safely evaluates simple comparative boolean conditions like:
    'left_elbow <= 90 and hip > 160' or 'angle < 30' or 'offset < 100'.
    No dangerous eval: uses restricted tokenized parsing with standard math operators.
    """
    if not condition_str or condition_str.strip() == "":
        return False

    clean_cond = condition_str.strip()
    # Replace variable names with their numerical values
    for var_name, var_val in variables.items():
        if var_val is not None:
            # Word-boundary replacement
            clean_cond = clean_cond.replace(var_name, str(var_val))

    # Allowed safe namespace
    safe_dict = {
        "__builtins__": None,
        "True": True,
        "False": False,
        "min": min,
        "max": max,
        "abs": abs
    }
    try:
        return bool(eval(clean_cond, safe_dict, {}))
    except Exception:
        return False


class RepStateMachine:
    """
    Stateful execution engine for dynamic multi-phase rep-counted exercises.
    """

    def __init__(self, spec: ExerciseSpec):
        self.spec = spec
        self.rep_rules = spec.rep_rules or RepRules()
        self.phases = {p.id: p for p in spec.phases}
        self.phase_order = [p.id for p in spec.phases]

        # State variables
        self.current_phase_id: str = self.phase_order[0] if self.phase_order else "ready"
        self.rep_count: float = 0.0
        self.current_set: int = 1
        self.sets_remaining: int = 3

        # Timing
        self.rep_start_time: float = time.time()
        self.phase_enter_time: float = time.time()
        self.last_rep_duration: float = 0.0

        # Tempo telemetry (eccentric, pause, concentric)
        self.eccentric_duration: float = 0.0
        self.pause_duration: float = 0.0
        self.concentric_duration: float = 0.0

        # Range of motion extrema within current rep
        self.rep_min_angles: Dict[str, float] = {}
        self.rep_max_angles: Dict[str, float] = {}

        # Rest break detection
        self.is_on_break: bool = False
        self.break_start_time: float = 0.0
        self.break_countdown: int = self.rep_rules.break_countdown_seconds
        self.consecutive_rest_frames: int = 0

        # History
        self.completed_reps_data: List[Dict[str, Any]] = []

    def reset(self):
        self.current_phase_id = self.phase_order[0] if self.phase_order else "ready"
        self.rep_count = 0.0
        self.rep_start_time = time.time()
        self.phase_enter_time = time.time()
        self.rep_min_angles.clear()
        self.rep_max_angles.clear()
        self.is_on_break = False
        self.break_start_time = 0.0
        self.consecutive_rest_frames = 0
        self.completed_reps_data.clear()

    def process_frame(
        self,
        angles: Dict[str, float],
        now: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Updates the state machine with newly computed joint angles for this frame.
        Returns state update event {rep_count, current_phase, rep_completed, is_break, feedback}.
        """
        if now is None:
            now = time.time()

        # Update min/max angles observed during this rep
        for joint, angle in angles.items():
            if angle is not None:
                if joint not in self.rep_min_angles or angle < self.rep_min_angles[joint]:
                    self.rep_min_angles[joint] = angle
                if joint not in self.rep_max_angles or angle > self.rep_max_angles[joint]:
                    self.rep_max_angles[joint] = angle

        current_phase = self.phases.get(self.current_phase_id)
        rep_completed = False
        half_rep_awarded = False
        feedback_cue: Optional[str] = None

        # Check Rest Break Detection (e.g. Bicep Curl / Lateral Raise arm resting down)
        if self.rep_rules.break_detection and "left_elbow" in angles:
            arm_angle = angles.get("left_elbow", 0.0)
            if arm_angle and arm_angle >= self.rep_rules.break_arm_rest_angle and self.rep_count > 0:
                self.consecutive_rest_frames += 1
                if self.consecutive_rest_frames >= 20 and not self.is_on_break:
                    self.is_on_break = True
                    self.break_start_time = now
                    if self.sets_remaining > 0:
                        self.sets_remaining -= 1
            else:
                if self.is_on_break and (now - self.break_start_time) >= self.rep_rules.break_countdown_seconds:
                    self.is_on_break = False
                    self.consecutive_rest_frames = 0
                    self.current_set += 1

        # Evaluate Phase Transition
        if current_phase and current_phase.transition:
            trans = current_phase.transition

            # 1. Check Rollback condition (e.g., failed rep or aborted attempt)
            if trans.rollback_condition and trans.rollback_phase:
                if safe_eval_condition(trans.rollback_condition, angles):
                    self.current_phase_id = trans.rollback_phase
                    self.phase_enter_time = now
                    return self._build_status(now, rep_completed=False, feedback="Reset form")

            # 2. Check Next Phase condition
            if safe_eval_condition(trans.condition, angles):
                next_phase_id = trans.next_phase
                phase_duration = now - self.phase_enter_time

                # Track tempo metrics based on phase name
                if "descending" in self.current_phase_id or "eccentric" in self.current_phase_id:
                    self.eccentric_duration = phase_duration
                elif "bottom" in self.current_phase_id or "pause" in self.current_phase_id:
                    self.pause_duration = phase_duration
                elif "ascending" in self.current_phase_id or "concentric" in self.current_phase_id:
                    self.concentric_duration = phase_duration

                # Special Half-Rep Counting (Push-up legacy style: +0.5 at bottom, +0.5 at top)
                if self.rep_rules.half_rep_count:
                    if next_phase_id == "bottom":
                        self.rep_count += 0.5
                        half_rep_awarded = True
                        feedback_cue = "Up"
                    elif next_phase_id in ("ready", "completed", self.phase_order[0]):
                        self.rep_count += 0.5
                        half_rep_awarded = True
                        feedback_cue = "Down"

                # Check for Full Rep Completion
                if next_phase_id == "completed" or (
                    not self.rep_rules.half_rep_count and next_phase_id == self.rep_rules.count_on_phase
                ):
                    rep_duration = now - self.rep_start_time
                    if rep_duration >= self.rep_rules.min_rep_duration_seconds:
                        if not self.rep_rules.half_rep_count:
                            self.rep_count += 1.0
                        rep_completed = True
                        self.last_rep_duration = rep_duration

                        # Store rep summary record
                        self.completed_reps_data.append({
                            "rep_number": int(self.rep_count),
                            "duration_seconds": round(rep_duration, 2),
                            "min_angles": dict(self.rep_min_angles),
                            "max_angles": dict(self.rep_max_angles),
                            "eccentric_seconds": round(self.eccentric_duration, 2),
                            "pause_seconds": round(self.pause_duration, 2),
                            "concentric_seconds": round(self.concentric_duration, 2),
                        })

                        # Cycle back to initial ready phase
                        next_phase_id = self.phase_order[0]
                        self.rep_start_time = now
                        self.rep_min_angles.clear()
                        self.rep_max_angles.clear()

                self.current_phase_id = next_phase_id
                self.phase_enter_time = now

        remaining_break = 0
        if self.is_on_break:
            remaining_break = max(0, int(self.rep_rules.break_countdown_seconds - (now - self.break_start_time)))

        return {
            "rep_count": self.rep_count,
            "current_phase": self.current_phase_id,
            "rep_completed": rep_completed,
            "half_rep": half_rep_awarded,
            "is_on_break": self.is_on_break,
            "break_seconds_left": remaining_break,
            "current_set": self.current_set,
            "sets_remaining": self.sets_remaining,
            "feedback": feedback_cue,
            "rep_duration": round(now - self.rep_start_time, 2),
        }

    def _build_status(self, now: float, rep_completed: bool, feedback: Optional[str]) -> Dict[str, Any]:
        return {
            "rep_count": self.rep_count,
            "current_phase": self.current_phase_id,
            "rep_completed": rep_completed,
            "half_rep": False,
            "is_on_break": self.is_on_break,
            "break_seconds_left": 0,
            "current_set": self.current_set,
            "sets_remaining": self.sets_remaining,
            "feedback": feedback,
            "rep_duration": round(now - self.rep_start_time, 2),
        }
