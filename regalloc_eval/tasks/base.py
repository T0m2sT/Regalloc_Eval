"""Shared helpers for task families. A task is a plain dict:
{id, family, aspect, prompt, instance, answer}; only `prompt` is ever sent to a model."""
import json
import random

from ..paths import REFERENCE, TASKS


def retry(fn, seed, tries=60):
    """Call fn(rng) with fresh seeds until it neither times out nor fails its own sanity assert."""
    for i in range(tries):
        try:
            return fn(random.Random(seed * 1000 + i))
        except (TimeoutError, AssertionError):
            continue
    raise RuntimeError(f"no instance for seed {seed}")


def task(tid, family, aspect, prompt, instance, answer):
    return dict(id=tid, family=family, aspect=aspect, prompt=prompt, instance=instance, answer=answer)


def write(t):
    TASKS.mkdir(parents=True, exist_ok=True)
    REFERENCE.mkdir(parents=True, exist_ok=True)
    (TASKS / f"{t['id']}.json").write_text(json.dumps(
        dict(id=t["id"], family=t["family"], aspect=t["aspect"], prompt=t["prompt"]), indent=1))
    (REFERENCE / f"{t['id']}.json").write_text(json.dumps(
        dict(id=t["id"], family=t["family"], aspect=t["aspect"], instance=t["instance"], answer=t["answer"]), indent=1))
