import sys

from app_controller import NebulaApp
from communication.mqtt_handler import MQTTManager
from config import Config
from utils.logger import setup_logger
from vision.gesture_engine import GestureEngine
from vision.hand_tracker import HandTracker
from vision.hud import HUD

logger = setup_logger()
config = Config()


def build_app():
    tracker = HandTracker(config)
    gesture_engine = GestureEngine(config)
    hud = HUD(config)
    mqtt_manager = MQTTManager(config)
    return NebulaApp(config, tracker, gesture_engine, hud, mqtt_manager, logger)


def main():
    app = None
    logger.info("=" * 50)
    logger.info("🚀 NEBULA INTERFACE STARTING")
    logger.info("=" * 50)

    try:
        app = build_app()
        if not app.start():
            return 1

        for attempt in range(3):
            if app.mqtt_manager.connect():
                logger.info("✓ MQTT Broker Connected")
                break
            logger.warning(f"⚠ MQTT connection attempt {attempt + 1}/3 failed")

        if not app.mqtt_manager.connected:
            logger.warning("⚠ Running without MQTT (ESP32 will not receive commands)")

        logger.info(
            "✓ Nebula Interface Ready - Press 'q' to quit, 'd' for debug, 'k' for calibration capture, 1-5 for label, 'r' to reset"
        )
        logger.info("=" * 50)

        app.run()
        return 0

    except KeyboardInterrupt:
        logger.info("⏸ Interrupted by user")
        return 0
    except Exception as exc:
        logger.error(f"✗ Unexpected error: {exc}")
        return 1
    finally:
        logger.info("🛑 Shutting down...")
        if app is not None:
            app.shutdown()
        logger.info("=" * 50)
        logger.info("✓ System shutdown complete")
        logger.info("=" * 50)


if __name__ == "__main__":
    sys.exit(main())
