# Nebula Interface Quick Start

## Get Started in 5 Minutes

### 1. Install and verify

```bash
cd c:\Users\Eng-JoJo\Desktop\projects\nebula-interface
python setup.py
```

This will install libraries, create required folders, check the camera, and verify MQTT.

### 2. Start Mosquitto

```bash
mosquitto -v
```

You should see output similar to:

```text
1632480000: Listening on port 1883
```

### 3. Open the Wokwi simulation

1. Go to [wokwi.com](https://wokwi.com)
2. Create a new project
3. Select **ESP32 DevKit V1**
4. Add **SSD1306 OLED** and **WS2812B NeoPixel** components
5. Wire the components like this:

```text
OLED SDA  -> GPIO 21
OLED SCL  -> GPIO 22
NeoPixel  -> GPIO 15
```

1. Copy the ESP32 code and start the simulation

### 4. Run the application

```bash
python main.py
```

You should see startup logs similar to:

```text
==================================================
NEBULA INTERFACE STARTING
==================================================
MQTT Broker Connected
Nebula Interface Ready
```

### 5. Try the gestures

| Gesture | Result |
| --- | --- |
| Raise hand | Detects the hand |
| Peace | Switches to LIGHTING mode |
| Fist | Switches to IDLE mode |
| Pinch | Adjusts brightness |

## Keyboard Shortcuts

| Key | Function |
| --- | --- |
| `q` | Close the program |
| `d` | Toggle debug mode |
| `c` | Display frame count |

## If Something Goes Wrong

### MQTT connection failed

```bash
mosquitto -v
```

### Camera not detected

```bash
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### Gestures are not recognized

- Improve lighting
- Move closer to the camera
- Press `d` to inspect debug overlays

## Expected Results

In the app window you should see values like this:

```text
FPS: 30.2
Mode: LIGHTING
Gesture: PEACE
Confidence: 0.95
State: HAND_TRACKING
Brightness: 75%
```

In Wokwi you should see:

- OLED displaying the current system state
- NeoPixel brightness changing with pinch gestures
- MQTT connection working end to end

## More Information

- [Full guide](README.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Project report](COMPLETION_REPORT.md)

Ready to use.
