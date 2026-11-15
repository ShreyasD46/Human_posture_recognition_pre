# Guide: Adding New Exercises & Poses

The AI Fitness Coach features a fully declarative plugin system. Any fitness trainer or engineer can add a new exercise in minutes by creating a single YAML file in `exercises/gym/` or `exercises/yoga/` without altering core engine code.

---

## 1. Step-by-Step Tutorial: Adding Dumbbell Shoulder Press

1. Create a new YAML file: `exercises/gym/shoulder_press.yaml`.
2. Populate the declarative schema:

```yaml
id: shoulder_press
name: Dumbbell Overhead Shoulder Press
category: gym
muscle_groups: [anterior_deltoids, lateral_deltoids, triceps]
difficulty: intermediate
camera_view: front
min_detection_confidence: 0.55
required_joints: [left_elbow, right_elbow, left_shoulder]
instructions: "Sit or stand with dumbbells at ear height (elbows at 90 degrees). Press overhead until arms are nearly straight, then lower under control."

phases:
  - id: ready
    description: Dumbbells at shoulder height, elbows at 90 degrees
    target_angles:
      left_elbow: { ideal: 90.0, tolerance: 15.0, weight: 0.5 }
      right_elbow: { ideal: 90.0, tolerance: 15.0, weight: 0.5 }
    transition:
      next_phase: pressing
      condition: "left_elbow > 105 and right_elbow > 105"

  - id: pressing
    description: Pressing weight overhead
    transition:
      next_phase: contracted
      condition: "left_elbow >= 160 and right_elbow >= 160"
      rollback_phase: ready
      rollback_condition: "left_elbow < 85 and right_elbow < 85"

  - id: contracted
    description: Full extension overhead
    target_angles:
      left_elbow: { ideal: 165.0, tolerance: 10.0, weight: 0.5 }
      right_elbow: { ideal: 165.0, tolerance: 10.0, weight: 0.5 }
    transition:
      next_phase: lowering
      condition: "left_elbow < 150 and right_elbow < 150"

  - id: lowering
    description: Controlled eccentric lowering
    transition:
      next_phase: ready
      condition: "left_elbow <= 95 and right_elbow <= 95"

rep_rules:
  count_on_phase: ready
  half_rep_count: false
  min_rep_duration_seconds: 0.8
  target_tempo:
    eccentric: 2.0
    pause: 0.5
    concentric: 1.0

form_rules:
  - id: uneven_press
    joint: left_elbow
    condition: "abs(left_elbow - right_elbow) > 25"
    severity: moderate
    feedback: "Fix Form: Press both arms upward simultaneously"
    weight: 0.35
```

3. **Verify Registration:**
Run the test command:
```bash
python -c "from exercises.registry import registry; print(registry.get('shoulder_press').name)"
```
4. The exercise automatically appears in the UI catalog and is available for workout sessions immediately!
