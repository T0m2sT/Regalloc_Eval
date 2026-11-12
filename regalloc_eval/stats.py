"""Offline task table (no API calls): size, proven optimum, and what a textbook Chaitin-Briggs heuristic achieves."""
import json

from .core.heuristics import chaitin_briggs
from .paths import REFERENCE, TASKS


def table():
    rows = [f"{'task':24s} {'family':10s} {'n':>3s} {'edges':>5s} {'k':>2s} {'opt':>5s} {'heur':>5s} {'prompt':>6s}  aspect"]
    for p in sorted(REFERENCE.glob("*.json")):
        r = json.loads(p.read_text())
        i, a = r["instance"], r["answer"]
        prompt = len(json.loads((TASKS / p.name).read_text())["prompt"])
        n, e, k = i.get("n", "-"), len(i.get("edges", [])), i.get("k", "-")
        opt = a.get("cost", a.get("chi", "-"))
        heur = chaitin_briggs(i["n"], i["edges"], i["k"], i["w"]) if r["family"] in ("spill", "pipeline") else "-"
        if r["family"] == "liveness":
            e = len(a["edges"])
        rows.append(f"{r['id']:24s} {r['family']:10s} {n!s:>3s} {e:>5d} {k!s:>2s} {opt!s:>5s} {heur!s:>5s} {prompt:>6d}  {r['aspect']}")
    return "\n".join(rows)
