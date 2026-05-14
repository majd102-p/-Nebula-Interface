from dataclasses import dataclass


@dataclass
class RuntimeState:
    running: bool = True
    debug_mode: bool = False
    frame_index: int = 0
    frame_count: int = 0
    consecutive_read_failures: int = 0
