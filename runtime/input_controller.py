import cv2


class InputController:
    def __init__(self, tracker, logger):
        self.tracker = tracker
        self.logger = logger

    def handle(self, runtime_state):
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            runtime_state.running = False
            self.logger.info("✓ Quit requested")
        elif key == ord("d"):
            runtime_state.debug_mode = not runtime_state.debug_mode
            self.logger.info(f"✓ Debug mode: {runtime_state.debug_mode}")
        elif key == ord("k"):
            self.tracker.calibration_store.enabled = (
                not self.tracker.calibration_store.enabled
            )
            self.logger.info(
                f"✓ Calibration capture: {self.tracker.calibration_store.enabled}"
            )
        elif (
            chr(key).isdigit() and chr(key) in self.tracker.calibration_store.label_map
        ):
            label = self.tracker.calibration_store.set_target_label(chr(key))
            self.logger.info(f"✓ Calibration target label: {label}")
        elif key == ord("r"):
            self.tracker.calibration_store.reset()
            self.logger.info("✓ Calibration samples reset")
        elif key == ord("c"):
            self.logger.info(f"📊 Frame count: {runtime_state.frame_count}")
