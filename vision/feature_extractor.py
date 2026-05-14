"""Compatibility wrapper around the canonical core feature extractor."""

from __future__ import annotations

from core import feature_extractor as core_feature_extractor

CoreHandFeatureExtractor = core_feature_extractor.HandFeatureExtractor


class HandFeatureExtractor(CoreHandFeatureExtractor):
    """Preserve the existing vision module API while using the core extractor."""

    def _get_fingers_extended(self, lm, handedness="Unknown", handedness_score=0.0):
        normalized = self._normalize_landmarks(
            lm,
            handedness=handedness,
            handedness_score=handedness_score,
        )
        return [
            1 if score >= 0.55 else 0
            for score in self._calculate_finger_extension_scores(
                lm, normalized, handedness, handedness_score
            )
        ]
