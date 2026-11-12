"""Summarize a run directory: overall, per family, per aspect, per task. Truncated trials are excluded
(a model that ran out of tokens has not failed the task) and counted separately."""
import json
from collections import defaultdict


def load(run_dir):
    recs = defaultdict(list)
    for f in sorted((run_dir / "transcripts").glob("*/*.json")):
        r = json.loads(f.read_text())
        recs[r["model"]].append(r)
    return recs


def _stats(rs):
    n = len(rs)
    return f"{sum(r['passed'] for r in rs)}/{n} pass, mean score {sum(r['score'] for r in rs) / n:.2f}"


def regrade(run_dir):
    """Re-score saved transcripts with the CURRENT graders (no API calls). Raw responses are never modified."""
    from .graders import grade
    from .paths import REFERENCE
    changed = 0
    for f in sorted((run_dir / "transcripts").glob("*/*.json")):
        r = json.loads(f.read_text())
        g = grade(json.loads((REFERENCE / f"{r['task']}.json").read_text()), r["response"])
        if (g["score"], g["passed"], g["note"]) != (r["score"], r["passed"], r["note"]):
            r.update(g)
            f.write_text(json.dumps(r, indent=1))
            changed += 1
    return changed


def summarize(run_dir):
    lines = []
    for model, rs in load(run_dir).items():
        ok = [r for r in rs if not r["truncated"]]
        lines.append(f"## {model}")
        lines.append(f"trials: {len(rs)} ({len(rs) - len(ok)} truncated, excluded); dates: {sorted({r['date'] for r in rs})}")
        if not ok:
            continue
        by_task = defaultdict(list)
        for r in ok:
            by_task[r["task"]].append(r)
        pk = sum(all(r["passed"] for r in v) for v in by_task.values()) / len(by_task)
        tok = {k: sum(r["usage"].get(k, 0) for r in rs) for k in ("input", "output")}
        lines.append(f"overall: {_stats(ok)}; pass^k (all trials pass) {pk:.0%}; tokens in={tok['input']} out={tok['output']}")
        for title, key in (("family", "family"), ("aspect", "aspect")):
            groups = defaultdict(list)
            for r in ok:
                groups[(r["family"], r["aspect"]) if key == "aspect" else r["family"]].append(r)
            lines.append(f"by {title}:")
            for g, v in sorted(groups.items()):
                label = f"{g[0]}: {g[1]}" if key == "aspect" else g
                lines.append(f"  {label}: {_stats(v)}")
        lines.append("by task:")
        for t, v in sorted(by_task.items()):
            lines.append(f"  {t}: {_stats(v)}")
        lines.append("")
    text = "\n".join(lines)
    (run_dir / "summary.txt").write_text(text)
    return text
