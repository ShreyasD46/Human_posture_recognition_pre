"""
Hold Timer & Breathing Pacer for Isometric Postures (Yoga poses & Sitting posture).
"""
import time
import math
from typing import Dict, Any, Optional
from core.models.exercise_spec import ExerciseSpec, HoldRules


class HoldTimer:
    """
    Tracks sustained hold duration, stability streaks, breathing cadence,
    and alerts for prolonged bad ergonomic posture.
    """

    def __init__(self, spec: ExerciseSpec):
        self.spec = spec
        self.rules = spec.hold_rules or HoldRules()

        self.target_hold_seconds: float = self.rules.hold_time_target_seconds
        self.breathing_pace_seconds: float = self.rules.breathing_pace_seconds
        self.max_bad_posture_seconds: float = self.rules.max_bad_posture_seconds

        # Continuous accumulation
        self.good_hold_seconds: float = 0.0
        self.bad_posture_seconds: float = 0.0
        self.current_streak_frames: int = 0
        self.max_streak_frames: int = 0

        self.start_time: float = time.time()
        self.last_update_time: float = time.time()
        self.is_completed: bool = False
        self.alert_triggered: bool = False

    def reset(self):
        self.good_hold_seconds = 0.0
        self.bad_posture_seconds = 0.0
        self.current_streak_frames = 0
        self.max_streak_frames = 0
        self.start_time = time.time()
        self.last_update_time = time.time()
        self.is_completed = False
        self.alert_triggered = False

    def process_frame(self, is_correct: bool, now: Optional[float] = None) -> Dict[str, Any]:
        """
        Updates hold time based on alignment validity this frame.
        """
        if now is None:
            now = time.time()

        dt = max(0.0, min(1.0, now - self.last_update_time))
        self.last_update_time = now

        if is_correct:
            self.good_hold_seconds += dt
            self.current_streak_frames += 1
            if self.current_streak_frames > self.max_streak_frames:
                self.max_streak_frames = self.current_streak_frames
        else:
            self.bad_posture_seconds += dt
            self.current_streak_frames = 0

        if self.good_hold_seconds >= self.target_hold_seconds:
            self.is_completed = True

        if self.bad_posture_seconds >= self.max_bad_posture_seconds:
            self.alert_triggered = True

        # Breathing cycle calculation: sine wave [0, 1]
        cycle_time = (now - self.start_time) % (2.0 * self.breathing_pace_seconds)
        if cycle_time < self.breathing_pace_seconds:
            breath_phase = "inhale"
            breath_progress = cycle_time / self.breathing_pace_seconds
        else:
            breath_phase = "exhale"
            breath_progress = (cycle_time - self.breathing_pace_seconds) / self.breathing_pace_seconds

        progress_pct = min(100.0, (self.good_hold_seconds / max(self.target_hold_seconds, 1.0)) * 100.0)

        return {
            "good_hold_seconds": round(self.good_hold_seconds, 1),
            "bad_posture_seconds": round(self.bad_posture_seconds, 1),
            "target_hold_seconds": self.target_hold_seconds,
            "hold_progress_pct": round(progress_pct, 1),
            "is_completed": self.is_completed,
            "alert_triggered": self.alert_triggered,
            "breath_phase": breath_phase,
            "breath_progress": round(breath_progress, 2),
            "pacing_guide": self.rules.pacing_guide,
        }
