"""Gesture classification for Nebula Interface.

The classifier combines deterministic pose scoring with an optional ML hook.
It is intentionally designed to be explainable, testable, and easy to extend.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional

from config import SystemMode


@dataclass(frozen=True)
class GestureDecision:
    label: str
    confidence: float
    source: str
    reason: str = ""
    scores: Dict[str, float] = field(default_factory=dict)


class GestureClassifier:
    AVAILABLE_GESTURES = ("FIST", "ONE", "PEACE", "OPEN", "PINCH_READY")

    def __init__(self, config, ml_model: Optional[Any] = None):
        gestures_cfg = config.data.get("gestures", {})
        ai_cfg = config.data.get("ai", {})
        self.ml_model = ml_model
        self.min_action_confidence = float(
            gestures_cfg.get("min_action_confidence", 0.72)
        )
        self.min_motion_confidence = float(
            gestures_cfg.get("motion_confidence_threshold", 0.7)
        )
        self.pinch_threshold = float(gestures_cfg.get("pinch_ready_threshold", 0.22))
        self.enable_motion_gestures = bool(
            gestures_cfg.get("enable_motion_gestures", False)
        )
        self.ml_enabled = bool(ai_cfg.get("enabled", True)) and ml_model is not None
        self.ml_min_confidence = float(ai_cfg.get("min_confidence", 0.78))
        self.ml_override_boost = float(ai_cfg.get("override_boost", 0.12))
        self.min_margin = float(ai_cfg.get("min_margin", 0.08))
        self.decision_history: Deque[str] = deque(
            maxlen=int(gestures_cfg.get("history_length", 7))
        )

    def classify(
        self,
        hand_data: Dict[str, Any],
        motion_gesture: Optional[str] = None,
        motion_confidence: float = 0.0,
    ) -> GestureDecision:
        features = hand_data.get("features") or {}
        finger_scores = self._finger_scores(hand_data, features)
        pinch = float(features.get("normalized_pinch", 1.0))
        openness = float(features.get("hand_openness", 0.0))
        grab_strength = float(features.get("grab_strength", 0.0))
        thumb_angle = float(features.get("thumb_angle", 0.0)) / 180.0

        scores = self._score_candidates(
            finger_scores=finger_scores,
            pinch=pinch,
            openness=openness,
            grab_strength=grab_strength,
            thumb_angle=thumb_angle,
        )

        rule_label = max(scores, key=scores.get)
        rule_confidence = self._refine_rule_confidence(
            rule_label,
            scores[rule_label],
            finger_scores,
            pinch,
            openness,
            grab_strength,
        )

        ml_decision = self._predict_ml(hand_data)
        if motion_gesture and motion_confidence >= self.min_motion_confidence:
            decision = GestureDecision(
                label=motion_gesture,
                confidence=float(motion_confidence),
                source="motion",
                reason="motion history exceeded threshold",
                scores=scores,
            )
            self._remember(decision.label)
            return decision

        if (
            ml_decision
            and ml_decision.confidence
            >= self.ml_min_confidence + self.ml_override_boost
        ):
            self._remember(ml_decision.label)
            return GestureDecision(
                label=ml_decision.label,
                confidence=ml_decision.confidence,
                source="ml",
                reason="ml override",
                scores=scores,
            )

        if ml_decision and ml_decision.label == rule_label:
            confidence = max(rule_confidence, ml_decision.confidence)
            decision = GestureDecision(
                label=rule_label,
                confidence=confidence,
                source="consensus",
                reason="rule and ml agreed",
                scores=scores,
            )
            self._remember(decision.label)
            return decision

        if rule_confidence >= self.min_action_confidence:
            decision = GestureDecision(
                label=rule_label,
                confidence=rule_confidence,
                source="rule",
                reason="rule score passed threshold",
                scores=scores,
            )
            self._remember(decision.label)
            return decision

        if ml_decision and ml_decision.confidence >= self.ml_min_confidence:
            self._remember(ml_decision.label)
            return ml_decision

        return GestureDecision(
            label="NO_ACTION",
            confidence=0.0,
            source="rejected",
            reason="no gesture exceeded threshold",
            scores=scores,
        )

    def classify_mode(self, gesture: str) -> Optional[SystemMode]:
        mapping = {
            "PEACE": SystemMode.LIGHTING,
            "FIST": SystemMode.IDLE,
            "OPEN": SystemMode.MEDIA,
            "ONE": SystemMode.MOUSE,
            "SWIPE_RIGHT": SystemMode.LIGHTING,
            "SWIPE_LEFT": SystemMode.MOUSE,
            "SWIPE_UP": SystemMode.MEDIA,
            "SWIPE_DOWN": SystemMode.IDLE,
        }
        return mapping.get(gesture)

    def _score_candidates(
        self,
        *,
        finger_scores: List[float],
        pinch: float,
        openness: float,
        grab_strength: float,
        thumb_angle: float,
    ) -> Dict[str, float]:
        thumb, index, middle, ring, pinky = finger_scores
        pinch_strength = max(0.0, 1.0 - (pinch / max(self.pinch_threshold, 1e-6)))
        open_digits = (index + middle + ring + pinky) / 4.0
        finger_sum = sum(finger_scores)

        scores = {
            "FIST": 0.45 * grab_strength
            + 0.35 * (1.0 - open_digits)
            + 0.20 * (1.0 - openness),
            "ONE": 0.60 * index
            + 0.20 * (1.0 - middle)
            + 0.10 * (1.0 - ring)
            + 0.10 * (1.0 - pinky),
            "PEACE": 0.40 * index
            + 0.40 * middle
            + 0.10 * (1.0 - ring)
            + 0.10 * (1.0 - pinky),
            "OPEN": 0.55 * openness + 0.25 * open_digits + 0.20 * (1.0 - grab_strength),
            "PINCH_READY": 0.60 * pinch_strength + 0.20 * thumb + 0.20 * index,
        }

        if thumb_angle > 0.55:
            scores["OPEN"] += 0.05
            scores["PINCH_READY"] += 0.05

        # Small penalties to keep contradictory poses from winning too easily.
        if finger_sum > 1.25:
            scores["FIST"] *= 0.75
        if finger_sum < 3.1:
            scores["OPEN"] *= 0.80
        if openness > 0.8:
            scores["ONE"] *= 0.85
            scores["PEACE"] *= 0.85
        if pinch > self.pinch_threshold * 1.5:
            scores["PINCH_READY"] *= 0.65

        return {label: max(0.0, min(1.0, value)) for label, value in scores.items()}

    def _refine_rule_confidence(
        self,
        label: str,
        score: float,
        finger_scores: List[float],
        pinch: float,
        openness: float,
        grab_strength: float,
    ) -> float:
        confidence = float(score)
        if label == "FIST":
            confidence = max(confidence, 0.85 * (1.0 - openness) + 0.15 * grab_strength)
        elif label == "OPEN":
            confidence = max(confidence, 0.65 * openness + 0.35 * (1.0 - grab_strength))
        elif label == "PINCH_READY":
            confidence = max(
                confidence, 1.0 - (pinch / max(self.pinch_threshold, 1e-6))
            )
        elif label in {"ONE", "PEACE"}:
            confidence = max(confidence, sum(finger_scores[1:3]) / 2.0)
        return max(0.0, min(1.0, confidence))

    def _predict_ml(self, hand_data: Dict[str, Any]) -> Optional[GestureDecision]:
        if not self.ml_enabled:
            return None

        try:
            label, confidence = self.ml_model.predict(hand_data)
        except Exception:
            return None

        if not label:
            return None

        return GestureDecision(
            label=str(label),
            confidence=float(confidence),
            source="ml",
            reason="ml model prediction",
            scores={},
        )

    def _finger_scores(
        self, hand_data: Dict[str, Any], features: Dict[str, Any]
    ) -> List[float]:
        scores = features.get("finger_extension_scores") or []
        if len(scores) == 5:
            return [float(value) for value in scores]

        fingers = hand_data.get("fingers_up") or [0, 0, 0, 0, 0]
        if len(fingers) != 5:
            return [0.0] * 5
        return [float(value) for value in fingers]

    def _remember(self, label: str) -> None:
        self.decision_history.append(label)
