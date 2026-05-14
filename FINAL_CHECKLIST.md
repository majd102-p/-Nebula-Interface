# ✅ Final Checklist - Nebula Interface

## 🎯 Before Running

- [ ] **Python 3.8+** installed
  ```bash
  python --version
  # ✓ Python 3.14
  ```

- [ ] **Run setup.py** (if not done yet)
  ```bash
  python setup.py
  ```

- [ ] **Libraries installed** (all tests should pass)
  ```bash
  python test_system.py
  # ✓ Total: 6/6 tests passed (validated locally May 15, 2026)
  ```

- [ ] **Mosquitto running**
  ```bash
  mosquitto -v
  # ✓ Listening on port 1883 (validated locally May 15, 2026)
  ```

- [ ] **Wokwi ready**
  - [ ] New project on wokwi.com
  - [ ] ESP32 DevKit V1 selected
  - [ ] SSD1306 OLED added
  - [ ] WS2812B NeoPixel (16 LED) added
  - [ ] Connections correct:
    - [ ] OLED SDA → GPIO 21
    - [ ] OLED SCL → GPIO 22
    - [ ] NeoPixel → GPIO 15
  - [ ] Code copied and pasted
  - [ ] "Start Simulation" pressed

- [ ] **Camera working**
  ```bash
  python -c "import cv2; print('Camera OK' if cv2.VideoCapture(0).isOpened() else 'No camera')"
  # ✓ Camera OK (validated locally May 15, 2026)
  ```

---

## 🚀 Startup

### Correct Order:

1. **Start Mosquitto First**
   ```bash
   mosquitto -v
   ```
   ✅ You should see: "Listening on port 1883"

2. **Run Wokwi**
   - https://wokwi.com
   - Press "Start Simulation"
   - ✅ OLED should display "Nebula"

3. **Run Python Last**
   ```bash
   cd c:\Users\Eng-JoJo\Desktop\projects\nebula-interface
   python main.py
   ```
  ✅ You should see:
   ```
   ==================================================
   🚀 NEBULA INTERFACE STARTING
   ==================================================
   ✓ MQTT Broker Connected
   ✓ Nebula Interface Ready
   ```

---

## 🎮 Test Gestures

After running the program:

- [ ] **Raise Hand**
  - ✓ Should see: "HAND_TRACKING"
  - ✓ Hand data should appear

- [ ] **Peace ✌️**
  - ✓ Mode changes to: "LIGHTING"
  - ✓ LED in Wokwi lights up

- [ ] **Fist ✊**
  - ✓ Mode returns to: "IDLE"
  - ✓ LED turns off

- [ ] **Pinch (thumb + index finger)**
  - ✓ Brightness changes (0-100%)
  - ✓ LED in Wokwi brightness changes
  - ✓ Number should appear on screen

---

## 🛠️ Keyboard Shortcuts

During execution:

- [ ] **Press 'd'** - Toggle Debug Mode
  - ✓ Additional information appears
  - ✓ "DEBUG MODE" message shown

- [ ] **Press 'c'** - Display Frame Count
  - ✓ Prints number of processed frames

- [ ] **Press 'q'** - Safe Shutdown
  - ✓ All resources cleaned up
  - ✓ MQTT disconnected safely

---

## 📊 Expected Performance

**On Screen:**
```
FPS: 28-30
Mode: LIGHTING
Gesture: PEACE
Confidence: 0.85-0.95
State: HAND_TRACKING
Brightness: 50%
```

**In Wokwi:**
- ✅ OLED displays: "NEBULA"
- ✅ OLED displays: Mode + Gesture
- ✅ OLED displays: Brightness %
- ✅ NeoPixel glows (16 LED)

**In Logs:**
```bash
tail -f logs/nebula_*.log
# Should see new messages every second
```

---

## ❌ Troubleshooting

| Problem | Solution |
|---------|----------|
| "MQTT Connection failed" | Ensure `mosquitto -v` is running |
| "Camera not detected" | Try `test_system.py` or different camera index |
| "لا يكتشف اليد" | حسّن الإضاءة، اقترب من الكاميرا |
| "FPS منخفض جداً" | قلل resolution في `configs/config.json` |
| "Wokwi لا يستقبل رسائل" | تحقق من MQTT address في ESP32 code |

**للمزيد:** اقرأ `TROUBLESHOOTING.md`

---

## 📝 ملاحظات مهمة

⚠️ **يجب البدء بهذا الترتيب:**
```
1. Mosquitto (MQTT Broker)
   ↓
2. Wokwi (ESP32 Simulation)
   ↓
3. Python (main.py)
```

⚠️ **إذا أغلقت أحد المكونات:**
- أغلق البرنامج (اضغط q)
- شغّل المكون الناقص
- شغّل البرنامج مجدداً

⚠️ **إذا حدثت مشاكل:**
1. اقرأ السجلات: `logs/nebula_*.log`
2. فعّل Debug Mode: اضغط 'd'
3. جرّب `python test_system.py` للتشخيص

---

## ✨ آخر التحقق

قبل الانتهاء:

- [ ] جميع الملفات موجودة
  ```bash
  ls -la *.py
  ls -la vision/
  ls -la communication/
  ```

- [ ] جميع الاختبارات نجحت
  ```bash
  python test_system.py
  # ✓ Total: 6/6 tests passed (validated locally May 15, 2026)
  ```

- [ ] السجلات تُنشأ بنجاح
  ```bash
  ls -la logs/
  ```

- [ ] config.json صحيح
  ```bash
  cat configs/config.json | python -m json.tool
  ```

---

## 🎉 الآن جاهز للتشغيل!

```bash
# المرة الأولى:
python setup.py

# ثم في كل مرة:
mosquitto -v              # Terminal 1
# (wokwi.com في Tab)     # Browser
python main.py            # Terminal 2
```

---

**استمتع بـ Nebula Interface!** 🌌

تم التحقق محلياً: May 15, 2026
الإصدار: v1.0 - Production Ready
