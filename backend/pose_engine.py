"""
Unified Stateful Pose & Exercise Evaluator Engine.
Supports dynamic Gym rep counting, Yoga hold timing, and Ghost Skeleton Retargeting.
100% backward compatible with existing Sthira yoga pose tests.
"""
import sys
import os
import time

# Ensure repo root is on sys.path
_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from data.poses import POSES
from scoring import compute_pose_score
from ml.model import SthiraPhysGNN_Engine
from exercises.registry import registry
from core.models.landmark import Landmark, STANDARD_JOINT_TRIPLETS
from core.math.angles import compute_joint_angle_by_triplet
from core.engine.fsm import RepStateMachine
from core.engine.hold_timer import HoldTimer
from core.scoring.form_scorer import FormScorer
from core.ghost.retargeting import GhostSkeletonGenerator

DEBOUNCE_FRAMES = 3
VOICE_COOLDOWN_SECONDS = 2.5
_POSITIVE_INTERVAL_FRAMES = 75
_POSITIVE_CUES = [
    "Great alignment, hold it steady.",
    "Perfect form, keep breathing.",
    "You're nailing it, stay here.",
    "Beautiful posture, hold this shape.",
    "Excellent, just breathe and hold.",
]


class PoseEvaluator:
    """
    Unified evaluator: seamlessly handles both dynamic Gym exercises and Yoga postures.
    Produces live skeleton color deviations and retargeted Ghost Reference skeletons.
    """

    def __init__(self, voice_cooldown: float = VOICE_COOLDOWN_SECONDS):
        self._streaks = {}
        self._last_voice = {}
        self._correct_streak = 0
        self._positive_cue_idx = 0
        self._voice_cooldown = voice_cooldown
        self.physgnn = SthiraPhysGNN_Engine(window_size=5)

        # Plugin components
        self.active_spec = None
        self.fsm = None
        self.hold_timer = None
        self.scorer = None
        self.ghost_gen = GhostSkeletonGenerator()
        self._initialized_exercise = None

    def _init_exercise(self, exercise_id: str):
        if self._initialized_exercise == exercise_id:
            return
        spec = registry.get(exercise_id)
        self.active_spec = spec
        if spec:
            if spec.category == "gym" and spec.phases:
                self.fsm = RepStateMachine(spec)
            else:
                self.fsm = None
            if spec.hold_rules:
                self.hold_timer = HoldTimer(spec)
            else:
                self.hold_timer = None
            self.scorer = FormScorer(spec, debounce_frames=DEBOUNCE_FRAMES, voice_cooldown_seconds=self._voice_cooldown)
        self._initialized_exercise = exercise_id

    def evaluate(self, pose_name: str, landmarks: list, enable_physgnn: bool = True) -> dict:
        """
        Evaluates landmarks: list of 33 dicts {x, y, z, visibility}.
        """
        spec = registry.get(pose_name)
        has_legacy = bool(POSES.get(pose_name))
        if not spec and not has_legacy:
            return {
                "status": "error", "score": 0, "per_joint": {},
                "errors": [], "speak": [], "message": f"Unknown exercise/pose: {pose_name}",
                "telemetry": {}, "refined_landmarks": landmarks, "ghost_landmarks": []
            }

        self._init_exercise(pose_name)

        # ── 1. Sthira-PhysGNN Spatio-Temporal Graph Refinement ───────────────
        if enable_physgnn:
            phys_res = self.physgnn.process_frame(landmarks)
            active_landmarks = phys_res["refined_landmarks"]
            telemetry = phys_res["telemetry"]
        else:
            active_landmarks = landmarks
            telemetry = {
                "jitter_raw": 0.0012,
                "jitter_refined": 0.0012,
                "bone_stretching_index": 6.8,
                "inpainted_joints": 0,
                "mode": "Baseline MediaPipe",
            }

        # Convert active_landmarks to Landmark objects if dicts
        lm_objs = [Landmark.from_dict(lm) if isinstance(lm, dict) else lm for lm in active_landmarks]
        now = time.time()

        # ── 2. Evaluation Logic ─────────────────────────────────────────────
        # For legacy yoga poses in POSES, execute the exact scoring and debounce logic
        if has_legacy and (not spec or spec.category == "yoga"):
            result = compute_pose_score(pose_name, active_landmarks, use_visibility_gating=True, use_3d=True)
            raw_errors = result["errors"]
            score = result["score"]
            per_joint = result["per_joint"]

            # Debounce: only surface an error once it has persisted N frames
            bad_joint_names = {e["joint"] for e in raw_errors}
            to_speak = []

            for e in raw_errors:
                name = e["joint"]
                self._streaks[name] = self._streaks.get(name, 0) + 1
                if self._streaks[name] >= DEBOUNCE_FRAMES:
                    last = self._last_voice.get(name, 0)
                    if now - last >= self._voice_cooldown:
                        to_speak.append(e["feedback"])
                        self._last_voice[name] = now

            for name in list(self._streaks.keys()):
                if name not in bad_joint_names:
                    self._streaks[name] = 0

            is_correct = len(raw_errors) == 0
            self._correct_streak = self._correct_streak + 1 if is_correct else 0
            if is_correct and self._correct_streak > 0 and self._correct_streak % _POSITIVE_INTERVAL_FRAMES == 0:
                cue = _POSITIVE_CUES[self._positive_cue_idx % len(_POSITIVE_CUES)]
                self._positive_cue_idx += 1
                to_speak.append(cue)

            errors = raw_errors
            rep_data = None
            hold_data = None
            if self.hold_timer:
                hold_data = self.hold_timer.process_frame(is_correct, now=now)
            current_phase = "hold"
        else:
            # Dynamic Gym or custom declarative plugin
            angles = {}
            for j_name, triplet in STANDARD_JOINT_TRIPLETS.items():
                if len(lm_objs) >= 29:
                    ang = compute_joint_angle_by_triplet(lm_objs, triplet, use_3d=True)
                    if ang is not None:
                        angles[j_name] = ang

            rep_data = None
            current_phase = "ready"
            if self.fsm:
                rep_data = self.fsm.process_frame(angles, now=now)
                current_phase = rep_data["current_phase"]

            score_res = self.scorer.evaluate(angles, current_phase_id=current_phase, now=now)
            score = score_res["score"]
            per_joint = score_res["per_joint_scores"]
            errors = score_res["errors"]
            to_speak = list(score_res["speak"])
            is_correct = score_res["status"] == "correct"

            hold_data = None
            if self.hold_timer:
                hold_data = self.hold_timer.process_frame(is_correct, now=now)

            if rep_data and rep_data.get("feedback"):
                to_speak.append(rep_data["feedback"])

            self._correct_streak = self._correct_streak + 1 if is_correct else 0

        # Joint colors for skeleton overlay
        joint_colors = {}
        for j, s in per_joint.items():
            if s is None:
                joint_colors[j] = "gray"
            elif s >= 80.0:
                joint_colors[j] = "green"
            elif s >= 50.0:
                joint_colors[j] = "amber"
            else:
                joint_colors[j] = "red"

        # ── 3. Ghost Reference Skeleton Generation ──────────────────────────
        target_angles = {}
        if spec and spec.phases:
            for ph in spec.phases:
                if ph.id == current_phase and ph.target_angles:
                    target_angles = {k: v.ideal for k, v in ph.target_angles.items()}
                    break
        elif has_legacy:
            target_angles = {item["name"]: item["ideal"] for item in POSES[pose_name].get("keypoint_angles", [])}

        ghost_landmarks = []
        if len(lm_objs) >= 29:
            try:
                ghost_raw = self.ghost_gen.generate_ghost(lm_objs, target_angles)
                ghost_landmarks = [g.to_dict() for g in ghost_raw]
            except Exception:
                ghost_landmarks = []

        response = {
            "status": "correct" if is_correct else "incorrect",
            "score": score,
            "per_joint": per_joint,
            "errors": errors,
            "speak": to_speak,
            "correct_hold_streak": self._correct_streak,
            "telemetry": telemetry,
            "refined_landmarks": active_landmarks,
            "ghost_landmarks": ghost_landmarks,
            "joint_colors": joint_colors,
            "category": spec.category if spec else "yoga",
        }

        if rep_data:
            response["rep_data"] = rep_data
            response["rep_count"] = rep_data["rep_count"]
            response["current_phase"] = rep_data["current_phase"]
            response["is_on_break"] = rep_data["is_on_break"]
            response["break_seconds_left"] = rep_data["break_seconds_left"]

        if hold_data:
            response["hold_data"] = hold_data
            response["good_hold_seconds"] = hold_data["good_hold_seconds"]
            response["hold_progress_pct"] = hold_data["hold_progress_pct"]
            response["breath_phase"] = hold_data["breath_phase"]

        return response
