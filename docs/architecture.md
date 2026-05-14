# Architecture

The project is structured as a pipeline: camera capture → `vision/hand_tracker.py` → `vision/feature_extractor.py` → `vision/hand_analysis_pipeline.py` → `vision/gesture_engine.py` → MQTT publish / HUD.

See [diagrams/architecture.md](diagrams/architecture.md) for the diagram and rationale.
