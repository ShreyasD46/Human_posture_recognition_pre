"""
One-Euro Filter implementation for real-time human landmark smoothing.
Reference: Casiez et al., "1 € Filter: A Simple Speed-based Low-pass Filter for Noisy Input in Human-Computer Interaction", CHI 2012.
"""
import math
from typing import List, Optional
from core.models.landmark import Landmark


class LowPassFilter:
    def __init__(self, alpha: float = 0.5):
        self.alpha = alpha
        self.hat_x_prev: Optional[float] = None

    def reset(self):
        self.hat_x_prev = None

    def filter(self, x: float, alpha: Optional[float] = None) -> float:
        if alpha is not None:
            self.alpha = alpha
        if self.hat_x_prev is None:
            hat_x = x
        else:
            hat_x = self.alpha * x + (1.0 - self.alpha) * self.hat_x_prev
        self.hat_x_prev = hat_x
        return hat_x


class OneEuroFilter1D:
    def __init__(self, min_cutoff: float = 1.0, beta: float = 0.007, d_cutoff: float = 1.0):
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self.x_filt = LowPassFilter()
        self.dx_filt = LowPassFilter()
        self.t_prev: Optional[float] = None

    def reset(self):
        self.x_filt.reset()
        self.dx_filt.reset()
        self.t_prev = None

    @staticmethod
    def _alpha(rate: float, cutoff: float) -> float:
        tau = 1.0 / (2.0 * math.pi * cutoff)
        te = 1.0 / rate
        return 1.0 / (1.0 + tau / te)

    def filter(self, x: float, timestamp: float) -> float:
        if self.t_prev is None:
            self.t_prev = timestamp
            return self.x_filt.filter(x, 1.0)

        dt = timestamp - self.t_prev
        self.t_prev = timestamp
        rate = 1.0 / max(dt, 1e-5)

        # Estimate derivative
        prev_x = self.x_filt.hat_x_prev if self.x_filt.hat_x_prev is not None else x
        dx = (x - prev_x) * rate
        edx = self.dx_filt.filter(dx, self._alpha(rate, self.d_cutoff))

        # Dynamic cutoff frequency
        cutoff = self.min_cutoff + self.beta * abs(edx)
        return self.x_filt.filter(x, self._alpha(rate, cutoff))


class LandmarkSmoother:
    """Smoothes a full list of 33 3D landmarks across consecutive frames."""

    def __init__(self, num_landmarks: int = 33, min_cutoff: float = 1.2, beta: float = 0.005):
        self.num_landmarks = num_landmarks
        self.filters_x = [OneEuroFilter1D(min_cutoff, beta) for _ in range(num_landmarks)]
        self.filters_y = [OneEuroFilter1D(min_cutoff, beta) for _ in range(num_landmarks)]
        self.filters_z = [OneEuroFilter1D(min_cutoff, beta) for _ in range(num_landmarks)]

    def reset(self):
        for fx in self.filters_x: fx.reset()
        for fy in self.filters_y: fy.reset()
        for fz in self.filters_z: fz.reset()

    def smooth(self, landmarks: List[Landmark], timestamp: float) -> List[Landmark]:
        smoothed: List[Landmark] = []
        for i, lm in enumerate(landmarks[:self.num_landmarks]):
            sx = self.filters_x[i].filter(lm.x, timestamp)
            sy = self.filters_y[i].filter(lm.y, timestamp)
            sz = self.filters_z[i].filter(lm.z, timestamp)
            smoothed.append(Landmark(x=sx, y=sy, z=sz, visibility=lm.visibility))
        return smoothed
