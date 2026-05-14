import time

from config import TrackingState


class FrameProcessor:
    def __init__(self, tracker, gesture_engine, hud, mqtt_manager, logger):
        self.tracker = tracker
        self.gesture_engine = gesture_engine
        self.hud = hud
        self.mqtt_manager = mqtt_manager
        self.logger = logger
        self.prev_time = time.time()

    def calculate_fps(self, current_time):
        delta = current_time - self.prev_time
        self.prev_time = current_time
        return 1 / delta if delta > 0 else 0

    def update_tracking_state(self, hand_data):
        if hand_data["gesture"] != "NO_HAND":
            self.gesture_engine.tracking_state = TrackingState.HAND_TRACKING
        else:
            self.gesture_engine.tracking_state = TrackingState.HAND_LOST

    def build_publish_payload(self, action, hand_data):
        if isinstance(action, tuple) and action[0] == "BRIGHTNESS":
            return "lighting", {
                "gesture": hand_data["gesture"],
                "mode": self.gesture_engine.current_mode.name,
                "value": int(action[1]),
                "confidence": float(hand_data["confidence"]),
            }

        return "gestures", {
            "gesture": hand_data["gesture"],
            "mode": self.gesture_engine.current_mode.name,
            "action": str(action),
        }

    def process(self, frame, runtime_state):
        processed_frame, hand_data = self.tracker.process_frame(frame)
        hand_data["fps"] = self.calculate_fps(time.time())
        runtime_state.frame_count += 1

        action, _, norm_pinch = self.gesture_engine.process(hand_data)
        brightness_preview = self.gesture_engine.get_brightness_preview(norm_pinch)

        self.update_tracking_state(hand_data)

        if action and self.mqtt_manager.connected:
            try:
                topic, payload = self.build_publish_payload(action, hand_data)
                self.mqtt_manager.publish(topic, payload)
            except Exception as exc:
                self.logger.error(f"MQTT publish error: {exc}")

        display_frame = self.hud.draw(
            processed_frame,
            hand_data,
            status={
                "system_mode": self.gesture_engine.current_mode.name,
                "tracking_state": self.gesture_engine.tracking_state.name,
                "brightness": brightness_preview,
                "motion_gesture": hand_data.get("motion_gesture"),
                "calibration_enabled": self.tracker.calibration_store.enabled,
                "calibration_label": self.tracker.calibration_store.target_label,
            },
            debug=runtime_state.debug_mode,
        )

        return display_frame
