#!/usr/bin/env bash
# Entry point. Usage: ./run.sh <setup|build|test|stats|run|report|regrade|package> [args]
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python

case "${1:-help}" in
  setup)   python3 -m venv .venv && $PY -m pip install -q -r requirements.txt ;;
  build)   $PY -m regalloc_eval build ;;                     # regenerate dataset/ (deterministic, no API)
  test)    $PY -m unittest discover -s tests -t . ;;         # solver + grader checks (no API)
  stats)   $PY -m regalloc_eval stats ;;                     # task table: optimum vs textbook heuristic (no API)
  run)     shift; $PY -m regalloc_eval run "$@" ;;           # USES API KEYS: see README for models and cost
  report)  shift; $PY -m regalloc_eval report "$@" ;;        # summarize results/runs/<name>
  regrade) shift; $PY -m regalloc_eval regrade "$@" ;;       # re-score saved transcripts with current graders (no API)
  package) if grep -rn "TODO(author)" README.md docs; then echo "refusing to package: resolve the TODO(author) items above"; exit 1; fi &&
           mkdir -p dist && rm -f dist/regalloc-eval.zip &&
           zip -qr dist/regalloc-eval.zip . -x ".venv/*" ".env" ".git/*" "dist/*" "results/dev/*" "*__pycache__*" ".DS_Store" &&
           ls -lh dist/regalloc-eval.zip ;;
  *)       sed -n '2,2p' "$0"; echo "commands: setup build test stats run report regrade package" ;;
esac
