"""Run tasks against models, grade each trial, and save one transcript per (model, task, trial).
Each trial is a fresh single request (no shared history). Re-running resumes from saved transcripts."""
import json
import time

from . import providers
from .config import load_env
from .graders import grade
from .paths import REFERENCE, TASKS


def is_truncated(finish):
    return "MAX_TOKENS" in finish.upper()


def run(models, trials, task_ids, temperature, max_tokens, run_dir):
    """models: ["provider:model-id", ...]. Writes run_dir/transcripts/<provider>_<model>/<task>_t<i>.json."""
    load_env()
    tasks = [json.loads(p.read_text()) for p in sorted(TASKS.glob("*.json")) if not task_ids or p.stem in task_ids]
    refs = {t["id"]: json.loads((REFERENCE / f"{t['id']}.json").read_text()) for t in tasks}
    for spec in models:
        provider, model = spec.split(":", 1)
        tdir = run_dir / "transcripts" / f"{provider}_{model.replace('/', '_')}"
        tdir.mkdir(parents=True, exist_ok=True)
        for t in tasks:
            for trial in range(trials):
                f = tdir / f"{t['id']}_t{trial}.json"
                if f.exists() and not is_truncated(json.loads(f.read_text()).get("finish_reason", "MAX_TOKENS")):
                    continue  # resume: keep finished trials, redo truncated ones
                try:
                    text, finish, usage = providers.complete(provider, model, t["prompt"], max_tokens, temperature)
                except Exception as e:  # keep going; rerunning resumes from saved trials
                    print(f"{spec} {t['id']} t{trial}: SKIPPED ({type(e).__name__}: {str(e)[:100]})", flush=True)
                    continue
                g = grade(refs[t["id"]], text)
                rec = dict(task=t["id"], family=t["family"], aspect=t["aspect"], model=spec, trial=trial,
                           date=time.strftime("%Y-%m-%d"), temperature=temperature, finish_reason=finish,
                           truncated=is_truncated(finish), usage=usage, prompt=t["prompt"], response=text, **g)
                f.write_text(json.dumps(rec, indent=1))
                print(f"{spec} {t['id']} t{trial}: score={g['score']:.2f} pass={g['passed']} | {g['note']}", flush=True)
