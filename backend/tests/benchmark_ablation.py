"""
Research Ablation Benchmark Harness for Sthira-PhysGNN.
Generates empirical comparative results against stock MediaPipe BlazePose,
producing LaTeX publication tables and JSON telemetry for pitch/presentation.

Run with:
    python tests/benchmark_ablation.py
"""
import sys
import os
import json

# Ensure backend/ is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ml.train import run_training_and_evaluation

def main():
    print("Running Sthira-PhysGNN Scientific Benchmark...")
    metrics = run_training_and_evaluation()

    # Save JSON summary
    out_json = os.path.join(os.path.dirname(__file__), "benchmark_summary.json")
    with open(out_json, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Benchmark summary exported to: {out_json}")

if __name__ == "__main__":
    main()
