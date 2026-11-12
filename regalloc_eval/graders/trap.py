"""Grades `trap`: the colorable/uncolorable verdict must match, and a 'colorable' verdict needs a valid coloring."""
from .parse import extract_json, is_proper, result


def grade(ref, text):
    ans = extract_json(text)
    if not isinstance(ans, dict) or not isinstance(ans.get("colorable"), bool):
        return result(0, "no parsable JSON")
    inst = ref["instance"]
    if ans["colorable"] != inst["colorable"]:
        return result(0, f"said colorable={ans['colorable']}, truth {inst['colorable']}")
    if not inst["colorable"]:
        return result(1, "correctly uncolorable")
    try:
        color = {int(v): c for v, c in ans["coloring"].items()}
    except (KeyError, TypeError, ValueError, AttributeError):
        return result(0, "bad coloring schema")
    if set(color) != set(range(inst["n"])) or not all(type(c) is int and 0 <= c < inst["k"] for c in color.values()):
        return result(0, "coloring incomplete or color out of range")
    if not is_proper(inst["edges"], color):
        return result(0, "improper coloring")
    return result(1, "valid coloring")
