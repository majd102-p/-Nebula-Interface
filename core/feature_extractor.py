"""Orientation-aware hand feature extraction for gesture analysis.

This module converts MediaPipe hand landmarks into a stable, normalized
representation that is suitable for both rule-based and ML-based gesture
classification.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from utils.helpers import calculate_angle, calculate_distance

Point3D = Tuple[float, float, float]
LandmarkSequence = Sequence[Any]


@dataclass(frozen=True)
class ExtractorSettings:
    thumb_open_spread_ratio: float = 0.44
    thumb_open_stretch_ratio: float = 0.36
    thumb_straight_angle_deg: float = 145.0
    finger_pip_straight_angle_deg: float = 160.0
    finger_dip_straight_angle_deg: float = 145.0
    finger_extension_ratio: float = 1.55
    finger_tip_margin_ratio: float = 0.08
    finger_vertical_margin: float = 0.015
    thumb_x_margin: float = 0.015
    handedness_min_score: float = 0.6


class HandFeatureExtractor:
    """Create a normalized feature dictionary from raw hand landmarks."""

    FINGER_CHAINS = (
        (5, 6, 7, 8),
        (9, 10, 11, 12),
        (13, 14, 15, 16),
        (17, 18, 19, 20),
    )

    def __init__(self, config=None):
        hand_cfg = config.data.get("hand", {}) if config else {}
        self.settings = ExtractorSettings(
            thumb_open_spread_ratio=float(
                hand_cfg.get("thumb_open_spread_ratio", 0.44)
            ),
            thumb_open_stretch_ratio=float(
                hand_cfg.get("thumb_open_stretch_ratio", 0.36)
            ),
            thumb_straight_angle_deg=float(
                hand_cfg.get("thumb_straight_angle_deg", 145.0)
            ),
            finger_pip_straight_angle_deg=float(
                hand_cfg.get("finger_pip_straight_angle_deg", 160.0)
            ),
            finger_dip_straight_angle_deg=float(
                hand_cfg.get("finger_dip_straight_angle_deg", 145.0)
            ),
            finger_extension_ratio=float(hand_cfg.get("finger_extension_ratio", 1.55)),
            finger_tip_margin_ratio=float(
                hand_cfg.get("finger_tip_margin_ratio", 0.08)
            ),
            finger_vertical_margin=float(hand_cfg.get("finger_vertical_margin", 0.015)),
            thumb_x_margin=float(hand_cfg.get("thumb_x_margin", 0.015)),
            handedness_min_score=float(hand_cfg.get("handedness_min_score", 0.6)),
        )
        self.prev_features: Optional[Dict[str, Any]] = None

    def extract_features(
        self,
        landmarks,
        handedness: str = "Unknown",
        handedness_score: float = 0.0,
    ) -> Optional[Dict[str, Any]]:
        if not landmarks:
            return None

        lm = landmarks.landmark
        normalized_landmarks = self._normalize_landmarks(
            lm, handedness=handedness, handedness_score=handedness_score
        )
        finger_extension_scores = self._calculate_finger_extension_scores(
            lm, normalized_landmarks, handedness, handedness_score
        )
        fingers_extended = [
            1 if score >= 0.55 else 0 for score in finger_extension_scores
        ]

        features: Dict[str, Any] = {
            "normalized_landmarks": normalized_landmarks,
            "landmark_vector": [
                coord for point in normalized_landmarks for coord in point[:2]
            ],
            "summary_vector": self._summary_vector(
                lm,
                finger_extension_scores,
                handedness=handedness,
                handedness_score=handedness_score,
            ),
            "hand_rotation_deg": self._estimate_hand_rotation(lm),
            "finger_extension_scores": finger_extension_scores,
            "fingers_extended": fingers_extended,
            "pinch_distance": calculate_distance(lm[4], lm[8]),
            "normalized_pinch": self._normalize_pinch(lm),
            "grab_strength": self._calculate_grab_strength(lm),
            "palm_angle": calculate_angle(lm[0], lm[5], lm[17]),
            "hand_openness": self._calculate_hand_openness(lm),
            "thumb_angle": calculate_angle(lm[1], lm[2], lm[4]),
            "palm_center": self._get_palm_center(lm),
            "palm_size": calculate_distance(lm[0], lm[9]),
            "handedness": handedness,
            "handedness_score": handedness_score,
        }
        features["feature_vector"] = self.to_vector(features)
        self.prev_features = features
        return features

    def to_vector(self, features: Dict[str, Any]) -> List[float]:
        vector = list(features.get("landmark_vector") or [])
        vector.extend(
            float(score) for score in features.get("finger_extension_scores") or []
        )
        vector.extend(
            [
                float(features.get("normalized_pinch", 0.0)),
                float(features.get("grab_strength", 0.0)),
                float(features.get("hand_openness", 0.0)),
                float(features.get("thumb_angle", 0.0)) / 180.0,
                float(features.get("hand_rotation_deg", 0.0)) / 180.0,
            ]
        )
        return vector

    def _summary_vector(
        self,
        lm: LandmarkSequence,
        finger_extension_scores: Iterable[float],
        handedness: str,
        handedness_score: float,
    ) -> List[float]:
        scores = [float(score) for score in finger_extension_scores]
        if len(scores) != 5:
            scores = [0.0] * 5

        return [
            scores[0],
            scores[1],
            scores[2],
            scores[3],
            scores[4],
            self._normalize_pinch(lm),
            self._calculate_grab_strength(lm),
            self._calculate_hand_openness(lm),
            self._estimate_hand_rotation(lm) / 180.0,
            float(handedness_score),
        ]

    def _estimate_hand_rotation(self, lm: LandmarkSequence) -> float:
        wrist = lm[0]
        middle_mcp = lm[9]
        return math.degrees(math.atan2(middle_mcp.y - wrist.y, middle_mcp.x - wrist.x))

    def _calculate_finger_extension_scores(
        self,
        lm: LandmarkSequence,
        normalized: Sequence[Point3D],
        handedness: str,
        handedness_score: float,
    ) -> List[float]:
        thumb_score = self._thumb_extension_score(lm, normalized)
        finger_scores = [
            self._finger_extension_score(lm, normalized, mcp, pip, dip, tip)
            for mcp, pip, dip, tip in self.FINGER_CHAINS
        ]
        scores = [thumb_score, *finger_scores]

        if (
            handedness_score < self.settings.handedness_min_score
            and handedness == "Unknown"
        ):
            scores[0] = min(1.0, scores[0] * 0.95)

        return [max(0.0, min(1.0, float(score))) for score in scores]

    def _finger_extension_score(
        self,
        lm: LandmarkSequence,
        normalized: Sequence[Point3D],
        mcp: int,
        pip: int,
        dip: int,
        tip: int,
    ) -> float:
        pip_joint_angle = calculate_angle(lm[mcp], lm[pip], lm[dip])
        dip_joint_angle = calculate_angle(lm[pip], lm[dip], lm[tip])
        tip_extension = calculate_distance(lm[tip], lm[mcp])
        pip_extension = calculate_distance(lm[pip], lm[mcp]) + 1e-6
        tip_to_wrist = calculate_distance(lm[tip], lm[0])
        pip_to_wrist = calculate_distance(lm[pip], lm[0])
        palm_size = calculate_distance(lm[0], lm[9]) + 1e-6

        straightness = self._clamp01(
            (pip_joint_angle - self.settings.finger_pip_straight_angle_deg) / 20.0
        )
        dip_straightness = self._clamp01(
            (dip_joint_angle - self.settings.finger_dip_straight_angle_deg) / 20.0
        )
        extension_ratio = self._clamp01(
            (tip_extension / pip_extension - 1.0)
            / max(1e-6, self.settings.finger_extension_ratio - 1.0)
        )
        tip_lift = self._clamp01(
            (tip_to_wrist - pip_to_wrist)
            / max(1e-6, self.settings.finger_tip_margin_ratio * palm_size * 2.5)
        )
        normalized_tip = normalized[tip]
        normalized_pip = normalized[pip]
        vertical_lift = self._clamp01((normalized_pip[1] - normalized_tip[1]) / 0.25)

        return self._clamp01(
            0.30 * straightness
            + 0.20 * dip_straightness
            + 0.20 * extension_ratio
            + 0.15 * tip_lift
            + 0.15 * vertical_lift
        )

    def _thumb_extension_score(
        self,
        lm: LandmarkSequence,
        normalized: Sequence[Point3D],
    ) -> float:
        thumb_tip = lm[4]
        thumb_mcp = lm[2]
        thumb_tip_norm = normalized[4]
        thumb_mcp_norm = normalized[2]
        span = calculate_distance(lm[0], lm[9]) + 1e-6

        spread = self._clamp01(abs(thumb_tip_norm[0] - thumb_mcp_norm[0]) / 0.45)
        lift = self._clamp01(abs(thumb_tip_norm[1] - thumb_mcp_norm[1]) / 0.35)
        angle = calculate_angle(lm[1], lm[2], lm[4])
        angle_score = self._clamp01(
            (angle - self.settings.thumb_straight_angle_deg) / 25.0
        )
        raw_span = self._clamp01(
            calculate_distance(thumb_tip, thumb_mcp) / (span * 0.7)
        )

        return self._clamp01(
            0.35 * spread + 0.20 * lift + 0.25 * angle_score + 0.20 * raw_span
        )

    def _normalize_pinch(self, lm: LandmarkSequence) -> float:
        palm_size = calculate_distance(lm[0], lm[9]) + 1e-6
        return calculate_distance(lm[4], lm[8]) / palm_size

    def _calculate_grab_strength(self, lm: LandmarkSequence) -> float:
        distances = [calculate_distance(lm[4], lm[i]) for i in (8, 12, 16, 20)]
        return max(0.0, 1.0 - (sum(distances) / (4 * 0.25)))

    def _calculate_hand_openness(self, lm: LandmarkSequence) -> float:
        total = sum(
            calculate_distance(lm[tip], lm[mcp])
            for tip, mcp in ((8, 5), (12, 9), (16, 13), (20, 17))
        )
        return min(1.0, total / 0.8)

    def _get_palm_center(self, lm: LandmarkSequence) -> Tuple[float, float]:
        indices = [0, 5, 9, 13, 17]
        x = sum(lm[i].x for i in indices) / len(indices)
        y = sum(lm[i].y for i in indices) / len(indices)
        return (x, y)

    def _normalize_landmarks(
        self,
        lm: LandmarkSequence,
        handedness: str = "Unknown",
        handedness_score: float = 0.0,
    ) -> List[Point3D]:
        wrist = lm[0]
        middle_mcp = lm[9]
        scale = calculate_distance(wrist, middle_mcp)
        if scale < 1e-6:
            scale = calculate_distance(wrist, lm[5])
        if scale < 1e-6:
            scale = 1.0

        base_angle = math.atan2(middle_mcp.y - wrist.y, middle_mcp.x - wrist.x)
        target_angle = -math.pi / 2
        rotation = target_angle - base_angle
        cos_r = math.cos(rotation)
        sin_r = math.sin(rotation)
        mirrored = (
            handedness_score >= self.settings.handedness_min_score
            and handedness == "Left"
        )

        normalized: List[Point3D] = []
        for point in lm:
            dx = point.x - wrist.x
            dy = point.y - wrist.y
            rx = (dx * cos_r - dy * sin_r) / scale
            ry = (dx * sin_r + dy * cos_r) / scale
            if mirrored:
                rx = -rx
            normalized.append((float(rx), float(ry), float(point.z)))
        return normalized

    @staticmethod
    def _clamp01(value: float) -> float:
        return max(0.0, min(1.0, float(value)))
