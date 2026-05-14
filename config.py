import json
import logging
from enum import Enum
from pathlib import Path


def _deep_merge_dict(defaults, override):
    """Recursively merge defaults into override without dropping nested keys."""
    if not isinstance(defaults, dict):
        return override

    if not isinstance(override, dict):
        return defaults

    merged = dict(override)
    for key, default_value in defaults.items():
        if key not in merged:
            merged[key] = default_value
            continue
        if isinstance(default_value, dict):
            merged[key] = _deep_merge_dict(default_value, merged.get(key))
    return merged


class SystemMode(Enum):
    IDLE = 0
    LIGHTING = 1
    MEDIA = 2
    MOUSE = 3
    SECURITY = 4


class TrackingState(Enum):
    NO_HAND = 0
    HAND_TRACKING = 1
    HAND_LOST = 2
    SLEEP = 3


class Config:
    def __init__(self):
        self.config_path = Path("configs/config.json")
        self.load_config()

    def load_config(self):
        default = {
            "camera": {"width": 640, "height": 480, "fps": 30, "processing_scale": 0.4},
            "hand": {
                "max_num_hands": 1,
                "min_detection_confidence": 0.7,
                "min_tracking_confidence": 0.7,
                "thumb_open_spread_ratio": 0.44,
                "thumb_open_stretch_ratio": 0.36,
                "thumb_straight_angle_deg": 145,
                "finger_pip_straight_angle_deg": 160,
                "finger_dip_straight_angle_deg": 145,
                "finger_extension_ratio": 1.55,
                "finger_tip_margin_ratio": 0.08,
                "finger_vertical_margin": 0.015,
                "thumb_x_margin": 0.015,
                "handedness_min_score": 0.6,
            },
            "smoothing": {"history_length": 10, "confirmation_frames": 5},
            "gestures": {
                "pinch_threshold": 0.055,
                "pinch_ready_threshold": 0.22,
                "min_action_confidence": 0.72,
                "cooldown_event": 0.65,
                "cooldown_continuous": 0.08,
                "enable_motion_gestures": False,
                "motion_history_length": 12,
                "motion_min_displacement": 0.18,
                "motion_axis_ratio": 1.4,
                "motion_confidence_threshold": 0.7,
                "enable_calibration_capture": False,
                "calibration_sample_stride": 4,
                "calibration_min_confidence": 0.65,
                "brightness_min_pinch": 0.18,
                "brightness_max_pinch": 0.55,
                "brightness_min": 10,
                "brightness_max": 100,
                "brightness_smoothing_alpha": 0.35,
                "brightness_deadband": 3,
            },
            "ai": {
                "enabled": True,
                "min_confidence": 0.78,
                "override_boost": 0.12,
                "min_margin": 0.08,
            },
            "hud": {
                "primary_color": [0, 255, 0],
                "warning_color": [0, 165, 255],
                "danger_color": [0, 0, 255],
            },
            "system": {
                "bounding_box_padding": 35,
                "debug_mode": False,
                "log_level": "INFO",
                "frame_skip": 1,
            },
        }

        self.config_path.parent.mkdir(exist_ok=True)
        if not self.config_path.exists():
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(default, f, indent=4, ensure_ascii=False)
            logging.info(f"✓ Config created: {self.config_path}")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                self.data = _deep_merge_dict(default, loaded)
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            self.data = default
