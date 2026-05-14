# Reference Map

This page records the external repositories that informed Nebula Interface and how their ideas were adapted into the current codebase.

## Reference Sources

| Repo | Main value | Nebula adaptation |
|------|------------|-------------------|
| `google-ai-edge/mediapipe` | Official MediaPipe baseline | `vision/hand_tracker.py`, landmark semantics, and the capture pipeline |
| `Kazuhito00/hand-gesture-recognition-using-mediapipe` | Strong gesture-classification pattern | `core/gesture_classifier.py` and the gesture decision flow |
| `kinivi/hand-gesture-recognition-mediapipe` | Clean, readable English fork | Simplified structure and maintainable gesture logic |
| `potrgani/hand-gesture-recognition-ha-addon` | MQTT-first architecture | `core/mqtt_manager.py` and event-driven publishing |
| `afsaldigitalart/mediapipe-gesture-control` | Responsive realtime control | Brightness feel, smoothing, and feedback cadence |

## What Was Reused Conceptually

- MediaPipe remains the source of hand landmarks.
- Gesture analysis is isolated from camera capture.
- Stable events are published over MQTT instead of embedding device logic in the detector.
- The HUD mirrors runtime state so the system is easy to debug.
- The embedded demo stays lightweight and consumes the same event stream as the desktop app.

## Project Mapping

| Nebula area | Responsibility |
|-------------|-----------------|
| `core/feature_extractor.py` | Rotation-aware feature extraction |
| `core/gesture_classifier.py` | Gesture scoring and decision rules |
| `core/state_machine.py` | Mode transitions |
| `core/mqtt_manager.py` | Transport, reconnect, heartbeat, and publish queue |
| `vision/hud.py` | Runtime overlay and diagnostics |
| `embedded/esp32_mqtt_demo/main.ino` | ESP32/Wokwi subscriber demo |

## Notes

- The codebase adapts ideas; it does not copy implementation wholesale.
- The best results came from combining a clean landmark pipeline with a small, explicit state machine.
- MQTT works best here as a delivery channel, not as a place for gesture reasoning.
