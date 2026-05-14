#include <WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_NeoPixel.h>

// Load secrets from secrets.h if present. Create a local 'secrets.h' from
// secrets.example.h and do NOT commit it to git.
#if defined(__has_include)
#  if __has_include("secrets.h")
#    include "secrets.h"
#  endif
#endif

#ifndef WIFI_SSID
// -------- CONFIG (edit locally in secrets.h) --------
const char* WIFI_SSID = "YOUR_SSID";
#endif

#ifndef WIFI_PASS
const char* WIFI_PASS = "YOUR_PASSWORD";
#endif

#ifndef MQTT_BROKER
const char* MQTT_BROKER = "test.mosquitto.org"; // or your broker IP
#endif

#ifndef MQTT_PORT
const uint16_t MQTT_PORT = 1883;
#endif

// Hardware pins
#define NEOPIXEL_PIN 15
#define NEOPIXEL_COUNT 8

// OLED config (I2C default)
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

WiFiClient espClient;
PubSubClient client(espClient);
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire);
Adafruit_NeoPixel strip(NEOPIXEL_COUNT, NEOPIXEL_PIN, NEO_GRB + NEO_KHZ800);

int current_brightness = 100;

void drawStatus(const char* line1, const char* line2 = NULL) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);
  display.println(line1);
  if (line2) display.println(line2);
  display.display();
}

void setStripBrightness(int b) {
  current_brightness = constrain(b, 0, 255);
  for (int i=0;i<NEOPIXEL_COUNT;i++) {
    uint32_t c = strip.Color((current_brightness*255)/100, 0, 0); // red ramp
    strip.setPixelColor(i, c);
  }
  strip.show();
}

void callback(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];

  if (String(topic) == "nebula/lighting/control") {
    // Expect payload as number (0-100) or JSON number
    int v = msg.toInt();
    if (v <= 0 && msg.indexOf('0') == -1) {
      drawStatus("Lighting control","invalid payload");
      return;
    }
    int scaled = map(constrain(v, 0, 100), 0, 100, 0, 255);
    setStripBrightness(scaled);
    char buf[32];
    sprintf(buf, "Brightness: %d%%", v);
    drawStatus("Lighting control", buf);
  } else if (String(topic) == "nebula/gestures/events") {
    // Show event text
    drawStatus("Gesture event:", msg.c_str());
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "ESP32-Nebula-" + String(random(0xffff), HEX);
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      client.subscribe("nebula/lighting/control");
      client.subscribe("nebula/gestures/events");
      drawStatus("MQTT connected", MQTT_BROKER);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(100);

  // Init display
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("SSD1306 allocation failed"));
    for(;;);
  }
  display.clearDisplay();
  display.display();

  // Init neopixel
  strip.begin();
  strip.show();

  // Connect WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  drawStatus("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");
  drawStatus("WiFi connected", WiFi.localIP().toString().c_str());

  client.setServer(MQTT_BROKER, MQTT_PORT);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();
}
