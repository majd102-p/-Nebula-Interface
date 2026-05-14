"""Small state machine helpers for gesture-driven mode transitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from config import SystemMode


@dataclass(frozen=True)
class TransitionResult:
    accepted: bool
    next_mode: SystemMode
    reason: str


class GestureStateMachine:
    def __init__(self, initial_mode: SystemMode = SystemMode.IDLE):
        self.current_mode = initial_mode
        self.transition_map: Dict[str, SystemMode] = {
            "PEACE": SystemMode.LIGHTING,
            "FIST": SystemMode.IDLE,
            "OPEN": SystemMode.MEDIA,
            "ONE": SystemMode.MOUSE,
            "SWIPE_RIGHT": SystemMode.LIGHTING,
            "SWIPE_LEFT": SystemMode.MOUSE,
            "SWIPE_UP": SystemMode.MEDIA,
            "SWIPE_DOWN": SystemMode.IDLE,
        }

    def propose(
        self, gesture: str, confidence: float, min_confidence: float
    ) -> TransitionResult:
        next_mode = self.transition_map.get(gesture)
        if next_mode is None:
            return TransitionResult(False, self.current_mode, "unsupported gesture")
        if confidence < min_confidence:
            return TransitionResult(
                False, self.current_mode, "below confidence threshold"
            )
        if gesture == "PEACE" and self.current_mode == SystemMode.LIGHTING:
            return TransitionResult(
                False, self.current_mode, "already in lighting mode"
            )
        if gesture == "OPEN" and self.current_mode != SystemMode.LIGHTING:
            return TransitionResult(
                False, self.current_mode, "open hand only toggles from lighting"
            )
        return TransitionResult(True, next_mode, "transition accepted")

    def commit(self, result: TransitionResult) -> Optional[SystemMode]:
        if not result.accepted:
            return None
        self.current_mode = result.next_mode
        return self.current_mode
