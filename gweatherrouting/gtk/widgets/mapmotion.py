"""Time-based map motion, independent of GTK and display refresh rate."""

import math
from collections import deque
from dataclasses import dataclass


@dataclass
class ZoomAnimation:
    start: float
    target: float
    started_at: float
    anchor: tuple
    pointer: tuple
    duration: float = 0.20

    def value_at(self, now):
        progress = max(0.0, min(1.0, (now - self.started_at) / self.duration))
        eased = 1 - (1 - progress) ** 3
        return self.start + (self.target - self.start) * eased, progress >= 1


class DragVelocity:
    def __init__(self):
        self.samples: deque[tuple[float, float, float]] = deque()

    def add(self, now, x, y):
        self.samples.append((now, x, y))
        while len(self.samples) > 1 and self.samples[0][0] < now - 0.10:
            self.samples.popleft()

    def release(self, now, x, y):
        if len(self.samples) < 2 or now - self.samples[-1][0] > 0.06:
            return 0.0, 0.0
        self.add(now, x, y)
        start, end = self.samples[0], self.samples[-1]
        elapsed = end[0] - start[0]
        distance = math.hypot(end[1] - start[1], end[2] - start[2])
        if elapsed < 0.01 or distance < 4:
            return 0.0, 0.0
        vx, vy = (end[1] - start[1]) / elapsed, (end[2] - start[2]) / elapsed
        limit = min(1.0, 1400 / math.hypot(vx, vy))
        return vx * limit, vy * limit


class PanInertia:
    def __init__(self, vx, vy):
        self.vx, self.vy = vx, vy

    @property
    def active(self):
        return math.hypot(self.vx, self.vy) >= 8

    def step(self, seconds):
        decay = math.exp(-seconds / 0.16)
        dx, dy = self.vx * 0.16 * (1 - decay), self.vy * 0.16 * (1 - decay)
        self.vx *= decay
        self.vy *= decay
        return dx, dy
