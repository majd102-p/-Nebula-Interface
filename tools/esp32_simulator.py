"""Simple ESP32-like MQTT simulator: subscribes to Nebula topics and prints messages.
Use this to validate that MQTT messages from the app reach a device.
"""

import json
import logging
import sys
import time

import paho.mqtt.client as mqtt

LOGGER = logging.getLogger("esp32_sim")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


TOPICS = ["nebula/lighting/control", "nebula/gestures/events", "nebula/system/status"]


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        LOGGER.info("Connected to broker, subscribing to topics: %s", TOPICS)
        for t in TOPICS:
            client.subscribe(t)
    else:
        LOGGER.error("Failed to connect to broker (rc=%s)", rc)


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        try:
            payload = json.loads(payload)
        except Exception:
            pass
        LOGGER.info("[ESP32] Received %s -> %s", msg.topic, payload)
    except Exception as e:
        LOGGER.error("Error handling message: %s", e)


def main(broker="localhost", port=1883):
    client_id = f"esp32-sim-{int(time.time())}"
    client = mqtt.Client(client_id=client_id)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(broker, port, 60)
    except Exception as e:
        LOGGER.error("Could not connect to MQTT broker %s:%s — %s", broker, port, e)
        sys.exit(2)

    client.loop_start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        LOGGER.info("Shutting down simulator...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ESP32 MQTT Simulator")
    parser.add_argument("--broker", default="localhost")
    parser.add_argument("--port", type=int, default=1883)
    args = parser.parse_args()
    main(broker=args.broker, port=args.port)
