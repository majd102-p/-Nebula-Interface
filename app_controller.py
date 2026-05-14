import cv2

from core.performance_monitor import PerformanceMonitor
from runtime.camera_manager import CameraManager
from runtime.frame_processor import FrameProcessor
from runtime.input_controller import InputController
from runtime.runtime_state import RuntimeState


class NebulaApp:
    def __init__(self, config, tracker, gesture_engine, hud, mqtt_manager, logger):
        self.config = config
        self.tracker = tracker
        self.gesture_engine = gesture_engine
        self.hud = hud
        self.mqtt_manager = mqtt_manager
        self.logger = logger
        self.state = RuntimeState()
        self.performance_monitor = PerformanceMonitor()
        self.camera = CameraManager(config, logger)
        self.input_controller = InputController(tracker, logger)
        self.frame_processor = FrameProcessor(
            tracker, gesture_engine, hud, mqtt_manager, self.performance_monitor, logger
        )

    @property
    def running(self):
        return self.state.running

    @running.setter
    def running(self, value):
        self.state.running = value

    def start(self):
        if self.camera.open() is None:
            self.logger.error("✗ Camera not available")
            return False
        return True

    def shutdown(self):
        self.state.running = False
        self.camera.close()
        self.mqtt_manager.shutdown()

    def run(self):
        while self.state.running:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    self.state.consecutive_read_failures += 1
                    self.logger.warning("⚠ Cannot read frame")
                    if self.state.consecutive_read_failures >= 10:
                        self.logger.warning(
                            "⚠ Reinitializing camera after repeated read failures"
                        )
                        if self.camera.reinitialize() is not None:
                            self.state.consecutive_read_failures = 0
                    continue

                self.state.consecutive_read_failures = 0
                self.state.frame_index += 1

                if (
                    self.state.frame_index
                    % (self.config.data.get("system", {}).get("frame_skip", 0) + 1)
                    != 0
                ):
                    self.input_controller.handle(self.state)
                    continue

                frame = cv2.flip(frame, 1)
                display_frame = self.frame_processor.process(frame, self.state)
                cv2.imshow("The Nebula Interface", display_frame)
                self.input_controller.handle(self.state)

            except Exception as exc:
                self.logger.error(f"✗ Frame processing error: {exc}")
                continue

        return self.state.frame_count
