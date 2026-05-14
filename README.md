# 🌌 Nebula Interface

## Advanced Hand Gesture Recognition for IoT Control

<!-- markdownlint-disable -->

![Status](https://img.shields.io/badge/status-production-green)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-purple)

Nebula Interface is a real-time hand gesture recognition system that turns webcam input into MQTT events for lighting and device control. It combines computer vision, event-driven architecture, and ESP32 simulation to create a practical IoT demo that is easy to learn from and strong enough to showcase in a portfolio.

## Why this project matters

This project is built as a learning-friendly reference, not just a demo. It shows how to connect vision, logic, and hardware in a clean way, and it explains the decisions behind the implementation so others can reuse the same patterns in their own projects.

If you are building a portfolio, this project demonstrates:

- Real-time computer vision with MediaPipe and OpenCV
- Event-driven software design with threading and queues
- MQTT-based IoT communication
- Clean configuration and error handling
- A complete developer workflow: setup, testing, logging, troubleshooting, and simulation

## What you can say on LinkedIn

You can describe this project with statements like:

- Built a real-time hand gesture recognition system using Python, OpenCV, and MediaPipe
- Designed an event-driven IoT control pipeline using MQTT and ESP32 simulation
- Implemented gesture smoothing, mode switching, and brightness control for touchless interaction
- Improved reliability with structured logging, retry logic, and graceful shutdown handling
- Created a production-ready developer experience with setup automation, diagnostics, and documentation

## Skills gained from this project

- Computer vision pipeline design
- Hand landmark processing and gesture classification
- State machines and event-driven architecture
- MQTT publish/subscribe communication
- Threading and background worker design
- Debugging and observability with logs
- Configuration management
- Simulation-based IoT testing
- Technical documentation writing
- System integration across software and embedded targets

## What makes this README useful

Many YouTube tutorials show the “happy path” only. This README is written to help you actually understand the system, avoid common mistakes, and build the project correctly the first time.

It explains:

- What each module does
- Why the architecture is structured this way
- How the hand gestures map to system states
- Why the chosen thresholds and cooldowns are used
- What common tutorial shortcuts are wrong or incomplete
- How to verify that the system is really working

## Reference Repositories

These are the main references that shaped the architecture:

| Repo | Why it matters | What Nebula takes from it |
|------|----------------|---------------------------|
| `google-ai-edge/mediapipe` | Official MediaPipe baseline | Hand tracking foundation and landmark semantics |
| `Kazuhito00/hand-gesture-recognition-using-mediapipe` | Best overall gesture pipeline | Clean MLP-style gesture classification ideas |
| `kinivi/hand-gesture-recognition-mediapipe` | Polished English fork | Simplified gesture handling and readable structure |
| `potrgani/hand-gesture-recognition-ha-addon` | Strong MQTT architecture | Event-first messaging and Home Assistant style control |
| `afsaldigitalart/mediapipe-gesture-control` | Smooth realtime control | Fast control-loop feel and responsive feedback |

### What was reused conceptually

- MediaPipe stays the source of truth for hand landmarks.
- Gesture analysis is separated from camera capture.
- Gesture output becomes events, not UI-only state.
- MQTT is treated as a transport layer for devices.
- The HUD mirrors the runtime state so debugging stays visible.

For a more direct source-to-project mapping, see [docs/reference_map.md](docs/reference_map.md).

---

## Overview

**Nebula Interface** uses:

- **Computer Vision**: MediaPipe for hand tracking
- **Gesture Logic**: Gesture recognition and mode transitions
- **MQTT**: Real-time messaging to devices
- **ESP32**: Hardware simulation in Wokwi
- **OLED + NeoPixel**: Visual feedback for mode and brightness

The system is designed around a simple idea: detect a gesture, turn it into a stable event, publish that event, and let the display or hardware react.

---

## Features

- Real-time hand tracking at high frame rates
- Gesture recognition for Peace, Fist, Open Hand, One, and Pinch
- Mode switching between IDLE, LIGHTING, MEDIA, and MOUSE
- Pinch-based brightness control from 0% to 100%
- MQTT integration for external device control
- Smooth gesture filtering to reduce jitter
- Safe shutdown and reconnect logic
- Structured logs for easier debugging
- Wokwi-based ESP32 simulation for reproducible testing

---

## System Design

The project is organized as a pipeline with explicit boundaries:

- Capture and detect hands
- Extract features from landmarks
- Run analysis and classification in a dedicated pipeline
- Turn the analysis into mode and brightness decisions
- Publish events and render the HUD

This is intentionally closer to a MediaPipe-style graph than a monolithic loop.

```mermaid
flowchart LR
    A[Camera Frame] --> B[HandTracker]
    B --> C[FeatureExtractor]
    C --> D[Hand Analysis Pipeline]
    D --> E[GestureEngine]
    E --> F[Event Queue]
    F --> G[MQTT Manager]
    F --> H[HUD Renderer]
    G <--> I[ESP32 Simulation\nOLED + NeoPixel]
```

### Design Principles

- Keep frame capture, analysis, decision making, and transport separate.
- Prefer typed data boundaries over shared mutable state where possible.
- Treat calibration, motion gestures, and AI refinement as an analysis layer, not as camera logic.
- Keep the main loop as a composition root only.
- Use MQTT as a delivery channel, not as a place where gesture logic lives.

### Canonical Core Layer

The reusable logic now lives in `core/`:

- `core/feature_extractor.py` creates rotation-aware, ML-ready hand features.
- `core/gesture_classifier.py` combines rule scores, motion overrides, and optional ML predictions.
- `core/mqtt_manager.py` provides queued publishing, heartbeat, LWT, reconnect, and rate limiting.
- `core/performance_monitor.py` tracks FPS, inference time, queue depth, and runtime health.
- `core/state_machine.py` isolates gesture-driven mode transitions.

The legacy `vision/` and `communication/` modules remain as compatibility wrappers over these core components.

### UML Class Diagram

```mermaid
classDiagram
    class HandTracker {
        +process_frame(frame)
        +get_bounding_box(landmarks)
        -classify_gesture(features)
    }

    class GestureEngine {
        +process(detection)
        +normalize_pinch(features)
        -handle_mode_transition(gesture)
    }

    class MQTTManager {
        +connect()
        +publish(topic, payload)
        +shutdown()
        -publisher_loop()
    }

    class HUD {
        +render(frame, state)
    }

    class FeatureExtractor {
        +extract(landmarks)
        +calculate_distances()
    }

    HandTracker --> FeatureExtractor
    HandTracker --> GestureEngine
    GestureEngine --> MQTTManager
    GestureEngine --> HUD
```

### UML Sequence Diagram

```mermaid
sequenceDiagram
    participant Cam as Camera
    participant HT as HandTracker
    participant GE as GestureEngine
    participant MQ as MQTTManager
    participant ESP as ESP32/Wokwi
    participant HUD as HUD

    Cam->>HT: Frame
    HT->>GE: Landmarks + features
    GE->>GE: Classify gesture
    GE->>MQ: Publish event/state
    MQ->>ESP: MQTT message
    GE->>HUD: Update display data
    HUD->>Cam: Render overlay
```

### UML Activity Diagram

```mermaid
flowchart TD
    Start([Start]) --> Capture[Capture frame]
    Capture --> Detect[Detect hand landmarks]
    Detect --> Valid{Hand detected?}
    Valid -- No --> ShowNoHand[Show idle HUD]
    Valid -- Yes --> Extract[Extract features]
    Extract --> Recognize[Recognize gesture]
    Recognize --> Stable{Stable enough?}
    Stable -- No --> Wait[Wait / smooth]
    Stable -- Yes --> Decide[Decide mode or brightness action]
    Decide --> Publish[Publish MQTT event]
    Publish --> Render[Render HUD]
    Render --> Capture
    ShowNoHand --> Capture
    Wait --> Capture
```

---

## How it works

1. The camera captures a frame.
2. MediaPipe finds hand landmarks.
3. Features are extracted from the landmarks.
4. Gesture logic classifies the current hand pose.
5. The system smooths the result to avoid false positives.
6. If the gesture is valid, the system publishes an MQTT message.
7. The HUD updates the screen with state, mode, gesture, and brightness.
8. The ESP32 simulation reacts through OLED and NeoPixel output.

## Calibration and local training

The project now includes a calibration workflow for building user-specific prototypes from your own hand samples.

### Runtime controls

- `k` toggles calibration capture on or off
- `1` to `5` selects the target label while capture is active
- `r` clears collected calibration samples

### Calibration labels

| Key | Label |
|-----|-------|
| 1 | FIST |
| 2 | ONE |
| 3 | PEACE |
| 4 | OPEN |
| 5 | PINCH_READY |

### Build prototypes from samples

After collecting samples, generate runtime prototypes with:

```bash
python scripts/build_calibration_prototypes.py
```

This creates `configs/calibration_prototypes.json`, which the local AI loader will use automatically when present.

---

## Gestures

| Gesture | Meaning | Result |
|---------|---------|--------|
| Peace ✌️ | Activation gesture | Switch to LIGHTING |
| Fist ✊ | Stop gesture | Return to IDLE |
| Open Hand | Control gesture | Switch to MEDIA |
| Pinch 🤏 | Continuous control | Adjust brightness |
| One ☝️ | Optional navigation | MOUSE / selection use cases |

---

## MQTT Topics

- `nebula/system/status` - Online/offline lifecycle state
- `nebula/system/heartbeat` - Periodic heartbeat from the Python app
- `nebula/gestures/events` - Gesture events
- `nebula/lighting/control` - Lighting control values

These topics keep the UI and device logic separated. That separation is important because it makes the system easier to debug, test, and extend.

---

## Project Structure

```text
nebula-interface/
├── main.py
├── config.py
├── core/
│   ├── feature_extractor.py
│   ├── gesture_classifier.py
│   ├── mqtt_manager.py
│   ├── performance_monitor.py
│   └── state_machine.py
├── runtime/
│   ├── camera_manager.py
│   ├── frame_processor.py
│   ├── input_controller.py
│   └── runtime_state.py
├── setup.py
├── test_system.py
├── README.md
├── TROUBLESHOOTING.md
├── QUICK_START.md
├── FINAL_CHECKLIST.md
├── COMPLETION_REPORT.md
├── requirements.txt
├── configs/
│   └── config.json
├── communication/
│   └── mqtt_handler.py
├── embedded/
│   └── esp32_mqtt_demo/
├── vision/
│   ├── hand_tracker.py
│   ├── gesture_engine.py
│   ├── feature_extractor.py
│   ├── smoothing.py
│   └── hud.py
├── utils/
│   ├── helpers.py
│   └── logger.py
├── assets/
│   └── screenshots/
└── logs/
```

---

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| Vision | Python, OpenCV, MediaPipe |
| Processing | Feature extraction, smoothing, normalization |
| Architecture | Threading, queue, state machine |
| Communication | MQTT with paho-mqtt |
| Embedded | ESP32, Wokwi, SSD1306 OLED, NeoPixel |
| Tools | VS Code, Git, logging, testing |

---

## Installation

### Recommended setup

```bash
python setup.py
```

### Manual setup

```bash
pip install -r requirements.txt
```

Then run the system test:

Before the first full run, validate the environment again with `python test_system.py`.

You should see all tests pass before you start `main.py`.

---

## Quick Start

### How to Run on ESP32 / Wokwi

Use this path when you want to see the full Python -> MQTT -> ESP32 loop working end to end.

1. Start an MQTT broker.

```bash
mosquitto -v
```

2. Configure the Python app in `configs/config.json`.

- Set `mqtt.host` to your broker address.
- Keep `mqtt.port` at `1883` unless your broker uses another port.
- Set the camera and gesture thresholds you want to demo.

3. Open the ESP32 demo in Wokwi or on real hardware.

- Wokwi path: create an ESP32 project, add an SSD1306 OLED and a WS2812 NeoPixel strip, then paste [embedded/esp32_mqtt_demo/main.ino](embedded/esp32_mqtt_demo/main.ino).
- Real hardware path: copy [embedded/esp32_mqtt_demo/secrets.example.h](embedded/esp32_mqtt_demo/secrets.example.h) to `secrets.h`, fill in Wi-Fi and broker credentials, then flash the sketch to the board.

4. Verify the wiring and topics.

- OLED on I2C default pins.
- NeoPixel on GPIO 15.
- Subscribe to `nebula/system/status`, `nebula/gestures/events`, and `nebula/lighting/control`.

### Wokwi Wiring

Use this wiring for an ESP32 DevKit V1 in Wokwi:

| Component | ESP32 Pin | Notes |
|-----------|-----------|-------|
| SSD1306 VCC | 3V3 | Power the OLED from 3.3V |
| SSD1306 GND | GND | Shared ground |
| SSD1306 SDA | GPIO 21 | Default I2C SDA on ESP32 |
| SSD1306 SCL | GPIO 22 | Default I2C SCL on ESP32 |
| WS2812 VCC | 5V | In Wokwi this is fine; keep common ground |
| WS2812 GND | GND | Shared ground |
| WS2812 DIN | GPIO 15 | Matches `NEOPIXEL_PIN` in [main.ino](embedded/esp32_mqtt_demo/main.ino) |

Recommended extras:

- Add a 330 ohm resistor between GPIO 15 and DIN if you are wiring real hardware.
- Keep the OLED address at `0x3C`, which matches the sketch.
- If you use a different ESP32 board, keep SDA/SCL on the default Wire pins unless you also change the code.

5. Run the Python app.

```bash
python main.py
```

6. Test the live loop.

- Show `PEACE` to switch mode.
- Show `FIST` to return to idle.
- Show an open hand to move into media mode.
- Use `PINCH_READY` for brightness control.
- Watch the OLED update immediately and the NeoPixel strip respond to lighting payloads.

### Troubleshooting the ESP32 path

- If the ESP32 does not connect, confirm Wi-Fi credentials and broker host/port.
- If the OLED stays blank, verify the I2C wiring and address.
- If brightness does not change, confirm that `nebula/lighting/control` is being published and that the payload contains a `value` field.
- If the gesture text looks wrong, inspect the `nebula/gestures/events` payload and the `decision_source` field.

Before the first full run, validate the environment again with `python test_system.py`.

Shortcuts:

- `q` = quit
- `d` = debug mode
- `c` = frame count

---

## Configuration

Edit `configs/config.json` to adjust:

- camera resolution
- detection thresholds
- gesture cooldowns
- UI colors
- smoothing settings

Example:

```json
{
  "camera": {"width": 1280, "height": 720, "fps": 30},
  "hand": {"min_detection_confidence": 0.7, "min_tracking_confidence": 0.7},
  "gestures": {"cooldown_event": 0.65, "cooldown_continuous": 0.08}
}
```

---

## Why these implementation choices are correct

### 1. Normalized pinch control
Using pinch distance relative to palm size is better than using raw pixel distance because it works across different camera distances and hand sizes.

### 2. Gesture smoothing
Real hands are noisy. Smoothing reduces flicker and prevents accidental state changes.

### 3. MQTT in a background thread
Network calls should not block the vision loop. A background publisher keeps the UI responsive.

### 4. State machine for modes
Mode-based logic is easier to understand and extend than one large if/else chain.

### 5. Logging and diagnostics
Logs make the project maintainable. If something fails, you can trace it quickly.

---

## Common YouTube mistakes and why this project avoids them

### Mistake 1: Using raw pinch distance only
Many tutorials compare two landmark coordinates directly and call it done. That breaks when the hand moves closer or farther from the camera. This project normalizes pinch distance against palm size so the value is more stable.

### Mistake 2: No smoothing
Without smoothing, the gesture can flip between states every frame. Here, smoothing helps keep the output stable and usable.

### Mistake 3: Blocking MQTT calls inside the main loop
Some tutorials publish directly in the frame-processing loop. That can freeze the camera pipeline. This project uses a background publisher thread instead.

### Mistake 4: No graceful shutdown
If the app closes without cleanup, camera and MQTT resources can remain in a bad state. This project closes everything cleanly.

### Mistake 5: No configuration file
Hard-coded thresholds make tuning painful. This project keeps settings in `config.json` so you can adjust behavior without rewriting code.

### Mistake 6: No verification step
Skipping a system test wastes time. Here, `test_system.py` verifies the environment before runtime issues appear.

### Mistake 7: No explanation of why the thresholds exist
Many tutorials show numbers without context. This README explains the purpose of confidence thresholds and cooldowns so you can tune them intelligently.

---

## What you learn from this project

If you build this project carefully, you will learn:

- How a real-time vision pipeline is structured
- How gesture recognition becomes an event system
- How to use MQTT for device communication
- How to design a state machine for user interaction
- How to make a project robust with logging and retries
- How to document a project so others can learn from it

---

## LinkedIn-ready skills

Use these skill statements in your profile or post:

- Real-time computer vision
- Gesture recognition using MediaPipe
- Python application architecture
- MQTT and IoT communication
- Event-driven programming
- Threading and asynchronous task separation
- Debugging and observability
- Technical documentation and developer experience
- ESP32 simulation and embedded integration
- Problem solving and systems integration

---

## Portfolio value

This project is strong for a portfolio because it shows more than code. It shows a complete engineering workflow:

- Problem definition
- System design
- Implementation
- Simulation
- Testing
- Debugging
- Documentation
- User education

That combination makes the project more credible than a simple tutorial clone.

---

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

Quick checks:

```bash
python test_system.py
mosquitto -v
```

If gestures are unstable:

- improve lighting
- keep your hand centered
- slow down the gesture
- press `d` for debug mode

---

## Screenshots and demo

Use this checklist before publishing the project or posting it on LinkedIn:

- Live HUD showing hand landmarks, gesture label, confidence, and performance stats.
- Peace gesture activating lighting mode.
- Fist gesture returning the system to idle.
- Open hand switching into media mode.
- Pinch control changing brightness in real time.
- ESP32 OLED showing the received gesture or brightness payload.
- NeoPixel strip reacting to the lighting topic.
- MQTT broker console showing published Nebula topics.
- Wokwi simulator or real ESP32 setup side by side with the Python app.

Recommended file targets:

- `assets/screenshots/hud-live.png`
- `assets/screenshots/gesture-peace.png`
- `assets/screenshots/gesture-fist.png`
- `assets/screenshots/gesture-pinch-brightness.png`
- `assets/screenshots/esp32-oled.png`
- `assets/screenshots/neopixel-feedback.png`

Add a demo video link after recording a short run that shows the full camera -> MQTT -> ESP32 flow.

---

## Future roadmap

- Add multiple-hand support
- Add custom gestures
- Improve analytics and logging
- Export event history
- Add a desktop control panel
- Deploy to real ESP32 hardware

---

## Final notes

This project is intentionally written so a beginner can follow it and an experienced developer can still extract architectural value from it. The goal is not only to make the system work, but to make it understandable and reusable.

If you want, you can use this README as a template for future AI, IoT, or computer vision projects.

---

**Developed with ❤️ by [majd102-p]**

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![MQTT](https://img.shields.io/badge/MQTT-660066?style=for-the-badge)
![ESP32](https://img.shields.io/badge/ESP32-000000?style=for-the-badge&logo=espressif&logoColor=white)

<!-- markdownlint-enable -->
