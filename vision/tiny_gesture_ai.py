import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class TinyGestureAI:
    """Lightweight local prototype-based classifier for gesture refinement."""

    def __init__(self, config):
        ai_cfg = config.data.get("ai", {})
        gestures_cfg = config.data.get("gestures", {})
        self.enabled = bool(ai_cfg.get("enabled", True))
        self.min_confidence = float(ai_cfg.get("min_confidence", 0.78))
        self.override_boost = float(ai_cfg.get("override_boost", 0.12))
        self.min_margin = float(ai_cfg.get("min_margin", 0.08))
        self.weights = [1.6, 1.6, 1.6, 1.4, 1.4, 1.2, 1.0, 1.0, 0.7]
        self.prototype_path = Path(
            gestures_cfg.get(
                "calibration_prototype_path", "configs/calibration_prototypes.json"
            )
        )
        self.vector_space = "features"

        # Prototypes are normalized and intentionally small for fast local inference.
        self.prototypes: Dict[str, List[float]] = {
            "FIST": [0, 0, 0, 0, 0, 0.90, 0.90, 0.10, 0.15],
            "ONE": [0, 1, 0, 0, 0, 0.55, 0.30, 0.45, 0.40],
            "PEACE": [0, 1, 1, 0, 0, 0.45, 0.20, 0.65, 0.45],
            "OPEN": [1, 1, 1, 1, 1, 0.75, 0.05, 0.95, 0.60],
            "PINCH_READY": [1, 1, 0, 0, 0, 0.15, 0.35, 0.40, 0.55],
        }
        self._load_calibration_prototypes()

    def _load_calibration_prototypes(self):
        if not self.prototype_path.exists():
            return

        try:
            with open(self.prototype_path, "r", encoding="utf-8") as file_handle:
                payload = json.load(file_handle)

            labels = payload.get("labels", {})
            loaded = {}
            vector_length = None
            for label, data in labels.items():
                prototype = data.get("prototype") or []
                if not prototype:
                    continue
                loaded[label] = [float(value) for value in prototype]
                vector_length = len(prototype)

            if loaded:
                self.prototypes = loaded
                self.vector_space = "landmark_vector"
                self.weights = [1.0] * (
                    vector_length or len(next(iter(loaded.values())))
                )
        except Exception:
            # Fallback stays active when calibration data is absent or invalid.
            return

    def _build_vector(self, hand_data: dict) -> Optional[List[float]]:
        features = hand_data.get("features") or {}
        fingers = (
            features.get("finger_extension_scores")
            or hand_data.get("fingers_up")
            or [0, 0, 0, 0, 0]
        )
        if len(fingers) != 5:
            return None

        landmark_vector = features.get("landmark_vector") or []
        normalized_pinch = float(features.get("normalized_pinch", 1.0))
        grab_strength = float(features.get("grab_strength", 0.0))
        hand_openness = float(features.get("hand_openness", 0.0))
        thumb_angle = float(features.get("thumb_angle", 0.0)) / 180.0

        if self.vector_space == "landmark_vector" and landmark_vector:
            return [float(value) for value in landmark_vector]

        return [
            float(fingers[0]),
            float(fingers[1]),
            float(fingers[2]),
            float(fingers[3]),
            float(fingers[4]),
            max(0.0, min(1.0, normalized_pinch)),
            max(0.0, min(1.0, grab_strength)),
            max(0.0, min(1.0, hand_openness)),
            max(0.0, min(1.0, thumb_angle)),
        ]

    def _distance(self, a: List[float], b: List[float]) -> float:
        weights = self.weights if len(self.weights) == len(a) else [1.0] * len(a)
        return math.sqrt(sum(w * ((x - y) ** 2) for x, y, w in zip(a, b, weights)))

    def predict(self, hand_data: dict) -> Tuple[Optional[str], float]:
        if not self.enabled:
            return None, 0.0

        vector = self._build_vector(hand_data)
        if vector is None:
            return None, 0.0

        distances = []
        for label, proto in self.prototypes.items():
            dist = self._distance(vector, proto)
            distances.append((label, dist))

        distances.sort(key=lambda item: item[1])
        best_label, best_dist = distances[0]
        second_dist = distances[1][1] if len(distances) > 1 else best_dist + 1e-6

        margin = max(0.0, second_dist - best_dist)
        if margin < self.min_margin:
            return None, 0.0

        confidence = max(0.0, min(1.0, second_dist / (best_dist + second_dist + 1e-6)))

        if confidence < self.min_confidence:
            return None, 0.0

        return best_label, confidence
