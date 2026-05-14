import cv2


class CameraManager:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.cap = None

    def open(self):
        preferred_index = self.config.data["camera"].get("index", 0)
        candidate_indexes = [preferred_index] + [
            idx for idx in (0, 1, 2) if idx != preferred_index
        ]

        backends = [
            (cv2.CAP_DSHOW, "CAP_DSHOW"),
            (cv2.CAP_MSMF, "CAP_MSMF"),
        ]

        for camera_index in candidate_indexes:
            for backend, backend_name in backends:
                cap_obj = cv2.VideoCapture(camera_index, backend)
                if not cap_obj.isOpened():
                    cap_obj.release()
                    continue

                cap_obj.set(
                    cv2.CAP_PROP_FRAME_WIDTH, self.config.data["camera"]["width"]
                )
                cap_obj.set(
                    cv2.CAP_PROP_FRAME_HEIGHT, self.config.data["camera"]["height"]
                )

                startup_ok = False
                for _ in range(3):
                    ok, _ = cap_obj.read()
                    if ok:
                        startup_ok = True
                        break

                if startup_ok:
                    self.logger.info(
                        f"✓ Camera initialized with backend {backend_name} (index {camera_index})"
                    )
                    self.cap = cap_obj
                    return cap_obj

                self.logger.warning(
                    f"⚠ Backend {backend_name} opened but failed to read frames (index {camera_index})"
                )
                cap_obj.release()

        self.cap = None
        return None

    def read(self):
        if self.cap is None:
            return False, None
        return self.cap.read()

    def reinitialize(self):
        self.close()
        return self.open()

    def close(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
