import cv2


class HUD:
    def __init__(self, config):
        self.config = config

    def draw(self, frame, hand_data, status=None, debug=False):
        h, w = frame.shape[:2]
        overlay = frame.copy()
        status = status or {}
        system_mode = status.get("system_mode", "IDLE")
        tracking_state = status.get("tracking_state", "NO_HAND")
        calibration_enabled = bool(status.get("calibration_enabled", False))
        calibration_label = status.get("calibration_label")

        # Bounding Box
        if hand_data.get("bbox"):
            x1, y1, x2, y2 = hand_data["bbox"]
            cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Main Info
        cv2.putText(
            overlay,
            f"FPS: {hand_data.get('fps', 0):.1f}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )
        cv2.putText(
            overlay,
            f"Mode: {system_mode}",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.85,
            (255, 255, 0),
            2,
        )
        cv2.putText(
            overlay,
            f"Gesture: {hand_data['gesture']}",
            (20, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2,
        )
        cv2.putText(
            overlay,
            f"Confidence: {hand_data['confidence']:.2f}",
            (20, 160),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            overlay,
            f"State: {tracking_state}",
            (20, 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 100),
            2,
        )
        cv2.putText(
            overlay,
            f"Calibration: {'ON' if calibration_enabled else 'OFF'}",
            (20, 240),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 200, 255) if calibration_enabled else (120, 120, 120),
            2,
        )
        if calibration_enabled:
            label_text = calibration_label or "AUTO"
            cv2.putText(
                overlay,
                f"Label: {label_text} (1-5, r=reset)",
                (20, 280),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 220, 255),
                2,
            )
        if hand_data.get("motion_gesture"):
            cv2.putText(
                overlay,
                f"Motion: {hand_data['motion_gesture']} ({hand_data.get('motion_confidence', 0.0):.2f})",
                (20, 320),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 180, 80),
                2,
            )

        # Brightness Bar (Pinch)
        if hand_data.get("features"):
            brightness = int(status.get("brightness", 0))
            brightness = max(0, min(100, brightness))
            bar_width = int(400 * (brightness / 100))
            cv2.rectangle(overlay, (w - 450, 50), (w - 50, 80), (50, 50, 50), -1)
            cv2.rectangle(
                overlay, (w - 450, 50), (w - 450 + bar_width, 80), (0, 255, 100), -1
            )
            cv2.putText(
                overlay,
                f"Brightness: {brightness}%",
                (w - 450, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 100),
                2,
            )

        # Debug Mode
        if debug and hand_data.get("features"):
            cv2.putText(
                overlay,
                "DEBUG MODE",
                (w // 2 - 80, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 0, 255),
                2,
            )

        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
        return frame
