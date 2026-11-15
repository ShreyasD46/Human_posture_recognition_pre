"""
Pydantic schemas for Declarative Exercise Specifications (YAML/JSON).
"""
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field


class TargetAngle(BaseModel):
    ideal: float
    tolerance: float = 15.0
    weight: float = 1.0


class PhaseTransition(BaseModel):
    next_phase: str
    condition: str
    rollback_phase: Optional[str] = None
    rollback_condition: Optional[str] = None


class RepPhase(BaseModel):
    id: str
    description: str = ""
    target_angles: Dict[str, TargetAngle] = Field(default_factory=dict)
    transition: Optional[PhaseTransition] = None


class TargetTempo(BaseModel):
    eccentric: float = 2.0   # seconds lowering
    pause: float = 0.5       # seconds pause
    concentric: float = 1.0  # seconds lifting


class RepRules(BaseModel):
    count_on_phase: str = "completed"
    half_rep_count: bool = False
    min_rep_duration_seconds: float = 0.6
    max_rep_duration_seconds: float = 10.0
    target_tempo: Optional[TargetTempo] = None
    break_detection: bool = False
    break_arm_rest_angle: float = 165.0
    break_countdown_seconds: int = 15


class HoldRules(BaseModel):
    hold_time_target_seconds: float = 15.0
    breathing_pace_seconds: float = 4.0   # 4s inhale, 4s exhale
    pacing_guide: str = "Inhale deep, lengthen spine. Exhale, ground through feet."
    max_bad_posture_seconds: float = 180.0


class FormRule(BaseModel):
    id: str
    joint: str
    phase: Optional[str] = None  # applies to specific phase or all phases if None
    condition: str              # e.g. "angle < 150" or "deviation > tolerance"
    severity: str = "moderate"  # "minor" | "moderate" | "major"
    feedback: str
    weight: float = 0.25


class ExerciseSpec(BaseModel):
    id: str
    name: str
    category: str = "gym"  # "gym" | "yoga"
    muscle_groups: List[str] = Field(default_factory=list)
    difficulty: str = "beginner"  # "beginner" | "intermediate" | "advanced"
    camera_view: str = "front"    # "front" | "side" | "either"
    min_detection_confidence: float = 0.55
    required_joints: List[str] = Field(default_factory=list)

    # State Machine / Reps
    phases: List[RepPhase] = Field(default_factory=list)
    rep_rules: Optional[RepRules] = None
    hold_rules: Optional[HoldRules] = None

    # Biomechanical Form Rules
    form_rules: List[FormRule] = Field(default_factory=list)

    # Optional python hook
    hook_module: Optional[str] = None
    hook_function: Optional[str] = None

    # Reference demo instructions
    instructions: str = ""
    demo_animation: Optional[str] = None
