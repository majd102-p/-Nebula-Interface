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
        fingers = hand_data["fingers_up"]
        count = sum(fingers)
        features = hand_data.get("features", {})
        normalized_pinch = features.get("normalized_pinch", 1.0) if features else 1.0

        is_pinch = (
            normalized_pinch < self.pinch_threshold
            and fingers[0] == 1
            and fingers[1] == 1
            and count <= 3
        )
        rule_score = 0.0
        if is_pinch:
            rule_gesture = "PINCH_READY"
            rule_score = max(
                0.0, 1.0 - (normalized_pinch / max(self.pinch_threshold, 1e-6))
            )
        elif count == 0:
            rule_gesture = "FIST"
            rule_score = 0.95
        elif count == 2 and fingers[1] and fingers[2] and not fingers[0]:
            rule_gesture = "PEACE"
            rule_score = 0.86
        elif count >= 4:
            rule_gesture = "OPEN"
            rule_score = 0.92
        elif count == 1 and fingers[1] and not fingers[0]:
            rule_gesture = "ONE"
            rule_score = 0.82
        else:
            rule_gesture = f"{count}_FINGERS"
            rule_score = max(0.2, min(0.65, count / 5.0))

        ai_gesture, ai_confidence = self.ai_model.predict(hand_data)
        hand_data["ai_confidence"] = ai_confidence
        if motion_gesture and motion_confidence >= self.min_motion_confidence:
            return motion_gesture, motion_confidence, "motion"

        supported = {"FIST", "PEACE", "OPEN", "ONE", "PINCH_READY"}
        if rule_gesture == ai_gesture:
            return rule_gesture, max(rule_score, ai_confidence), "consensus"

        min_confidence = self.ai_model.min_confidence
        override_threshold = min_confidence + self.ai_model.override_boost

        if ai_gesture and ai_confidence >= override_threshold:
            return ai_gesture, ai_confidence, "ai"

        if rule_gesture in supported and rule_score >= self.min_action_confidence:
            if ai_gesture and ai_confidence >= min_confidence:
                if rule_gesture == "OPEN" and ai_gesture == "PINCH_READY":
                    return ai_gesture, ai_confidence, "ai"
                return rule_gesture, rule_score, "rule"
            return rule_gesture, rule_score, "rule"

        if ai_gesture and ai_confidence >= min_confidence:
            return ai_gesture, ai_confidence, "ai"

        return "NO_ACTION", 0.0, "rejected"
