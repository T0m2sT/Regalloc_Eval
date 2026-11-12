"""Grades `liveness`: the interference edge set must match exactly (score is Jaccard, but only exact passes)."""
from .parse import extract_json, result


def grade(ref, text):
    ans = extract_json(text)
    if not isinstance(ans, dict) or not isinstance(ans.get("edges"), list):
        return result(0, "no parsable JSON")
    try:
        got = {frozenset(e) for e in ans["edges"] if len(set(e)) == 2}
    except TypeError:
        return result(0, "bad schema")
    want = {frozenset(e) for e in ref["answer"]["edges"]}
    if got == want:
        return result(1, "exact edge set")
    j = len(got & want) / len(got | want)
    return result(j, f"missing {len(want - got)}, extra {len(got - want)} (Jaccard {j:.2f}); not a pass")
