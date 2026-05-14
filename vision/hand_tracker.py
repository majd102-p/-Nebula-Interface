import logging
import urllib.request
from pathlib import Path
from types import SimpleNamespace

import cv2
import mediapipe as mp

from .feature_extractor import HandFeatureExtractor
from .hand_analysis_pipeline import HandAnalysisPipeline

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_PATH = Path("assets/models/hand_landmarker.task")


def _download_model_if_needed():
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    if MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 0:
        return

    logging.info("Downloading MediaPipe hand landmarker model...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    logging.info("Hand landmarker model saved to %s", MODEL_PATH)


def _draw_hand_landmarks(frame, landmarks, color=(0, 255, 0)):
    points = [
        (int(lm.x * frame.shape[1]), int(lm.y * frame.shape[0]))
        for lm in landmarks.landmark
    ]
    for x, y in points:
        cv2.circle(frame, (x, y), 4, color, -1)

    connections = [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),
        (0, 5),
        (5, 6),
        (6, 7),
        (7, 8),
        (5, 9),
        (9, 10),
        (10, 11),
        (11, 12),
        (9, 13),
        (13, 14),
        (14, 15),
        (15, 16),
        (13, 17),
        (17, 18),
        (18, 19),
        (19, 20),
        (0, 17),
    ]
    for start, end in connections:
        cv2.line(frame, points[start], points[end], color, 2)


class HandTracker:
    def __init__(self, config):
        self.config = config
        self.processing_scale = float(
            config.data.get("camera", {}).get("processing_scale", 0.5)
        )
        _download_model_if_needed()

        base_options = mp.tasks.BaseOptions(model_asset_path=str(MODEL_PATH))
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mp.tasks.vision.RunningMode.IMAGE,
            num_hands=config.data["hand"]["max_num_hands"],
            min_hand_detection_confidence=config.data["hand"][
                "min_detection_confidence"
            ],
            min_tracking_confidence=config.data["hand"]["min_tracking_confidence"],
            min_hand_presence_confidence=config.data["hand"].get(
                "min_hand_presence_confidence", 0.5
            ),
        )
        self.hands = mp.tasks.vision.HandLandmarker.create_from_options(options)

        self.feature_extractor = HandFeatureExtractor(config)
        self.analysis = HandAnalysisPipeline(config)
        self.calibration_store = self.analysis.calibration_store

    def get_bounding_box(self, landmarks, w, h, padding=35):
        x_coords = [lm.x for lm in landmarks.landmark]
        y_coords = [lm.y for lm in landmarks.landmark]

        x_min = int(max(0, min(x_coords) * w - padding))
        y_min = int(max(0, min(y_coords) * h - padding))
        x_max = int(min(w, max(x_coords) * w + padding))
        y_max = int(min(h, max(y_coords) * h + padding))
        return (x_min, y_min, x_max, y_max)

    def _empty_hand_data(self):
        return {
            "landmarks": None,
            "handedness": "Unknown",
            "handedness_score": 0.0,
            "fingers_up": [0] * 5,
            "pinch_distance": 0.0,
            "gesture": "NO_HAND",
            "confidence": 0.0,
            "ai_confidence": 0.0,
            "motion_gesture": None,
            "motion_confidence": 0.0,
            "bbox": None,
            "features": None,
            "fps": 0.0,
        }

    def _update_hand_data_from_landmarks(
        self,
        frame,
        hand_landmarks,
        hand_data,
        handedness="Unknown",
        handedness_score=0.0,
    ):
        h, w = frame.shape[:2]
        hand_data["landmarks"] = hand_landmarks
        hand_data["handedness"] = handedness
        hand_data["handedness_score"] = handedness_score
        hand_data["bbox"] = self.get_bounding_box(hand_landmarks, w, h)
        _draw_hand_landmarks(frame, hand_landmarks)
        hand_data["features"] = self.feature_extractor.extract_features(
            hand_landmarks,
            handedness=handedness,
            handedness_score=handedness_score,
        )
        if hand_data["features"] and hand_data["features"].get("fingers_extended"):
            hand_data["fingers_up"] = hand_data["features"]["fingers_extended"]
        else:
            hand_data["fingers_up"] = self._get_fingers_up(hand_landmarks)
        hand_data["pinch_distance"] = self._get_pinch_distance(hand_landmarks)

        hand_data = self.analysis.enrich(hand_data)

        return hand_data

    def process_frame(self, frame):
        process_frame = frame
        if 0 < self.processing_scale < 1.0:
            process_width = max(1, int(frame.shape[1] * self.processing_scale))
            process_height = max(1, int(frame.shape[0] * self.processing_scale))
            process_frame = cv2.resize(
                frame, (process_width, process_height), interpolation=cv2.INTER_AREA
            )

        rgb_frame = cv2.cvtColor(process_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        results = self.hands.detect(mp_image)

        hand_data = self._empty_hand_data()

        if results.hand_landmarks:
            hand_landmarks = SimpleNamespace(landmark=results.hand_landmarks[0])
            handedness_label = "Unknown"
            handedness_score = 0.0

            if getattr(results, "handedness", None) and results.handedness:
                first_hand = results.handedness[0]
                if first_hand:
                    top = first_hand[0]
                    handedness_label = (
                        getattr(top, "category_name", "Unknown") or "Unknown"
                    )
                    handedness_score = float(getattr(top, "score", 0.0) or 0.0)

            hand_data = self._update_hand_data_from_landmarks(
                frame,
                hand_landmarks,
                hand_data,
                handedness=handedness_label,
                handedness_score=handedness_score,
            )

        return frame, hand_data

    def _get_fingers_up(self, landmarks):
        return self.feature_extractor._get_fingers_extended(landmarks.landmark)

    def _get_pinch_distance(self, landmarks):
        return self.analysis.calculate_pinch_distance(landmarks)
