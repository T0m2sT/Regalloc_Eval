# Design

## What this is
An eval of one narrow, expert skill: **register allocation decisions**. Every task has a machine-checkable outcome
and a proven-correct reference answer, so grading needs no LLM judge.

## Data flow
```
core/ (pure algorithms)         tasks/ (one module per family)       dataset/
  graphs.py   generators   -->    spill / chroma / trap /       -->   tasks/<id>.json      prompt only (model sees this)
  liveness.py IR + dataflow       liveness / pipeline                  reference/<id>.json  instance + proven answer
  solver.py   exact B&B           build() -> task dicts
                                                                        |
providers/ (gemini, anthropic) <-- runner.py <-- tasks/<id>.json        |
        |                              |                                |
        v                              v                                v
   raw response ----------------> graders/<family>.py <-------- reference/<id>.json
                                       |
                                       v
                       results/runs/<name>/transcripts/*.json  --> report.py --> summary.txt
```

## Layers
| Layer | Path | Rule |
|---|---|---|
| Core | `regalloc_eval/core/` | Pure functions, explicit `random.Random`, no I/O. The exact solver is ground truth. `heuristics.py` is a textbook baseline for the difficulty table only, never used for grading. |
| Tasks | `regalloc_eval/tasks/` | One module per family: `SPECS` (what exists) and `build()` (how). All seeds live here. |
| Graders | `regalloc_eval/graders/` | One module per family. Grade the outcome, accept any valid optimal answer. |
| Providers | `regalloc_eval/providers/` | One module per vendor, SDK imported lazily, same `complete()` signature. |
| Harness | `runner.py`, `report.py` | Runs trials, saves a transcript per trial, summarizes. Resumable. |
| Data | `dataset/`, `results/` | Generated tasks; run outputs. `results/dev/` is scratch and never shipped. |

## Invariants
- **Deterministic dataset.** `./run.sh build` always produces byte-identical files (seeds are fixed in each family's `SPECS`).
- **Everything graded is stated in the prompt** (rule text in `tasks/prompts.py`, output schema per task).
- **Reference answers never reach the model.** Only `tasks/<id>.json` (prompt) is sent.
- **Graders are tested on right and wrong answers** (`tests/test_graders.py`) and the solver is checked against brute force.
- **Truncated responses are not failures.** A response cut off by the token cap is flagged and excluded from scores.
- **Outcome over method.** Any valid coloring at the optimal cost passes; no particular algorithm is required.
