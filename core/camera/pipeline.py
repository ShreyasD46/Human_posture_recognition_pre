"""
Threaded Camera Capture Pipeline with Stale-Frame Dropping (Zero Lag).
Supports Picamera2 (CSI), OpenCV (V4L2 / USB), and Mock Video files.
"""
import time
import threading
from typing import Optional, Tuple
import numpy as np

from core.camera.base import CameraDevice


class OpenCVBackend(CameraDevice):
    """USB webcam / V4L2 video capture using OpenCV."""

    def __init__(self, device_index: int = 0, width: int = 640, height: int = 480, fps: int = 30):
        self.device_index = device_index
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = None

    def open(self) -> bool:
        import cv2
        self.cap = cv2.VideoCapture(self.device_index)
        if not self.cap.isOpened():
            return False
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        return True

    def read(self) -> Tuple[bool, Optional[np.ndarray], float]:
        if not self.is_opened():
            return False, None, 0.0
        import cv2
        ret, frame_bgr = self.cap.read()
        ts = time.time() * 1000.0
        if not ret or frame_bgr is None:
            return False, None, ts
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        return True, frame_rgb, ts

    def close(self) -> None:
        if self.cap:
            self.cap.release()
            self.cap = None

    def is_opened(self) -> bool:
        return self.cap is not None and self.cap.isOpened()


class MockVideoBackend(CameraDevice):
    """Replays video files for regression testing and offline benchmarks."""

    def __init__(self, video_path: str, loop: bool = True):
        self.video_path = video_path
        self.loop = loop
        self.cap = None

    def open(self) -> bool:
        import cv2
        self.cap = cv2.VideoCapture(self.video_path)
        return self.cap.isOpened()

    def read(self) -> Tuple[bool, Optional[np.ndarray], float]:
        if not self.is_opened():
            return False, None, 0.0
        import cv2
        ret, frame_bgr = self.cap.read()
        ts = time.time() * 1000.0
        if not ret or frame_bgr is None:
            if self.loop:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame_bgr = self.cap.read()
                if not ret or frame_bgr is None:
                    return False, None, ts
            else:
                return False, None, ts
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        return True, frame_rgb, ts

    def close(self) -> None:
        if self.cap:
            self.cap.release()
            self.cap = None

    def is_opened(self) -> bool:
        return self.cap is not None and self.cap.isOpened()


class Picamera2Backend(CameraDevice):
    """Raspberry Pi Camera Module 3 (CSI) backend via libcamera / Picamera2."""

    def __init__(self, width: int = 640, height: int = 480, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self.picam2 = None

    def open(self) -> bool:
        try:
            from picamera2 import Picamera2
            self.picam2 = Picamera2()
            config = self.picam2.create_preview_configuration(
                main={"size": (self.width, self.height), "format": "RGB888"}
            )
            self.picam2.configure(config)
            self.picam2.start()
            return True
        except Exception:
            return False

    def read(self) -> Tuple[bool, Optional[np.ndarray], float]:
        if not self.is_opened():
            return False, None, 0.0
        try:
            frame_rgb = self.picam2.capture_array("main")
            ts = time.time() * 1000.0
            return True, frame_rgb, ts
        except Exception:
            return False, None, 0.0

    def close(self) -> None:
        if self.picam2:
            try:
                self.picam2.stop()
            except Exception:
                pass
            self.picam2 = None

    def is_opened(self) -> bool:
        return self.picam2 is not None


class ThreadedCameraPipeline:
    """
    Asynchronous Threaded Frame Capture Pipeline.
    Producer thread reads hardware camera continuously.
    Consumer (inference) always pops the freshest available frame.
    Stale queued frames are automatically overwritten/dropped.
    """

    def __init__(self, device: CameraDevice):
        self.device = device
        self._latest_frame: Optional[np.ndarray] = None
        self._latest_ts: float = 0.0
        self._new_frame_event = threading.Event()
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Statistics
        self.total_captured: int = 0
        self.total_dropped: int = 0

    def start(self) -> bool:
        if not self.device.open():
            return False
        self._running = True
        self._thread = threading.Thread(target=self._capture_worker, daemon=True)
        self._thread.start()
        return True

    def _capture_worker(self):
        while self._running:
            success, frame, ts = self.device.read()
            if success and frame is not None:
                with self._lock:
                    if self._new_frame_event.is_set():
                        # Previous frame was not read before new frame arrived -> stale frame dropped!
                        self.total_dropped += 1
                    self._latest_frame = frame
                    self._latest_ts = ts
                    self._new_frame_event.set()
                self.total_captured += 1
            else:
                time.sleep(0.01)

    def get_latest_frame(self, timeout: float = 0.5) -> Tuple[bool, Optional[np.ndarray], float]:
        """Pops the freshest frame, resetting the event."""
        if not self._new_frame_event.wait(timeout):
            return False, None, 0.0

        with self._lock:
            frame = self._latest_frame
            ts = self._latest_ts
            self._new_frame_event.clear()
        return True, frame, ts

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self.device.close()
