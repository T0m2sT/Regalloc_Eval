"""CLI: python -m regalloc_eval <build | stats | run | report | regrade>   (tests: python -m unittest discover -s tests)"""
import argparse
from datetime import date

from . import report, runner, stats
from .paths import RUNS
from .tasks.base import write
from .tasks.registry import iter_all


def main():
    ap = argparse.ArgumentParser(prog="regalloc_eval")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="generate dataset/tasks and dataset/reference (deterministic, no API)")
    sub.add_parser("stats", help="print the task table with optimum vs heuristic (no API)")
    r = sub.add_parser("run", help="run models on tasks (USES API KEYS and costs money)")
    r.add_argument("--models", nargs="+", required=True, help="provider:model-id, e.g. anthropic:claude-haiku-5-5")
    r.add_argument("--trials", type=int, default=3)
    r.add_argument("--tasks", nargs="*", help="task ids (default: all)")
    r.add_argument("--temperature", type=float, default=1.0)
    r.add_argument("--max-tokens", type=int, default=30000, help="output cap INCLUDING hidden thinking tokens")
    r.add_argument("--name", default=f"run_{date.today()}", help="results/runs/<name>")
    rp = sub.add_parser("report", help="summarize a run")
    rp.add_argument("name")
    rg = sub.add_parser("regrade", help="re-score saved transcripts with the current graders (no API calls)")
    rg.add_argument("name")
    a = ap.parse_args()

    if a.cmd == "build":
        n = 0
        for t in iter_all():  # write each task as it is built, so a slow instance never loses finished work
            write(t)
            n += 1
            print(f"wrote {t['id']}", flush=True)
        print(f"wrote {n} tasks")
    elif a.cmd == "stats":
        print(stats.table())
    elif a.cmd == "run":
        run_dir = RUNS / a.name
        runner.run(a.models, a.trials, a.tasks, a.temperature, a.max_tokens, run_dir)
        print(report.summarize(run_dir))
    elif a.cmd == "regrade":
        print(f"re-scored {report.regrade(RUNS / a.name)} transcripts whose verdict changed")
    elif a.cmd == "report":
        print(report.summarize(RUNS / a.name))


if __name__ == "__main__":
    main()
