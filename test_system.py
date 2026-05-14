#!/usr/bin/env python3
"""
Nebula Interface - System Test Script
Tests all components before running main application
"""

import json
import socket
import sys
from pathlib import Path


def print_test(name, passed, details=""):
    status = "✓" if passed else "✗"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} {name}")
    if details:
        print(f"  → {details}")


def test_python_version():
    """Test Python version"""
    version = sys.version_info
    passed = version >= (3, 8)
    print_test("Python Version", passed, f"Python {version.major}.{version.minor}")
    return passed


def test_imports():
    """Test required imports"""
    imports = {
        "cv2": "OpenCV",
        "mediapipe": "MediaPipe",
        "paho.mqtt.client": "Paho MQTT",
        "numpy": "NumPy",
    }

    all_passed = True
    for module, name in imports.items():
        try:
            __import__(module)
            print_test(f"Import {name}", True)
        except ImportError:
            print_test(f"Import {name}", False, "Not installed")
            all_passed = False

    return all_passed


def test_camera():
    """Test camera availability"""
    try:
        import cv2

        cap = cv2.VideoCapture(0)
        available = cap.isOpened()
        if available:
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print_test("Camera", available, f"{width}x{height}")
        else:
            print_test("Camera", False, "No camera detected")
        cap.release()
        return available
    except Exception as e:
        print_test("Camera", False, str(e))
        return False


def test_mqtt():
    """Test MQTT broker"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("localhost", 1883))
        sock.close()

        passed = result == 0
        status = "Running" if passed else "Not running"
        print_test("MQTT Broker", passed, f"localhost:1883 - {status}")
        return passed
    except Exception as e:
        print_test("MQTT Broker", False, str(e))
        return False


def test_config():
    """Test configuration file"""
    config_path = Path("configs/config.json")

    if not config_path.exists():
        print_test("Config File", False, "configs/config.json not found")
        return False

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        required_keys = ["camera", "hand", "gestures", "system"]
        has_keys = all(key in config for key in required_keys)

        if has_keys:
            print_test("Config File", True, "All required keys present")
        else:
            print_test("Config File", False, "Missing required keys")

        return has_keys
    except Exception as e:
        print_test("Config File", False, f"Invalid JSON: {e}")
        return False


def test_directories():
    """Test required directories"""
    dirs = ["logs", "configs", "assets"]
    all_exist = True

    for dir_name in dirs:
        path = Path(dir_name)
        exists = path.exists()
        if not exists:
            path.mkdir(parents=True, exist_ok=True)
        print_test(f"Directory: {dir_name}/", exists or path.exists())
        all_exist = all_exist and (exists or path.exists())

    return all_exist


def main():
    print("\n" + "=" * 60)
    print("  NEBULA INTERFACE - SYSTEM TEST")
    print("=" * 60 + "\n")

    results = {
        "Python Version": test_python_version(),
        "Directories": test_directories(),
        "Config File": test_config(),
        "Required Imports": test_imports(),
        "Camera": test_camera(),
        "MQTT Broker": test_mqtt(),
    }

    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60 + "\n")

    passed = sum(results.values())
    total = len(results)

    for test_name, passed_status in results.items():
        status = "PASS" if passed_status else "FAIL"
        print(f"  {test_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed\n")

    if passed == total:
        print("✓ System ready! Run: python main.py\n")
        return 0
    else:
        missing = [k for k, v in results.items() if not v]
        print("✗ System not ready. Fix these issues:")
        for issue in missing:
            print(f"  - {issue}")
        print("\nSee TROUBLESHOOTING.md for solutions\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
