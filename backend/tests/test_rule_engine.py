"""
Regression tests for the pose rule engine.

Run with:  pytest backend/tests/ -v
           (from the repo root, with backend/ on sys.path)

These tests lock in the core behaviour of PoseEvaluator.evaluate() so
any future change to scoring, weights, or angle tolerance that accidentally
breaks pose detection is caught immediately.
"""

import sys
import os

# Ensure backend/ is on sys.path when running from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pose_engine import PoseEvaluator
from tests.fixtures.pose_samples import (
    TADASANA_CORRECT,
    TADASANA_SLOUCHED,
    TADASANA_BENT_KNEES,
    TRIKONASANA_CORRECT,
    TRIKONASANA_BENT_KNEE,
    TRIKONASANA_OCCLUDED_KNEE,
    VRIKSHASANA_CORRECT,
    VIRABHADRASANA_II_CORRECT,
    UTKATASANA_CORRECT,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def fresh_eval(pose_name, landmarks, frames=1):
    """Run the evaluator N times to get past the DEBOUNCE_FRAMES threshold."""
    ev = PoseEvaluator()
    result = None
    for _ in range(frames):
        result = ev.evaluate(pose_name, landmarks)
    return result


DEBOUNCE = 3   # keep in sync with pose_engine.DEBOUNCE_FRAMES


# ---------------------------------------------------------------------------
# ── TADASANA ────────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

class TestTadasana:
    def test_correct_passes(self):
        result = fresh_eval("tadasana", TADASANA_CORRECT)
        assert result["status"] == "correct", f"Expected correct, got errors: {result['errors']}"
        assert result["errors"] == []

    def test_correct_score_high(self):
        result = fresh_eval("tadasana", TADASANA_CORRECT)
        score = result.get("score")
        if score is not None:   # score only present after Phase 1 is wired in
            assert score >= 75, f"Expected score ≥75 for correct Tadasana, got {score}"

    def test_slouched_flags_shoulder(self):
        result = fresh_eval("tadasana", TADASANA_SLOUCHED, frames=DEBOUNCE)
        joint_names = [e["joint"] for e in result["errors"]]
        assert any("shoulder" in j for j in joint_names), (
            f"Expected shoulder error for slouched Tadasana, got joints: {joint_names}"
        )

    def test_bent_knees_flags_knee(self):
        result = fresh_eval("tadasana", TADASANA_BENT_KNEES, frames=DEBOUNCE)
        joint_names = [e["joint"] for e in result["errors"]]
        assert any("knee" in j for j in joint_names), (
            f"Expected knee error for bent-knees Tadasana, got joints: {joint_names}"
        )

    def test_correct_returns_speak_list(self):
        result = fresh_eval("tadasana", TADASANA_CORRECT)
        assert "speak" in result
        assert isinstance(result["speak"], list)


# ---------------------------------------------------------------------------
# ── TRIKONASANA ─────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

class TestTrikonasana:
    def test_correct_passes(self):
        result = fresh_eval("trikonasana", TRIKONASANA_CORRECT)
        assert result["status"] == "correct", f"Got errors: {result['errors']}"

    def test_bent_knee_flags_front_knee(self):
        result = fresh_eval("trikonasana", TRIKONASANA_BENT_KNEE, frames=DEBOUNCE)
        joint_names = [e["joint"] for e in result["errors"]]
        assert any("knee" in j for j in joint_names), (
            f"Expected front_knee error for bent-knee Trikonasana, got: {joint_names}"
        )

    def test_bent_knee_score_lower_than_correct(self):
        correct = fresh_eval("trikonasana", TRIKONASANA_CORRECT).get("score")
        bent    = fresh_eval("trikonasana", TRIKONASANA_BENT_KNEE).get("score")
        if correct is not None and bent is not None:
            assert bent < correct, (
                f"Bent-knee score ({bent}) should be lower than correct score ({correct})"
            )

    def test_occluded_knee_skipped(self):
        """When a landmark has very low visibility and confidence gating is active,
        the front_knee joint should be skipped (not produce an error for that joint)."""
        result = fresh_eval("trikonasana", TRIKONASANA_OCCLUDED_KNEE, frames=DEBOUNCE)
        # With Phase 2 gating: front_knee should not appear in errors
        # Without Phase 2: this test is advisory only (no assertion failure)
        per_joint = result.get("per_joint", {})
        if per_joint:
            assert per_joint.get("front_knee") is None, (
                "Occluded front_knee landmark should produce per_joint=None, not a score"
            )


# ---------------------------------------------------------------------------
# ── VRIKSHASANA ─────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

class TestVrikshasana:
    def test_correct_passes(self):
        result = fresh_eval("vrikshasana", VRIKSHASANA_CORRECT)
        assert result["status"] == "correct", f"Got errors: {result['errors']}"


# ---------------------------------------------------------------------------
# ── VIRABHADRASANA II ────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

class TestVirabhadrasanaII:
    def test_correct_passes(self):
        result = fresh_eval("virabhadrasana_ii", VIRABHADRASANA_II_CORRECT)
        assert result["status"] == "correct", f"Got errors: {result['errors']}"


# ---------------------------------------------------------------------------
# ── UTKATASANA ──────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

class TestUtkatasana:
    def test_correct_passes(self):
        result = fresh_eval("utkatasana", UTKATASANA_CORRECT)
        assert result["status"] == "correct", f"Got errors: {result['errors']}"


# ---------------------------------------------------------------------------
# ── Unknown / edge cases ────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_unknown_pose_returns_error_status(self):
        ev = PoseEvaluator()
        result = ev.evaluate("gandalf_pose", TADASANA_CORRECT)
        assert result["status"] == "error"

    def test_empty_landmarks_does_not_crash(self):
        ev = PoseEvaluator()
        result = ev.evaluate("tadasana", [])
        # Should return a result dict without raising
        assert isinstance(result, dict)

    def test_too_few_landmarks_does_not_crash(self):
        ev = PoseEvaluator()
        result = ev.evaluate("tadasana", [{"x": 0.5, "y": 0.5, "visibility": 0.9}] * 10)
        assert isinstance(result, dict)

    def test_result_always_has_required_keys(self):
        ev = PoseEvaluator()
        result = ev.evaluate("tadasana", TADASANA_CORRECT)
        for key in ("status", "errors", "speak"):
            assert key in result, f"Missing key: {key}"
