#!/usr/bin/env python3
"""
Nebula Interface - Setup Script
Installs dependencies and checks system requirements
"""

import subprocess
import sys
from pathlib import Path


def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def check_python_version():
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]} OK")


def install_requirements():
    print_header("Installing Dependencies")

    req_file = Path("requirements.txt")
    if not req_file.exists():
        print("❌ requirements.txt not found")
        sys.exit(1)

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)], check=True
        )
        print("\n✓ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Installation failed: {e}")
        sys.exit(1)


def create_directories():
    print_header("Creating Directories")

    dirs = ["logs", "configs", "assets", "assets/screenshots"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✓ {dir_name}/")


def check_mqtt_broker():
    print_header("Checking MQTT Broker")

    import socket

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("localhost", 1883))
        sock.close()

        if result == 0:
            print("✓ MQTT Broker running on localhost:1883")
        else:
            print("⚠ MQTT Broker NOT running on localhost:1883")
            print("  → Start Mosquitto: mosquitto -v")
    except Exception as e:
        print(f"⚠ Could not check MQTT: {e}")


def main():
    print_header("NEBULA INTERFACE - SETUP")

    print("Step 1: Checking Python Version")
    check_python_version()

    print("\nStep 2: Creating Directories")
    create_directories()

    print("\nStep 3: Installing Requirements")
    install_requirements()

    print("\nStep 4: Checking MQTT Broker")
    check_mqtt_broker()

    print_header("✓ Setup Complete!")
    print("Ready to start: python main.py")
    print("\nFirst, make sure:")
    print("  1. Mosquitto is running: mosquitto -v")
    print("  2. Wokwi ESP32 simulation is running")
    print("  3. Your camera is connected")
    print("\nThen run: python main.py\n")


if __name__ == "__main__":
    main()
