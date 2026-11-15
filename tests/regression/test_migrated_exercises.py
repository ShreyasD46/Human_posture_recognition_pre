"""
Regression tests verifying all migrated Gym and Yoga exercises.
Locks in rep counts, hold timers, and form checks.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from exercises.registry import registry
from core.models.landmark import Landmark, LandmarkIndex
from core.engine.fsm import RepStateMachine
from core.engine.hold_timer import HoldTimer
from core.scoring.form_scorer import FormScorer
from core.ghost.retargeting import GhostSkeletonGenerator


def create_sample_landmarks(angles_dict=None):
    """Generates a dummy 33-landmark skeleton."""
    return [Landmark(x=0.5, y=0.5, z=0.0, visibility=0.95) for _ in range(33)]


class TestGymPushUp:
    def test_push_up_spec_loaded(self):
        spec = registry.get("push_up")
        assert spec is not None
        assert spec.category == "gym"
        assert spec.rep_rules.half_rep_count is True

    def test_push_up_rep_cycle(self):
        spec = registry.get("push_up")
        fsm = RepStateMachine(spec)

        # 1. Ready position (elbow=165, hip=170)
        res = fsm.process_frame({"left_elbow": 165.0, "left_hip": 170.0, "left_shoulder": 45.0})
        assert res["current_phase"] == "ready"
        assert res["rep_count"] == 0.0

        # 2. Descending (elbow=140)
        res = fsm.process_frame({"left_elbow": 140.0, "left_hip": 170.0, "left_shoulder": 45.0})
        assert res["current_phase"] == "descending"

        # 3. Bottom inflection (elbow=85, hip=170) -> Should award +0.5 rep!
        res = fsm.process_frame({"left_elbow": 85.0, "left_hip": 170.0, "left_shoulder": 45.0})
        assert res["current_phase"] == "bottom"
        assert res["half_rep"] is True
        assert res["rep_count"] == 0.5
        assert res["feedback"] == "Up"

        # 4. Ascending (elbow=110)
        res = fsm.process_frame({"left_elbow": 110.0, "left_hip": 170.0, "left_shoulder": 45.0})
        assert res["current_phase"] == "ascending"

        # 5. Lockout top (elbow=165, hip=170, shoulder=45) -> Should complete full rep (total 1.0)!
        res = fsm.process_frame({"left_elbow": 165.0, "left_hip": 170.0, "left_shoulder": 45.0})
        assert res["half_rep"] is True
        assert res["rep_count"] == 1.0
        assert res["feedback"] == "Down"


class TestGymBicepCurl:
    def test_bicep_curl_rep_cycle(self):
        spec = registry.get("bicep_curl")
        fsm = RepStateMachine(spec)

        # 1. Ready (arm extended > 160)
        res = fsm.process_frame({"left_elbow": 165.0, "left_shoulder": 20.0})
        assert res["current_phase"] == "ready"
        assert res["rep_count"] == 0

        # 2. Curling (elbow=120)
        res = fsm.process_frame({"left_elbow": 120.0, "left_shoulder": 20.0})
        assert res["current_phase"] == "curling"

        # 3. Peak contraction (elbow=30)
        res = fsm.process_frame({"left_elbow": 30.0, "left_shoulder": 20.0})
        assert res["current_phase"] == "contracted"

        # 4. Lowering (elbow=70)
        res = fsm.process_frame({"left_elbow": 70.0, "left_shoulder": 20.0})
        assert res["current_phase"] == "lowering"

        # 5. Fully extended (elbow=165)
        # Simulate min rep duration passing
        res = fsm.process_frame({"left_elbow": 165.0, "left_shoulder": 20.0}, now=fsm.rep_start_time + 1.2)
        assert res["rep_completed"] is True
        assert res["rep_count"] == 1.0


class TestGymLateralRaise:
    def test_lateral_raise_rep_cycle(self):
        spec = registry.get("lateral_raise")
        fsm = RepStateMachine(spec)

        # 1. Ready (arms at sides = 15 deg)
        res = fsm.process_frame({"left_shoulder_lateral": 15.0, "right_shoulder_lateral": 15.0})
        assert res["current_phase"] == "ready"

        # 2. Raising (arms = 45 deg)
        res = fsm.process_frame({"left_shoulder_lateral": 45.0, "right_shoulder_lateral": 45.0})
        assert res["current_phase"] == "raising"

        # 3. Contracted (arms = 85 deg)
        res = fsm.process_frame({"left_shoulder_lateral": 85.0, "right_shoulder_lateral": 85.0})
        assert res["current_phase"] == "contracted"

        # 4. Lowering & Return to ready
        res = fsm.process_frame({"left_shoulder_lateral": 60.0, "right_shoulder_lateral": 60.0})
        assert res["current_phase"] == "lowering"

        res = fsm.process_frame({"left_shoulder_lateral": 15.0, "right_shoulder_lateral": 15.0}, now=fsm.rep_start_time + 1.2)
        assert res["rep_completed"] is True
        assert res["rep_count"] == 1.0


class TestGymSittingPosture:
    def test_sitting_posture_hold(self):
        spec = registry.get("sitting_posture")
        timer = HoldTimer(spec)

        # Good posture: neck=25 deg, torso=5 deg
        res = timer.process_frame(is_correct=True, now=timer.start_time + 1.0)
        assert res["good_hold_seconds"] >= 0.9
        assert res["alert_triggered"] is False


class TestYogaPoses:
    def test_all_yoga_poses_loaded(self):
        yoga_poses = registry.list_all("yoga")
        ids = {p.id for p in yoga_poses}
        expected = {"tadasana", "vrikshasana", "trikonasana", "virabhadrasana_ii", "utkatasana"}
        assert expected.issubset(ids)

    def test_tadasana_form_scorer(self):
        spec = registry.get("tadasana")
        scorer = FormScorer(spec)

        # Ideal alignment
        res = scorer.evaluate({"left_knee": 178.0, "right_knee": 178.0, "left_spine": 178.0, "left_shoulder": 95.0}, current_phase_id="hold")
        assert res["status"] == "correct"
        assert res["score"] >= 90.0

        # Slouched posture error
        res = scorer.evaluate({"left_knee": 178.0, "right_knee": 178.0, "left_spine": 150.0, "left_shoulder": 95.0}, current_phase_id="hold")
        assert any(e["rule_id"] == "spine_lean" for e in res["errors"])


class TestGhostRetargeting:
    def test_ghost_skeleton_generation(self):
        generator = GhostSkeletonGenerator()
        landmarks = create_sample_landmarks()
        ghost = generator.generate_ghost(landmarks, {"left_elbow": 90.0, "left_knee": 90.0})
        assert len(ghost) == 33
        assert ghost[LandmarkIndex.LEFT_ELBOW].x != 0.0
