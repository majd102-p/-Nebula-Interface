from collections import deque
from math import hypot


class MotionHistoryClassifier:
    def __init__(self, config):
        motion_cfg = config.data.get("gestures", {})
        self.enabled = bool(motion_cfg.get("enable_motion_gestures", False))
        self.history_length = int(motion_cfg.get("motion_history_length", 12))
        self.min_displacement = float(motion_cfg.get("motion_min_displacement", 0.18))
        self.min_axis_ratio = float(motion_cfg.get("motion_axis_ratio", 1.4))
        self.min_confidence = float(motion_cfg.get("motion_confidence_threshold", 0.7))
        self.history = deque(maxlen=max(3, self.history_length))

    def reset(self):
        self.history.clear()

    def _finger_tip(self, hand_data):
        features = hand_data.get("features") or {}
        normalized = features.get("normalized_landmarks") or []
        if len(normalized) >= 9:
            return normalized[8]

        landmarks = hand_data.get("landmarks")
        if not landmarks:
            return None

        lm = landmarks.landmark
        wrist = lm[0]
        point = lm[8]
        scale = hypot(lm[9].x - wrist.x, lm[9].y - wrist.y) or 1.0
        return ((point.x - wrist.x) / scale, (point.y - wrist.y) / scale, 0.0)

    def update(self, hand_data):
        if not self.enabled:
            return None, 0.0

        tip = self._finger_tip(hand_data)
        if tip is None:
            self.reset()
            return None, 0.0

        self.history.append(tip)
        if len(self.history) < self.history.maxlen:
            return None, 0.0

        start = self.history[0]
        end = self.history[-1]
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        abs_dx = abs(dx)
        abs_dy = abs(dy)
        displacement = hypot(dx, dy)

        if displacement < self.min_displacement:
            return None, 0.0

        if abs_dx >= abs_dy * self.min_axis_ratio:
            label = "SWIPE_RIGHT" if dx > 0 else "SWIPE_LEFT"
            confidence = min(1.0, displacement / (self.min_displacement * 2.5))
        elif abs_dy >= abs_dx * self.min_axis_ratio:
            label = "SWIPE_DOWN" if dy > 0 else "SWIPE_UP"
            confidence = min(1.0, displacement / (self.min_displacement * 2.5))
        else:
            return None, 0.0

        if confidence < self.min_confidence:
            return None, 0.0

        return label, confidence
