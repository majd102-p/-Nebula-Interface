"""Lightweight runtime telemetry for Nebula Interface."""

from __future__ import annotations

import statistics
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict


@dataclass
class PerformanceSnapshot:
    fps: float
    frame_time_ms: float
    inference_ms: float
    queue_depth: int
    dropped_frames: int
    uptime_s: float


@dataclass
class PerformanceMonitor:
    window_size: int = 60
    frame_times: Deque[float] = field(default_factory=lambda: deque(maxlen=60))
    inference_times_ms: Deque[float] = field(default_factory=lambda: deque(maxlen=60))
    _start_time: float = field(default_factory=time.perf_counter)
    _last_frame_time: float = field(default_factory=time.perf_counter)
    frame_count: int = 0
    dropped_frames: int = 0
    queue_depth: int = 0

    def mark_frame(self) -> float:
        now = time.perf_counter()
        frame_time = now - self._last_frame_time
        self._last_frame_time = now
        self.frame_times.append(frame_time)
        self.frame_count += 1
        return frame_time

    def mark_inference(self, duration_ms: float) -> None:
        self.inference_times_ms.append(float(duration_ms))

    def mark_drop(self) -> None:
        self.dropped_frames += 1

    def set_queue_depth(self, depth: int) -> None:
        self.queue_depth = max(0, int(depth))

    def snapshot(self) -> PerformanceSnapshot:
        avg_frame_time = self._mean(self.frame_times)
        fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0
        return PerformanceSnapshot(
            fps=fps,
            frame_time_ms=avg_frame_time * 1000.0,
            inference_ms=self._mean(self.inference_times_ms),
            queue_depth=self.queue_depth,
            dropped_frames=self.dropped_frames,
            uptime_s=time.perf_counter() - self._start_time,
        )

    def as_dict(self) -> Dict[str, float]:
        snap = self.snapshot()
        return {
            "fps": snap.fps,
            "frame_time_ms": snap.frame_time_ms,
            "inference_ms": snap.inference_ms,
            "queue_depth": float(snap.queue_depth),
            "dropped_frames": float(snap.dropped_frames),
            "uptime_s": snap.uptime_s,
        }

    @staticmethod
    def _mean(values) -> float:
        return float(statistics.fmean(values)) if values else 0.0
