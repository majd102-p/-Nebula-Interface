import math

import numpy as np

from utils.helpers import calculate_angle, calculate_distance


class HandFeatureExtractor:
    """
    طبقة استخراج الميزات المتقدمة
    تحول Raw Landmarks → Feature Vector قابل للتوسع (Rule-based → ML)
    """

    def __init__(self, config=None):
        self.prev_features = None
        hand_cfg = config.data.get("hand", {}) if config else {}
        self.thumb_open_spread_ratio = float(
            hand_cfg.get("thumb_open_spread_ratio", 0.44)
        )
        self.thumb_open_stretch_ratio = float(
            hand_cfg.get("thumb_open_stretch_ratio", 0.36)
        )
        self.thumb_straight_angle_deg = float(
            hand_cfg.get("thumb_straight_angle_deg", 145.0)
        )
        self.finger_pip_straight_angle_deg = float(
            hand_cfg.get("finger_pip_straight_angle_deg", 160.0)
        )
        self.finger_dip_straight_angle_deg = float(
            hand_cfg.get("finger_dip_straight_angle_deg", 145.0)
        )
        self.finger_extension_ratio = float(
            hand_cfg.get("finger_extension_ratio", 1.55)
        )
        self.finger_tip_margin_ratio = float(
            hand_cfg.get("finger_tip_margin_ratio", 0.08)
        )
        self.finger_vertical_margin = float(
            hand_cfg.get("finger_vertical_margin", 0.015)
        )
        self.thumb_x_margin = float(hand_cfg.get("thumb_x_margin", 0.015))
        self.handedness_min_score = float(hand_cfg.get("handedness_min_score", 0.6))

    def extract_features(self, landmarks, handedness="Unknown", handedness_score=0.0):
        if not landmarks:
            return None

        lm = landmarks.landmark
        features = {}

        # Canonical landmark space used by the AI and motion-history paths.
        features["normalized_landmarks"] = self._normalize_landmarks(
            lm,
            handedness=handedness,
            handedness_score=handedness_score,
        )
        features["landmark_vector"] = [
            coord for point in features["normalized_landmarks"] for coord in point[:2]
        ]

        # Finger states
        features["fingers_extended"] = self._get_fingers_extended(
            lm, handedness, handedness_score
        )

        # Pinch & Grab
        features["pinch_distance"] = calculate_distance(lm[4], lm[8])
        features["normalized_pinch"] = self._normalize_pinch(lm)
        features["grab_strength"] = self._calculate_grab_strength(lm)

        # Angles & Orientation
        features["palm_angle"] = calculate_angle(lm[0], lm[5], lm[17])
        features["hand_openness"] = self._calculate_hand_openness(lm)
        features["thumb_angle"] = calculate_angle(lm[1], lm[2], lm[4])

        # Palm info
        features["palm_center"] = self._get_palm_center(lm)
        features["palm_size"] = calculate_distance(lm[0], lm[9])

        self.prev_features = features
        return features

    def _get_fingers_extended(self, lm, handedness="Unknown", handedness_score=0.0):
        palm_size = calculate_distance(lm[0], lm[9]) + 1e-6
        fingers = []

        thumb_tip_x = lm[4].x
        thumb_ip_x = lm[3].x
        thumb_mcp_x = lm[2].x
        x_margin = self.thumb_x_margin

        # Primary rule: thumb moves on X axis relative to the rest of the hand.
        if handedness_score >= self.handedness_min_score and handedness == "Right":
            thumb_is_extended = (
                thumb_tip_x > thumb_ip_x + x_margin
                and thumb_tip_x > thumb_mcp_x + x_margin
            )
        elif handedness_score >= self.handedness_min_score and handedness == "Left":
            thumb_is_extended = (
                thumb_tip_x < thumb_ip_x - x_margin
                and thumb_tip_x < thumb_mcp_x - x_margin
            )
        else:
            thumb_dx = thumb_tip_x - thumb_ip_x
            thumb_is_extended = abs(thumb_dx) > x_margin

        fingers.append(1 if thumb_is_extended else 0)

        finger_chains = [
            (5, 6, 7, 8),
            (9, 10, 11, 12),
            (13, 14, 15, 16),
            (17, 18, 19, 20),
        ]
        for mcp, pip, dip, tip in finger_chains:
            pip_joint_angle = calculate_angle(lm[mcp], lm[pip], lm[dip])
            dip_joint_angle = calculate_angle(lm[pip], lm[dip], lm[tip])
            tip_extension = calculate_distance(lm[tip], lm[mcp])
            pip_extension = calculate_distance(lm[pip], lm[mcp]) + 1e-6
            tip_to_wrist = calculate_distance(lm[tip], lm[0])
            pip_to_wrist = calculate_distance(lm[pip], lm[0])

            is_straight = (
                pip_joint_angle > self.finger_pip_straight_angle_deg
                and dip_joint_angle > self.finger_dip_straight_angle_deg
            )
            has_real_extension = (
                tip_extension / pip_extension
            ) > self.finger_extension_ratio
            has_tip_margin = (tip_to_wrist - pip_to_wrist) > (
                self.finger_tip_margin_ratio * palm_size
            )
            is_pointing_up = lm[tip].y < (lm[pip].y - self.finger_vertical_margin)

            fingers.append(
                1
                if (
                    is_straight
                    and has_real_extension
                    and has_tip_margin
                    and is_pointing_up
                )
                else 0
            )

        return fingers

    def _normalize_pinch(self, lm):
        palm_size = calculate_distance(lm[0], lm[9]) + 0.001
        return calculate_distance(lm[4], lm[8]) / palm_size

    def _calculate_grab_strength(self, lm):
        distances = [calculate_distance(lm[4], lm[i]) for i in [8, 12, 16, 20]]
        return max(0.0, 1.0 - (sum(distances) / (4 * 0.25)))

    def _calculate_hand_openness(self, lm):
        total = sum(
            calculate_distance(lm[tip], lm[mcp])
            for tip, mcp in [(8, 5), (12, 9), (16, 13), (20, 17)]
        )
        return min(1.0, total / 0.8)

    def _get_palm_center(self, lm):
        indices = [0, 5, 9, 13, 17]
        x = sum(lm[i].x for i in indices) / 5
        y = sum(lm[i].y for i in indices) / 5
        return (x, y)

    def _normalize_landmarks(self, lm, handedness="Unknown", handedness_score=0.0):
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
            handedness_score >= self.handedness_min_score and handedness == "Left"
        )

        normalized = []
        for point in lm:
            dx = point.x - wrist.x
            dy = point.y - wrist.y
            rx = (dx * cos_r - dy * sin_r) / scale
            ry = (dx * sin_r + dy * cos_r) / scale
            if mirrored:
                rx = -rx
            normalized.append((float(rx), float(ry), float(point.z)))

        return normalized
