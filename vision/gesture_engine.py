import logging
import time

from config import SystemMode, TrackingState
from core.state_machine import GestureStateMachine
from utils.helpers import calculate_distance, clamp


class GestureEngine:
    def __init__(self, config):
        self.config = config
        self.current_mode: SystemMode = SystemMode.IDLE
        self.tracking_state: TrackingState = TrackingState.NO_HAND
        self.state_machine = GestureStateMachine(initial_mode=self.current_mode)
        self.last_event_time = 0
        self.last_continuous_time = 0
        self.last_brightness = float(
            config.data.get("gestures", {}).get("brightness_max", 100)
        )
        self.last_preview_brightness = int(self.last_brightness)

        self.EVENT_GESTURES = {"PEACE", "FIST", "OPEN", "ONE"}
        self.CONTINUOUS_GESTURES = {"PINCH_READY"}

        gestures_cfg = self.config.data.get("gestures", {})
        self.enable_motion_gestures = bool(
            gestures_cfg.get("enable_motion_gestures", False)
        )
        self.min_action_confidence = float(
            gestures_cfg.get("min_action_confidence", 0.72)
        )
        self.brightness_min_pinch = float(
            gestures_cfg.get("brightness_min_pinch", 0.18)
        )
        self.brightness_max_pinch = float(
            gestures_cfg.get("brightness_max_pinch", 0.55)
        )
        self.brightness_min = int(gestures_cfg.get("brightness_min", 10))
        self.brightness_max = int(gestures_cfg.get("brightness_max", 100))
        self.brightness_alpha = float(
            gestures_cfg.get("brightness_smoothing_alpha", 0.35)
        )
        self.brightness_deadband = int(gestures_cfg.get("brightness_deadband", 3))

    def is_cooldown_ready(self, is_event=True):
        cooldown = (
            self.config.data["gestures"]["cooldown_event"]
            if is_event
            else self.config.data["gestures"]["cooldown_continuous"]
        )
        last_time = self.last_event_time if is_event else self.last_continuous_time
        return time.time() - last_time >= cooldown

    def get_normalized_pinch(self, pinch_distance, landmarks, features):
        if features and "normalized_pinch" in features:
            return features["normalized_pinch"]
        return self.normalize_pinch(pinch_distance, landmarks)

    def _map_pinch_to_brightness(self, normalized_pinch):
        pinch = max(
            self.brightness_min_pinch, min(self.brightness_max_pinch, normalized_pinch)
        )
        span = max(1e-6, self.brightness_max_pinch - self.brightness_min_pinch)
        ratio = (pinch - self.brightness_min_pinch) / span
        brightness = self.brightness_max - ratio * (
            self.brightness_max - self.brightness_min
        )
        return clamp(brightness, self.brightness_min, self.brightness_max)

    def _apply_brightness_deadband(self, rounded_brightness):
        if (
            abs(rounded_brightness - int(round(self.last_brightness)))
            < self.brightness_deadband
        ):
            return int(round(self.last_brightness))
        return rounded_brightness

    def calculate_brightness(self, normalized_pinch):
        mapped = float(self._map_pinch_to_brightness(normalized_pinch))
        smoothed = self.last_brightness + self.brightness_alpha * (
            mapped - self.last_brightness
        )
        rounded = int(round(smoothed))
        self.last_brightness = smoothed
        return self._apply_brightness_deadband(rounded)

    def get_brightness_preview(self, normalized_pinch):
        if normalized_pinch <= 0:
            return self.last_preview_brightness

        self.last_preview_brightness = self._map_pinch_to_brightness(normalized_pinch)
        return self.last_preview_brightness

    def get_mode_change(self, gesture):
        next_mode = self.state_machine.transition_map.get(gesture)
        if next_mode is None:
            return None, None
        return next_mode, f"✓ Mode changed to {next_mode.name}"

    def _accept_mode_change(self, gesture):
        proposed = self.state_machine.propose(
            gesture,
            confidence=1.0,
            min_confidence=self.min_action_confidence,
        )
        if not proposed.accepted:
            return None

        committed = self.state_machine.commit(proposed)
        if committed is None:
            return None

        self.current_mode = committed
        self.last_event_time = time.time()
        _, message = self.get_mode_change(gesture)
        if message:
            logging.info(message)
        return f"MODE_CHANGED_TO_{committed.name}"

    def handle_motion_gesture(self, motion_gesture, motion_confidence):
        if not self.enable_motion_gestures:
            return None
        if not motion_gesture or motion_confidence < self.min_action_confidence:
            return None
        if not self.is_cooldown_ready(is_event=True):
            return None

        proposed = self.state_machine.propose(
            motion_gesture,
            confidence=motion_confidence,
            min_confidence=self.min_action_confidence,
        )
        if not proposed.accepted:
            return None

        committed = self.state_machine.commit(proposed)
        if committed is None:
            return None

        self.current_mode = committed
        self.last_event_time = time.time()
        _, message = self.get_mode_change(motion_gesture)
        if message:
            logging.info(message)
        return f"MODE_CHANGED_TO_{committed.name}"

    def handle_continuous_control(self, gesture, normalized_pinch):
        if gesture not in self.CONTINUOUS_GESTURES or not self.is_cooldown_ready(
            is_event=False
        ):
            return None

        self.last_continuous_time = time.time()
        if self.current_mode != SystemMode.LIGHTING or normalized_pinch <= 0:
            return None

        brightness = self.calculate_brightness(normalized_pinch)
        self.last_preview_brightness = brightness
        logging.debug(f"Brightness action: {brightness}%")
        return ("BRIGHTNESS", brightness)

    def handle_event_gesture(self, gesture):
        if gesture not in self.EVENT_GESTURES or not self.is_cooldown_ready(
            is_event=True
        ):
            return None

        return self._accept_mode_change(gesture)

    def normalize_pinch(self, pinch_distance, landmarks):
        """Normalize pinch distance relative to palm size"""
        if not landmarks:
            return 0.0
        try:
            wrist = landmarks.landmark[0]
            middle = landmarks.landmark[9]
            palm_size = calculate_distance(wrist, middle) + 0.001
            return pinch_distance / palm_size
        except Exception as e:
            logging.warning(f"Error normalizing pinch: {e}")
            return 0.0

    def process(self, hand_data):
        """Process gesture and return action, new_mode, and normalized_pinch"""
        gesture = hand_data.get("gesture", "NO_HAND")
        gesture_confidence = float(hand_data.get("confidence", 0.0))
        pinch_distance = hand_data.get("pinch_distance", 0.0)
        landmarks = hand_data.get("landmarks")
        features = hand_data.get("features")
        motion = {
            "gesture": hand_data.get("motion_gesture"),
            "confidence": hand_data.get("motion_confidence", 0.0),
        }

        normalized_pinch = self.get_normalized_pinch(
            pinch_distance, landmarks, features
        )
        if gesture == "NO_ACTION" or gesture_confidence < self.min_action_confidence:
            return None, None, normalized_pinch

        continuous_action = self.handle_continuous_control(gesture, normalized_pinch)
        if continuous_action:
            return continuous_action, None, normalized_pinch

        motion_gesture = motion.get("gesture")
        motion_confidence = float(motion.get("confidence", 0.0))

        motion_action = self.handle_motion_gesture(motion_gesture, motion_confidence)
        if motion_action:
            return (
                motion_action,
                (self.current_mode if motion_action else None),
                normalized_pinch,
            )

        event_action = self.handle_event_gesture(gesture)
        return (
            event_action,
            (self.current_mode if event_action else None),
            normalized_pinch,
        )
