# Nebula Interface — Release Notes

Version: v1.0
Date: 2026-05-15

Summary
-------
- Production-ready release of Nebula Interface: hand-gesture driven lighting and HUD.
- Verified locally: setup, tests, MQTT broker, camera access, and simulated ESP32 message delivery.

Highlights
----------
- Cleaned codebase: formatting (Black/isort) and linting (flake8) applied.
- CI workflows included: Python tests and MkDocs deploy (GitHub Actions).
- ESP32 demo: `embedded/esp32_mqtt_demo/main.ino` and `secrets.example.h` included.
- Simulators: `tools/esp32_simulator.py` and `tools/publish_demo_messages.py` for local validation.

Notes & Next Steps
------------------
- To publish this release to GitHub, create a repo and push the `master` branch, then push tag `v1.0`.
- For automated docs deploy, enable GitHub Pages or use the `deploy_mkdocs.yml` workflow.

SHA: (local commit)
