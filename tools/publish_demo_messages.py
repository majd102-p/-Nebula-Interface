"""Publish demo MQTT messages for Nebula topics to test device delivery.
Runs a small sequence then exits.
"""

import json
import time

import paho.mqtt.client as mqtt


def publish_demo(broker="localhost", port=1883, repeats=3):
    client = mqtt.Client(client_id=f"nebula-demo-pub-{int(time.time())}")
    client.connect(broker, port, 60)
    client.loop_start()

    try:
        for i in range(repeats):
            # Lighting control example
            lighting = {"gesture": "PINCH", "mode": "LIGHTING", "value": 64}
            client.publish("nebula/lighting/control", json.dumps(lighting))
            print("Published lighting:", lighting)

            # Gesture event example
            gesture = {"gesture": "SWIPE_RIGHT", "mode": "NAVIGATION", "action": "NEXT"}
            client.publish("nebula/gestures/events", json.dumps(gesture))
            print("Published gesture:", gesture)

            time.sleep(1)
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--broker", default="localhost")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    publish_demo(broker=args.broker, port=args.port, repeats=args.repeats)
