# 📑 Nebula Interface - Project Index

<!-- markdownlint-disable -->

## 🌟 Welcome to Nebula Interface

Advanced hand gesture recognition system for touchless device control.

---

## 📚 Files & Documentation

### 🚀 Quick Start
| File | Description |
|------|-------------|
| **[QUICK_START.md](QUICK_START.md)** | ⚡ Get started in 5 minutes |
| **[FINAL_CHECKLIST.md](FINAL_CHECKLIST.md)** | ✅ Complete verification checklist |

### 📖 Full Guide
| File | Description |
|------|-------------|
| **[README.md](README.md)** | 📋 Complete project explanation |
| **[COMPLETION_REPORT.md](COMPLETION_REPORT.md)** | 🎯 Completion report |

### 🔧 Troubleshooting
| File | Description |
|------|-------------|
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | 🔧 Solve 10 common issues |

---

## 🐍 Python Files

### Main Files
| File | Size | Description |
|------|------|-------------|
| **main.py** | 5.5 KB | Main program (video processing + MQTT) |
| **config.py** | 2.2 KB | System settings and configuration |
| **setup.py** | 2.6 KB | Automatic installation script |
| **test_system.py** | 4.8 KB | Comprehensive system test (6 tests) |

### vision/ Folder (Vision Processing)
```
vision/
├── __init__.py              # Package marker
├── hand_tracker.py          # Hand tracker (MediaPipe)
├── gesture_engine.py        # Gesture engine
├── feature_extractor.py     # Hand feature extraction
├── hud.py                   # Display interface
└── smoothing.py             # Motion smoothing
```

### communication/ Folder (Communications)
```
communication/
└── mqtt_handler.py          # MQTT handler with retry logic
```

### utils/ Folder (Helper Tools)
```
utils/
├── helpers.py               # Helper functions (mathematics)
└── logger.py                # Logging system
```

---

## ⚡ Quick Start Steps

### 1️⃣ Initial Installation
```bash
python setup.py
# or:
pip install -r requirements.txt
```

### 2️⃣ Run Mosquitto (Terminal 1)
```bash
mosquitto -v
```

### 3️⃣ Run Wokwi (Browser)
```
https://wokwi.com
→ New Project
→ ESP32 DevKit V1
→ Add SSD1306 + WS2812B
→ Copy ESP32 code
→ Start Simulation
```

### 4️⃣ Run the Program (Terminal 2)
```bash
python main.py
```

---

## 🎯 Testing

### Full System Test
```bash
python test_system.py
# Should see: Total: 6/6 tests passed
```

### Gesture Testing
- Raise hand → Detects hand
- Peace ✌️ → Switch to LIGHTING
- Fist ✊ → Return to IDLE
- Pinch 🤏 → Change brightness

---

## 🌨 Main Features

✅ **Hand Tracking** - Real-time hand tracking
✅ **Gesture Recognition** - Recognize 5 different gestures
✅ **MQTT Communication** - Reliable connection with retry logic
✅ **ESP32 Integration** - Full simulation in Wokwi
✅ **Error Handling** - Comprehensive error handling
✅ **Debug Mode** - Press 'd' for details

---

## 📊 Architecture

```
┌─────────────────────────────────┐
│   Python Application (main.py)  │
├─────────────────────────────────┤
│ • Camera → cv2.VideoCapture     │
│ • Vision → MediaPipe Hands      │
│ • Gesture → Real-time Recognition│
│ • MQTT → Communication Layer    │
└─────────────────────────────────┘
              ↕
┌─────────────────────────────────┐
│   MQTT Broker (Mosquitto)       │
│   localhost:1883                │
└─────────────────────────────────┘
              ↕
┌─────────────────────────────────┐
│   ESP32 in Wokwi                │
│ • OLED Display (SSD1306)        │
│ • NeoPixel LEDs (WS2812B)       │
└─────────────────────────────────┘
```

---

## 🔐 Requirements

### Pre-installation
- Python 3.8+
- Mosquitto MQTT Broker
- Webcam / Camera

### Libraries (auto-installed)
```
opencv-python>=4.8.0
mediapipe>=0.10.8
paho-mqtt>=1.6.1
numpy>=1.24.0
Pillow>=10.0.0
```

---

## ⌨️ Shortcuts

| Key | Function |
|-----|----------|
| `q` | Safe program shutdown |
| `d` | Toggle Debug Mode |
| `c` | Display frame count |

---

## 📊 MQTT Topics

| Topic | Type | Content |
|-------|------|----------|
| `nebula/system/status` | Publish | System state |
| `nebula/gestures/events` | Publish | Gesture events |
| `nebula/lighting/control` | Subscribe | Control commands |

---

## 🌎 Learning & Development

### For Beginners
1. Read [QUICK_START.md](QUICK_START.md)
2. Follow [FINAL_CHECKLIST.md](FINAL_CHECKLIST.md)
3. Run program and test gestures

### For Advanced Users
1. Edit `configs/config.json` for improvements
2. Read comments in files
3. Try adding new gestures

### For Contributors
1. Read [COMPLETION_REPORT.md](COMPLETION_REPORT.md)
2. Understand structure in [README.md](README.md)
3. Look for `TODO` and `FIXME` in files

---

## 🐛 Troubleshooting

**Problem?** Read [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

Or try:
```bash
# Quick diagnosis
python test_system.py

# View logs
tail -f logs/nebula_*.log

# Enable debug mode (press 'd' in program)
```

---

## 📊 Statistics

| Metric | Value |
|--------|-------|
| Python files | 11 |
| Lines of code | ~2000 |
| Documented files | 5 |
| Tests | 6 |
| Version | v1.0 |
| Status | ✅ Production Ready |

---

## 📑 Important Notes

⚠️ **Correct startup order:**
1. Mosquitto (MQTT)
2. Wokwi (ESP32)
3. Python (main.py)

⚠️ **If the browser or terminal closes:**
- Close the program (q)
- Restart from step 1

✅ **For safe shutdown:**
```bash
Press 'q' in the program window
```

---

## 🌐 External Resources

- [MediaPipe Documentation](https://mediapipe.dev/)
- [Mosquitto MQTT](https://mosquitto.org/)
- [Wokwi Simulator](https://wokwi.com/)
- [OpenCV Tutorial](https://docs.opencv.org/)
- [Paho MQTT Client](https://pypi.org/project/paho-mqtt/)

---

## 📞 Support

| Issue | Solution |
|-------|----------|
| Nothing works | Read QUICK_START.md first |
| Installation errors | Run `python setup.py` |
| Camera not detected | Try `test_system.py` |
| MQTT not working | Ensure `mosquitto -v` is running |
| Gestures not recognized | Improve lighting, read TROUBLESHOOTING.md |

---

## 🎉 Final Summary

**Nebula Interface ready for immediate use!**

✅ All files organized
✅ All tools documented
✅ All tests passed
✅ All errors handled

**Start now:**
```bash
python setup.py && python main.py
```

---

**Last Updated:** May 9, 2026
**Version:** v1.0
**Status:** ✅ Production Ready

---

**Enjoy Nebula Interface!** 🌌✨

<!-- markdownlint-enable -->
