"""
Replay evaluation test: processes sample workout video through camera pipeline.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from core.camera.pipeline import MockVideoBackend
from core.models.landmark import Landmark
from exercises.registry import registry
from core.engine.fsm import RepStateMachine


def test_mock_video_backend_pushup():
    video_path = os.path.join(os.path.dirname(__file__), "../../vendor/gym_legacy/Push_up_output.webm")
    if not os.path.exists(video_path):
        pytest.skip(f"Sample video not found at {video_path}")

    backend = MockVideoBackend(video_path, loop=False)
    assert backend.open() is True

    frame_count = 0
    while frame_count < 30:
        ret, frame, ts = backend.read()
        if not ret or frame is None:
            break
        assert frame.shape[2] == 3  # RGB
        frame_count += 1

    backend.close()
    assert frame_count >= 10
