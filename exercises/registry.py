"""
Exercise Plugin Registry and Declarative YAML Loader.
"""
import os
import glob
import yaml
from typing import Dict, List, Optional
from core.models.exercise_spec import ExerciseSpec


class ExerciseRegistry:
    """Central registry for all declarative gym exercises and yoga poses."""

    def __init__(self, base_dirs: Optional[List[str]] = None):
        if base_dirs is None:
            here = os.path.dirname(os.path.abspath(__file__))
            self.base_dirs = [
                os.path.join(here, "gym"),
                os.path.join(here, "yoga"),
            ]
        else:
            self.base_dirs = base_dirs

        self._exercises: Dict[str, ExerciseSpec] = {}
        self.load_all()

    def load_all(self):
        self._exercises.clear()
        for directory in self.base_dirs:
            if not os.path.exists(directory):
                continue
            yaml_files = glob.glob(os.path.join(directory, "*.yaml")) + glob.glob(os.path.join(directory, "*.yml"))
            for yf in yaml_files:
                try:
                    with open(yf, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    if isinstance(data, dict) and "id" in data:
                        spec = ExerciseSpec(**data)
                        self._exercises[spec.id] = spec
                except Exception as e:
                    print(f"[ExerciseRegistry] Warning: Failed to parse {yf}: {e}")

    def get(self, exercise_id: str) -> Optional[ExerciseSpec]:
        return self._exercises.get(exercise_id)

    def list_all(self, category: Optional[str] = None) -> List[ExerciseSpec]:
        all_specs = list(self._exercises.values())
        if category:
            return [s for s in all_specs if s.category.lower() == category.lower()]
        return all_specs

    def register(self, spec: ExerciseSpec):
        self._exercises[spec.id] = spec


# Global default singleton registry
registry = ExerciseRegistry()
