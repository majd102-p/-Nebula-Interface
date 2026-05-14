# ESP32 MQTT Demo (Wokwi)

This example is a minimal Arduino sketch for an ESP32 that subscribes to the Nebula MQTT topics and updates an SSD1306 OLED and a small NeoPixel strip.

How to run in Wokwi:

1. Go to [Wokwi](https://wokwi.com) and create a new Arduino ESP32 project.
2. Add an `SSD1306` OLED (I2C) and a `WS2812` (NeoPixel) to the board.
3. Paste the contents of `main.ino` into the editor.
4. Edit `WIFI_SSID` and `WIFI_PASS` or use Wokwi's network simulation options.
5. Start the simulation. The sketch will connect to `test.mosquitto.org` by default.


Testing from your PC (with local Mosquitto running):

Publish brightness:

```bash
mosquitto_pub -h localhost -t nebula/lighting/control -m 80
```

Publish gesture event:

```bash
mosquitto_pub -h localhost -t nebula/gestures/events -m "PEACE"
```

Notes:

- The sketch expects a simple numeric payload (0-100) for `nebula/lighting/control`.
- For production, secure your MQTT broker (TLS and auth) and avoid plaintext WiFi credentials.
