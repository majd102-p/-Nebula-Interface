# Nebula Accuracy and Logic Roadmap

## Objective

Build a highly reliable local gesture-control pipeline with measurable quality gates, deterministic behavior, and minimal false positives.

## Scope

- Hand landmark stability
- Finger count correctness
- Gesture classification reliability
- Brightness control smoothness
- Runtime safety and fallback behavior

## Quality Targets

1. Finger count frame-level accuracy >= 96% on validation set.
2. Gesture event false-positive rate <= 1.5% during no-intent motion.
3. Mode-change accidental trigger <= 0.5% per 10-minute session.
4. Brightness jitter <= 4% RMS when the hand remains steady.
5. End-to-end latency (capture to action) <= 80 ms on the target machine.

## Ground Truth and Evaluation Protocol

1. Record short labeled clips for each gesture class and neutral/no-hand.
2. Split by person and session to avoid data leakage.
3. Evaluate frame-level and event-level metrics separately.
4. Keep a fixed holdout set for regression checks.
5. Re-run benchmarks after every threshold or model change.

## Professional-Grade Enhancements

1. Normalize all landmark features against the wrist and hand scale before any classification.
2. Add rotation-aware preprocessing so gesture logic stays stable when the hand tilts.
3. Split gesture recognition into two paths:
   - static pose and finger-count gestures
   - motion-based gestures from fingertip history
4. Add per-user calibration to learn a small personalized prototype set.
5. Add uncertainty rejection so weak predictions become no-action instead of false actions.
6. Add class-specific hold and cooldown rules for high-risk transitions.
7. Use world-landmark or depth-aware signals where scale ambiguity hurts accuracy.
8. Track per-session quality counters for false positives, re-inits, jitter, and latency.
9. Capture labeled debug clips under different lighting, distance, and occlusion conditions.
10. Evaluate with person-separated splits and report confusion matrix, macro F1, and per-class precision/recall.

## Phase 1: Data and Instrumentation

1. Add runtime logging for:
   - Rule gesture
   - AI gesture
   - AI confidence
   - Final fused decision
   - Finger vector and normalized pinch
2. Save sampled frames and metadata every N frames in debug mode.
3. Add an offline evaluator script to compute confusion matrix and F1 per gesture.
4. Add a calibration capture mode for user-specific gesture prototypes and thresholds.

## Phase 2: Deterministic Rule Hardening

1. Keep the rule layer as the primary safety net.
2. Add per-gesture minimum hold frames.
3. Add a no-hand cooldown lock to suppress stale gesture carry-over.
4. Add explicit invalid-state handling for impossible finger combinations.

## Phase 3: Local Tiny AI Refinement

1. Use the prototype-based local classifier already integrated.
2. Calibrate class prototypes per user and session from a short calibration run.
3. Apply ambiguity gating with a margin threshold to reject uncertain predictions.
4. Only allow AI override when confidence and margin pass thresholds.

## Phase 4: Fusion Policy Optimization

1. Define a deterministic fusion policy:
   - Rule and AI agree: accept.
   - Rule uncertain and AI confident: accept AI.
   - Rule strong and AI weak: keep rule.
2. Add class-specific override rules:
   - PINCH_READY requires thumb and index constraints.
   - OPEN cannot override PINCH when pinch distance is low.
3. Add weighted temporal voting across the last K decisions.
4. Add explicit invalid or no-action output when confidence or margin falls below threshold.

## Phase 5: Brightness Control Stability

1. Use bounded pinch-to-brightness mapping.
2. Apply smoothing and deadband.
3. Add a slew-rate limiter for maximum change per update.
4. Add hold-on-no-hand behavior to prevent jumps on re-detection.

## Phase 6: Reliability and Operations

1. Keep camera backend and index probing with startup read validation.
2. Add runtime health counters for dropped frames, read failures, and reinit count.
3. Add alert thresholds in logs when quality degrades.

## Anti-Hallucination Guardrails

1. Never emit a gesture action from AI alone when confidence is below threshold.
2. Reject ambiguous predictions when the margin is below minimum.
3. Require temporal stability before mode transitions.
4. Keep deterministic fallback when AI is disabled or uncertain.
5. Version and lock thresholds in config for reproducibility.

## Suggested Config Tuning Order

1. `gestures.pinch_ready_threshold`
2. `ai.min_confidence`
3. `ai.min_margin`
4. `gestures.brightness_smoothing_alpha`
5. `gestures.brightness_deadband`

## Acceptance Checklist

1. All automated checks pass.
2. Validation metrics meet targets.
3. No regressions in camera startup and recovery.
4. Manual test scenarios pass:
   - neutral hand movement
   - partial occlusion
   - lighting change
   - fast transitions
5. Calibration run improves accuracy over the generic baseline on the same user.

## Next Implementation Tasks

1. Add an offline evaluator script for confusion matrix and precision, recall, and F1.
2. Add calibration mode to build user-specific prototypes.
3. Add per-gesture hold-frame configuration.
4. Add structured CSV and JSON telemetry export.
5. Add rotation-aware normalized landmark preprocessing for both rule and AI paths.
6. Add motion-history classification for dynamic gestures that should not rely on single-frame rules.
