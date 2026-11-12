"""Grades `chroma`: the reported k must be the exact chromatic number and the coloring must attain it."""
from .parse import extract_json, is_proper, result


def grade(ref, text):
    ans = extract_json(text)
    if not isinstance(ans, dict) or type(ans.get("k")) is not int:
        return result(0, "no parsable JSON")
    inst, chi = ref["instance"], ref["answer"]["chi"]
    if ans["k"] != chi:
        return result(0, f"said k={ans['k']}, minimum is {chi}")
    try:
        color = {int(v): c for v, c in ans["coloring"].items()}
    except (KeyError, TypeError, ValueError, AttributeError):
        return result(0, "bad coloring schema")
    if set(color) != set(range(inst["n"])) or not all(type(c) is int and 0 <= c < chi for c in color.values()):
        return result(0, "right k, but coloring incomplete or color out of range")
    if not is_proper(inst["edges"], color):
        return result(0, "right k, but improper coloring")
    return result(1, f"k={chi} with valid coloring")
