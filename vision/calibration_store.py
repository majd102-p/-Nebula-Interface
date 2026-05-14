import csv
from pathlib import Path


class CalibrationStore:
    def __init__(self, config):
        gestures_cfg = config.data.get("gestures", {})
        self.enabled = bool(gestures_cfg.get("enable_calibration_capture", False))
        self.sample_stride = max(
            1, int(gestures_cfg.get("calibration_sample_stride", 4))
        )
        self.min_confidence = float(
            gestures_cfg.get("calibration_min_confidence", 0.65)
        )
        self.frame_index = 0
        self.target_label = None
        self.label_map = {
            "1": "FIST",
            "2": "ONE",
            "3": "PEACE",
            "4": "OPEN",
            "5": "PINCH_READY",
        }
        self.output_path = Path("configs/calibration_samples.csv")
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def set_target_label(self, key):
        self.target_label = self.label_map.get(str(key), None)
        return self.target_label

    def reset(self):
        self.frame_index = 0
        if self.output_path.exists():
            self.output_path.unlink()
        return True

    def capture(self, hand_data):
        if not self.enabled:
            return False

        self.frame_index += 1
        if self.frame_index % self.sample_stride != 0:
            return False

        features = hand_data.get("features") or {}
        landmark_vector = features.get("landmark_vector") or []
        if not landmark_vector:
            return False

        if float(hand_data.get("confidence", 0.0)) < self.min_confidence:
            return False

        label = self.target_label or hand_data.get("gesture", "UNKNOWN")

        row = [
            label,
            hand_data.get("handedness", "Unknown"),
            f"{hand_data.get('handedness_score', 0.0):.4f}",
            f"{hand_data.get('confidence', 0.0):.4f}",
            f"{hand_data.get('ai_confidence', 0.0):.4f}",
            f"{hand_data.get('motion_gesture') or ''}",
            f"{hand_data.get('motion_confidence', 0.0):.4f}",
        ] + [f"{value:.6f}" for value in landmark_vector]

        with open(self.output_path, "a", newline="", encoding="utf-8") as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow(row)

        return True
