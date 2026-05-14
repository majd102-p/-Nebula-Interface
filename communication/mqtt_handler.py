from core.mqtt_manager import MQTTManager as CoreMQTTManager


class MQTTManager(CoreMQTTManager):
    """Compatibility wrapper that preserves the legacy import path."""

    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.broker = self.settings.host
        self.port = self.settings.port
        self.client_id = self.settings.client_id
        self.reconnect_delay = self.settings.reconnect_delay
        self.max_reconnect_attempts = self.settings.max_reconnect_attempts
