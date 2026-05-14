import json
import logging
import queue
import threading
import time

import paho.mqtt.client as mqtt

from config import SystemMode


class MQTTManager:
    def __init__(self, config):
        self.config = config
        self.broker = "localhost"
        self.port = 1883
        self.client_id = f"nebula-vision-{int(time.time())}"
        self.reconnect_delay = 2
        self.max_reconnect_attempts = 5
        self.reconnect_attempt = 0

        self.topics = {
            "status": "nebula/system/status",
            "gestures": "nebula/gestures/events",
            "lighting": "nebula/lighting/control",
        }

        self.outbound_queue = queue.Queue(maxsize=100)
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.connected = False
        self.shutdown_event = threading.Event()

        # Start publisher thread
        self.publisher_thread = threading.Thread(
            target=self._publisher_loop, daemon=True
        )
        self.publisher_thread.start()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            self.reconnect_attempt = 0
            logging.info("✓ MQTT Connected to broker")
            client.subscribe(self.topics["lighting"])
            client.publish(self.topics["status"], json.dumps({"status": "connected"}))
        else:
            logging.warning(f"⚠ MQTT Connection failed with code {rc}")

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        if rc != 0:
            logging.warning(f"⚠ MQTT Disconnected (code: {rc})")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            logging.info(f"📨 MQTT Message from {msg.topic}: {payload}")
        except Exception as e:
            logging.error(f"Error parsing MQTT message: {e}")

    def connect(self):
        """Connect to MQTT broker with retry logic"""
        for attempt in range(self.max_reconnect_attempts):
            try:
                self.client.connect(self.broker, self.port, 60)
                self.client.loop_start()

                # Wait for connection confirmation
                for _ in range(10):
                    if self.connected:
                        return True
                    time.sleep(0.5)

                return False
            except Exception as e:
                self.reconnect_attempt = attempt + 1
                logging.warning(
                    f"⚠ MQTT connection attempt {self.reconnect_attempt}/{self.max_reconnect_attempts} failed: {e}"
                )
                if attempt < self.max_reconnect_attempts - 1:
                    time.sleep(self.reconnect_delay)

        return False

    def _publisher_loop(self):
        """Background thread for publishing queued messages"""
        while not self.shutdown_event.is_set():
            try:
                msg = self.outbound_queue.get(timeout=1)
                if self.connected and self.client:
                    try:
                        self.client.publish(msg["topic"], msg["payload"])
                    except Exception as e:
                        logging.error(f"Publish error: {e}")
                        self.outbound_queue.put(msg)
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Publisher thread error: {e}")

    def publish(self, topic_key: str, payload: dict):
        """Queue a message for publishing"""
        if topic_key not in self.topics:
            logging.warning(f"Unknown topic key: {topic_key}")
            return False

        full_payload = {
            "timestamp": int(time.time()),
            "event_type": "GESTURE_EVENT",
            **payload,
        }

        try:
            self.outbound_queue.put(
                {"topic": self.topics[topic_key], "payload": json.dumps(full_payload)},
                block=False,
            )
            return True
        except queue.Full:
            logging.warning("⚠ MQTT queue full, dropping message")
            return False
        except Exception as e:
            logging.error(f"Error queueing message: {e}")
            return False

    def shutdown(self):
        """Graceful shutdown"""
        logging.info("Shutting down MQTT...")
        self.shutdown_event.set()

        try:
            self.client.loop_stop()
            self.client.disconnect()
            logging.info("✓ MQTT shutdown complete")
        except Exception as e:
            logging.error(f"Error during MQTT shutdown: {e}")
