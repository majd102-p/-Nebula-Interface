"""Thread-safe MQTT manager with LWT, heartbeat, reconnect, and rate limiting."""

from __future__ import annotations

import json
import logging
import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import paho.mqtt.client as mqtt


@dataclass
class MQTTSettings:
    host: str = "localhost"
    port: int = 1883
    client_id: str = field(default_factory=lambda: f"nebula-{int(time.time())}")
    username: Optional[str] = None
    password: Optional[str] = None
    keepalive: int = 60
    qos: int = 1
    retain: bool = False
    heartbeat_interval: float = 10.0
    reconnect_delay: float = 2.0
    max_reconnect_attempts: int = 10
    queue_size: int = 250
    min_publish_interval: float = 0.05
    status_topic: str = "nebula/system/status"
    heartbeat_topic: str = "nebula/system/heartbeat"
    gestures_topic: str = "nebula/gestures/events"
    lighting_topic: str = "nebula/lighting/control"


class MQTTManager:
    def __init__(self, config):
        mqtt_cfg = config.data.get("mqtt", {})
        self.settings = MQTTSettings(
            host=mqtt_cfg.get("host", "localhost"),
            port=int(mqtt_cfg.get("port", 1883)),
            client_id=mqtt_cfg.get("client_id") or f"nebula-{int(time.time())}",
            username=mqtt_cfg.get("username"),
            password=mqtt_cfg.get("password"),
            keepalive=int(mqtt_cfg.get("keepalive", 60)),
            qos=int(mqtt_cfg.get("qos", 1)),
            retain=bool(mqtt_cfg.get("retain", False)),
            heartbeat_interval=float(mqtt_cfg.get("heartbeat_interval", 10.0)),
            reconnect_delay=float(mqtt_cfg.get("reconnect_delay", 2.0)),
            max_reconnect_attempts=int(mqtt_cfg.get("max_reconnect_attempts", 10)),
            queue_size=int(mqtt_cfg.get("queue_size", 250)),
            min_publish_interval=float(mqtt_cfg.get("min_publish_interval", 0.05)),
            status_topic=mqtt_cfg.get("status_topic", "nebula/system/status"),
            heartbeat_topic=mqtt_cfg.get("heartbeat_topic", "nebula/system/heartbeat"),
            gestures_topic=mqtt_cfg.get("gestures_topic", "nebula/gestures/events"),
            lighting_topic=mqtt_cfg.get("lighting_topic", "nebula/lighting/control"),
        )
        self.logger = logging.getLogger("Nebula.MQTT")
        self.client = self._create_client()
        self.connected = False
        self.shutdown_event = threading.Event()
        self.outbound_queue: "queue.Queue[Dict[str, Any]]" = queue.Queue(
            maxsize=self.settings.queue_size
        )
        self.last_publish_at: Dict[str, float] = {}
        self.topics = {
            "status": self.settings.status_topic,
            "heartbeat": self.settings.heartbeat_topic,
            "gestures": self.settings.gestures_topic,
            "lighting": self.settings.lighting_topic,
        }
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.publisher_thread = threading.Thread(
            target=self._publisher_loop, daemon=True
        )
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True
        )
        self.publisher_thread.start()
        self.heartbeat_thread.start()

    def _create_client(self):
        kwargs = {
            "client_id": self.settings.client_id,
            "protocol": mqtt.MQTTv311,
        }
        try:
            kwargs["callback_api_version"] = mqtt.CallbackAPIVersion.VERSION1
        except Exception:
            pass
        client = mqtt.Client(**kwargs)
        if self.settings.username:
            client.username_pw_set(self.settings.username, self.settings.password)
        return client

    def connect(self) -> bool:
        for attempt in range(1, self.settings.max_reconnect_attempts + 1):
            if self.shutdown_event.is_set():
                return False
            try:
                will_payload = json.dumps(
                    {
                        "status": "offline",
                        "client_id": self.settings.client_id,
                        "timestamp": int(time.time()),
                    }
                )
                self.client.will_set(
                    self.topics["status"],
                    payload=will_payload,
                    qos=self.settings.qos,
                    retain=True,
                )
                self.client.connect(
                    self.settings.host,
                    self.settings.port,
                    self.settings.keepalive,
                )
                self.client.loop_start()
                if self._wait_for_connect():
                    return True
            except Exception as exc:
                self.logger.warning(
                    "MQTT connect attempt %s/%s failed: %s",
                    attempt,
                    self.settings.max_reconnect_attempts,
                    exc,
                )
            time.sleep(self.settings.reconnect_delay)
        return False

    def disconnect(self) -> None:
        self.shutdown_event.set()
        try:
            self._enqueue(
                self.topics["status"],
                {"status": "offline", "client_id": self.settings.client_id},
                retain=True,
                qos=self.settings.qos,
            )
        except Exception:
            pass
        try:
            self.client.loop_stop()
            self.client.disconnect()
        finally:
            self.connected = False

    def shutdown(self) -> None:
        self.logger.info("Shutting down MQTT manager")
        self.disconnect()

    def publish(
        self,
        topic_key: str,
        payload: Dict[str, Any],
        *,
        retain: Optional[bool] = None,
        qos: Optional[int] = None,
    ) -> bool:
        topic = self.topics.get(topic_key, topic_key)
        return self._enqueue(topic, payload, retain=retain, qos=qos)

    def publish_status(self, status: Dict[str, Any]) -> bool:
        return self._enqueue(
            self.topics["status"], status, retain=True, qos=self.settings.qos
        )

    def publish_heartbeat(self, extra: Optional[Dict[str, Any]] = None) -> bool:
        payload = {
            "status": "online",
            "client_id": self.settings.client_id,
            "timestamp": int(time.time()),
        }
        if extra:
            payload.update(extra)
        return self._enqueue(
            self.topics["heartbeat"], payload, retain=False, qos=self.settings.qos
        )

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            self.logger.info(
                "MQTT connected to %s:%s", self.settings.host, self.settings.port
            )
            client.subscribe(
                [
                    (self.topics["status"], self.settings.qos),
                    (self.topics["heartbeat"], self.settings.qos),
                    (self.topics["gestures"], self.settings.qos),
                    (self.topics["lighting"], self.settings.qos),
                ]
            )
            self.publish_status(
                {
                    "status": "online",
                    "client_id": self.settings.client_id,
                    "timestamp": int(time.time()),
                }
            )
        else:
            self.logger.warning("MQTT connection failed with code %s", rc)

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        if rc != 0:
            self.logger.warning("MQTT disconnected unexpectedly (code=%s)", rc)

    def on_message(self, client, userdata, msg):
        try:
            decoded = msg.payload.decode("utf-8")
            try:
                payload = json.loads(decoded)
            except Exception:
                payload = decoded
            self.logger.info("MQTT message on %s: %s", msg.topic, payload)
        except Exception as exc:
            self.logger.error("Failed to decode MQTT message: %s", exc)

    def _heartbeat_loop(self) -> None:
        while not self.shutdown_event.is_set():
            if self.connected:
                self.publish_heartbeat()
            self.shutdown_event.wait(self.settings.heartbeat_interval)

    def _publisher_loop(self) -> None:
        while not self.shutdown_event.is_set():
            try:
                item = self.outbound_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if not self.connected:
                self.outbound_queue.put(item)
                time.sleep(self.settings.reconnect_delay)
                continue

            topic = item["topic"]
            payload = item["payload"]
            qos = int(item.get("qos", self.settings.qos))
            retain = bool(item.get("retain", self.settings.retain))
            min_interval = float(
                item.get("min_interval", self.settings.min_publish_interval)
            )

            now = time.time()
            last_sent = self.last_publish_at.get(topic, 0.0)
            if now - last_sent < min_interval:
                continue

            try:
                info = self.client.publish(topic, payload, qos=qos, retain=retain)
                if getattr(info, "rc", 0) == 0:
                    self.last_publish_at[topic] = now
                else:
                    self.logger.warning(
                        "MQTT publish rejected for topic %s (rc=%s)", topic, info.rc
                    )
            except Exception as exc:
                self.logger.error("MQTT publish error: %s", exc)
                self.connected = False
                self.outbound_queue.put(item)
                time.sleep(self.settings.reconnect_delay)

    def _enqueue(
        self,
        topic: str,
        payload: Dict[str, Any],
        *,
        retain: Optional[bool] = None,
        qos: Optional[int] = None,
        min_interval: Optional[float] = None,
    ) -> bool:
        message = {
            "topic": topic,
            "payload": json.dumps(
                {"timestamp": int(time.time()), **payload}, ensure_ascii=False
            ),
            "retain": self.settings.retain if retain is None else retain,
            "qos": self.settings.qos if qos is None else qos,
            "min_interval": (
                self.settings.min_publish_interval
                if min_interval is None
                else min_interval
            ),
        }
        try:
            self.outbound_queue.put_nowait(message)
            return True
        except queue.Full:
            self.logger.warning("MQTT queue full, dropping topic %s", topic)
            return False

    def _wait_for_connect(self) -> bool:
        for _ in range(20):
            if self.connected:
                return True
            time.sleep(0.25)
        return False
