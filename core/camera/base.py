"""
Camera device abstraction and swappable backends.
"""
from abc import ABC, abstractmethod
from typing import Optional, Tuple
import numpy as np


class CameraDevice(ABC):
    @abstractmethod
    def open(self) -> bool:
        """Open the camera resource."""
        pass

    @abstractmethod
    def read(self) -> Tuple[bool, Optional[np.ndarray], float]:
        """
        Reads next frame.
        Returns: (success: bool, frame_rgb: np.ndarray, timestamp_ms: float)
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Release camera resource."""
        pass

    @abstractmethod
    def is_opened(self) -> bool:
        """Check if camera is active."""
        pass
