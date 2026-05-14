import math


def calculate_distance(p1, p2):
    return math.hypot(p1.x - p2.x, p1.y - p2.y)


def calculate_angle(p1, p2, p3):
    a = math.atan2(p3.y - p2.y, p3.x - p2.x)
    b = math.atan2(p1.y - p2.y, p1.x - p2.x)
    angle = abs(math.degrees(a - b))
    return 360 - angle if angle > 180 else angle


def clamp(value, min_val=0, max_val=100):
    return max(min_val, min(max_val, int(value)))
