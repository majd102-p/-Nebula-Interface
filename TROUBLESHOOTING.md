# 🔧 Troubleshooting Guide - Nebula Interface

## ❌ Common Issues & Solutions

---

## 1️⃣ **ModuleNotFoundError: No module named 'mediapipe'**

### Causes

- Required libraries are not installed

### Solution

```bash
pip install -r requirements.txt
# or:
python setup.py
```

---

## 2️⃣ MQTT Connection failed

### Causes

- Mosquitto is not running
- Port 1883 is already in use

### Solution

```bash
# Start Mosquitto
mosquitto -v

# Check if port is in use
netstat -ano | findstr 1883

# If port is busy, kill the process:
taskkill /PID <PID> /F
mosquitto -v
```

---

## 3️⃣ Camera not detected / Cannot read frame

### Causes

- Camera is being used by another application
- Wrong camera index (0, 1, etc.)

### Solution

```bash
# Test camera:
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"

# If False, try:
python -c "import cv2; print(cv2.VideoCapture(1).isOpened())"

# Modify main.py:
cap = cv2.VideoCapture(1)  # Instead of 0
```

---

## 4️⃣ Gestures not recognized

### Causes

- Poor lighting conditions
- Hand is too far from camera
- Confidence threshold is too high

### Solution

In `configs/config.json`:

```json
{
  "hand": {
    "min_detection_confidence": 0.5,
    "min_tracking_confidence": 0.5
  }
}
```

---

## 5️⃣ MQTT is slow or disconnects

### Causes

- Weak internet connection
- Too many messages

### Solution

In `config.py`:

```python
"gestures": {
  "cooldown_event": 1.0,        # Increased from 0.65
  "cooldown_continuous": 0.15   # Increased from 0.08
}
```

---

## 6️⃣ ESP32 Wokwi is not receiving messages

### Causes

- Wrong IP address
- Simulator is closed

### Solution

In ESP32 code in Wokwi:

```cpp
const char* mqtt_server = "localhost";  // Make sure this is correct
```

Check sent messages:

```bash
# Use MQTT Explorer:
1. Download: https://mqtt-explorer.com
2. Connect to: localhost:1883
3. Subscribe to: nebula/#
4. View live messages
```

---

## 7️⃣ FPS is very low (<10)

### Causes

- Slow camera
- Weak processor
- Camera resolution is too high

### Solution

In `configs/config.json`:

```json
{
  "camera": {
    "width": 640,   // Changed from 1280
    "height": 480,  // Changed from 720
    "fps": 30
  }
}
```

---

## 8️⃣ Application crashes when closing

### Causes

- Thread did not terminate properly

### Solution

Press `q` slowly for graceful shutdown:

```bash
# Keyboard shortcuts:
q  → quit gracefully
d  → toggle debug mode
c  → show frame count
```

---

## 9️⃣ Error in feature_extractor

### Solution

Make sure `hand_data` has:

```python
hand_data["features"] = HandFeatureExtractor().extract_features(landmarks)
```

---

## 🔟 How to enable Debug Mode

While running, press `d`:

- Shows additional information
- Displays debug boxes
- Prints FPS and other data

```bash
# View messages:
tail -f logs/nebula_*.log
```

---

## 📊 MQTT Test Commands

```bash
# Subscribe to all topics:
mosquitto_sub -t "nebula/#" -v

# Publish test message:
mosquitto_pub -t "nebula/lighting/control" -m '{"value": 50}'

# View broker statistics:
mosquitto_sub -t "$SYS/broker/#" -v
```

---

## 🎯 Correct Startup Steps

```bash
# 1. Install dependencies
python setup.py

# 2. Start Mosquitto
mosquitto -v
# ✓ 1632480000: Listening on port 1883

# 3. Start Wokwi (in browser)

- https://wokwi.com
- → Create new project
- → Add code
- → Click Start Simulation

# 4. Run Python application
python main.py
# ✓ Nebula Interface Started

# 5. Test gestures
# Raise your hand → You should see "HAND_TRACKING"
# Peace ✌️ → Should change to "LIGHTING"
# Fist ✊ → Should return to "IDLE"
```

---

## ✅ Verify Connections

```bash
# Is MQTT running?
ps aux | grep mosquitto

# Is camera working?
python -c "import cv2; cap = cv2.VideoCapture(0); print('Ready' if cap.isOpened() else 'Failed')"

# Is MediaPipe installed?
python -c "import mediapipe; print('OK')"

# Is everything ready?
python setup.py
```

---

## 🆘 Still Having Issues?

If problem persists:

1. Check logs: `logs/nebula_*.log`
2. Enable Debug Mode: Press `d`
3. Use MQTT Explorer to monitor messages
4. Carefully read console output for error details

---

**Last Updated:** May 9, 2026
