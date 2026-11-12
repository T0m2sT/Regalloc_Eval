from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "dataset" / "tasks"          # model-visible prompts
REFERENCE = ROOT / "dataset" / "reference"  # hidden: instance + proven-correct answer
RUNS = ROOT / "results" / "runs"
