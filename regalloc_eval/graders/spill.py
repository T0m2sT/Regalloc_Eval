"""Grades `spill`, `precolored` and `pipeline`: the answer must be a VALID allocation; the score is
optimal_cost / answer_cost (1.0 only at the proven optimum). Any valid coloring is accepted, never one fixed answer."""
from .parse import extract_json, result


def grade(ref, text):
    ans = extract_json(text)
    if not isinstance(ans, dict):
        return result(0, "no parsable JSON")
    inst, opt = ref["instance"], ref["answer"]["cost"]
    n, k, w = inst["n"], inst["k"], inst["w"]
    pre = {int(a): c for a, c in inst["pre"].items()}
    names = inst.get("names")  # pipeline tasks name variables instead of numbering them
    key = {nm: i for i, nm in enumerate(names)}.__getitem__ if names else int
    try:
        spilled = {key(v) for v in ans["spilled"]}
        color = {key(v): c for v, c in ans["coloring"].items()}
    except (KeyError, TypeError, ValueError, AttributeError):
        return result(0, "bad schema")
    if not all(0 <= v < n for v in spilled | set(color)):
        return result(0, "node out of range")
    # A node with no interference edges (e.g. a variable that never occurs in the program) may be omitted from
    # 'coloring': any register works for it, so insisting on it would be a false fail. 
    touched = {v for e in inst["edges"] for v in e}
    for v in set(range(n)) - touched - spilled - set(color):
        color[v] = pre.get(v, 0)
    if spilled & set(pre):
        return result(0, "spilled a precolored node")
    if set(color) & spilled:
        return result(0, "node both spilled and colored")
    if set(color) != set(range(n)) - spilled:
        return result(0, "coloring does not cover exactly the non-spilled nodes")
    if not all(type(c) is int and 0 <= c < k for c in color.values()):
        return result(0, "color out of range")
    if any(color[v] != c for v, c in pre.items()):
        return result(0, "precolored node changed color")
    bad = [(a, b) for a, b in inst["edges"] if a in color and b in color and color[a] == color[b]]
    if bad:
        return result(0, f"conflict on edge {tuple(bad[0])}")
    cost = sum(w[v] for v in spilled)
    if cost < opt:  # impossible if the solver is exact: fail loudly
        raise AssertionError(f"cost {cost} below proven optimum {opt}: solver bug")
    return result(opt / cost, f"valid, cost {cost} vs optimal {opt}")
