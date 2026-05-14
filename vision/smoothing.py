from collections import deque
from statistics import StatisticsError, mode


class GestureSmoother:
    def __init__(self, history_length=10, confirmation_frames=5):
        self.history = deque(maxlen=history_length)
        self.confirmation_frames = confirmation_frames
        self.current_gesture = None
        self.stable_count = 0
        self.confidence = 0.0

    def update(self, gesture):
        self.history.append(gesture)
        history_maxlen = self.history.maxlen or 1

        if len(self.history) < history_maxlen:
            self.confidence = len(self.history) / history_maxlen
            return None

        try:
            most_common = mode(self.history)
        except StatisticsError:
            # mode() raises StatisticsError when no unique mode is found
            most_common = gesture

        if most_common == self.current_gesture:
            self.stable_count += 1
        else:
            self.stable_count = 1
            self.current_gesture = most_common

        self.confidence = min(1.0, self.stable_count / self.confirmation_frames)

        if self.stable_count >= self.confirmation_frames:
            return self.current_gesture
        return None
