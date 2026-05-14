from core.gesture_classifier import GestureClassifier
from utils.helpers import calculate_distance

from .calibration_store import CalibrationStore
from .motion_classifier import MotionHistoryClassifier
from .smoothing import GestureSmoother
from .tiny_gesture_ai import TinyGestureAI


class HandAnalysisPipeline:
    def __init__(self, config):
        self.config = config
        gestures_cfg = config.data.get("gestures", {})
        self.smoother = GestureSmoother(
            history_length=config.data["smoothing"]["history_length"],
            confirmation_frames=config.data["smoothing"]["confirmation_frames"],
        )
        self.motion_classifier = MotionHistoryClassifier(config)
        self.calibration_store = CalibrationStore(config)
        self.ai_model = TinyGestureAI(config)
        self.classifier = GestureClassifier(config, ml_model=self.ai_model)
        self.pinch_threshold = float(gestures_cfg.get("pinch_ready_threshold", 0.22))
        self.min_action_confidence = float(
            gestures_cfg.get("min_action_confidence", 0.72)
        )
        self.min_motion_confidence = float(
            gestures_cfg.get("motion_confidence_threshold", 0.7)
        )

    def enrich(self, hand_data):
        if hand_data.get("gesture") == "NO_HAND":
            return hand_data

        motion_gesture, motion_confidence = self.motion_classifier.update(hand_data)
        hand_data["motion_gesture"] = motion_gesture
        hand_data["motion_confidence"] = motion_confidence

        self.calibration_store.capture(hand_data)
        gesture, confidence, decision_source = self._classify_gesture(
            hand_data,
            motion_gesture=motion_gesture,
            motion_confidence=motion_confidence,
        )

        hand_data["gesture"] = gesture
        hand_data["confidence"] = confidence
        hand_data["decision_source"] = decision_source

        if gesture == "NO_ACTION" or confidence < self.min_action_confidence:
            return hand_data

        stable_gesture = self.smoother.update(hand_data["gesture"])
        if stable_gesture and stable_gesture != "NO_ACTION":
            hand_data["gesture"] = stable_gesture
            hand_data["confidence"] = max(confidence, self.smoother.confidence)

        return hand_data

    def calculate_pinch_distance(self, landmarks):
        return calculate_distance(landmarks.landmark[4], landmarks.landmark[8])

    def _classify_gesture(self, hand_data, motion_gesture=None, motion_confidence=0.0):
        decision = self.classifier.classify(
            hand_data,
            motion_gesture=motion_gesture,
            motion_confidence=motion_confidence,
        )
        hand_data["ai_confidence"] = float(
            (hand_data.get("ai_confidence") or decision.confidence)
        )
        return decision.label, decision.confidence, decision.source
