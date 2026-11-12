"""Builds a known-good answer and several deliberately wrong answers for each reference task."""
import copy
import json

from regalloc_eval.core.solver import solve_spill


def fence(obj):
    return "reasoning...\n```json\n" + json.dumps(obj) + "\n```"


def _spill_cases(ref):
    inst, ans = ref["instance"], ref["answer"]
    nm = inst.get("names")
    lab = (lambda v: nm[int(v)]) if nm else (lambda v: int(v))
    col = ans["coloring"]
    spilled = [lab(v) for v, c in col.items() if c is None]
    coloring = {str(lab(v)): c for v, c in col.items() if c is not None}
    good = {"spilled": spilled, "coloring": coloring}
    bads = [{"spilled": spilled}]  # bad schema
    a, b = inst["edges"][0]
    ka, kb = str(lab(a)), str(lab(b))
    if ka in coloring and kb in coloring:  # conflict on an edge
        c2 = dict(coloring)
        c2[ka] = c2[kb]
        bads.append({"spilled": spilled, "coloring": c2})
    pre = {int(v) for v in inst["pre"]}
    extra = next(v for v in range(inst["n"]) if v not in pre and str(lab(v)) in coloring)  # valid but suboptimal
    bads.append({"spilled": spilled + [lab(extra)], "coloring": {v: c for v, c in coloring.items() if v != str(lab(extra))}})
    free = [lab(v) for v in range(inst["n"]) if v not in pre]  # valid but expensive: spill everything free
    bads.append({"spilled": free, "coloring": {str(lab(v)): c for v, c in inst["pre"].items()}})
    return good, bads


def cases(ref):
    """Returns (good_answer, [wrong_answers]) for one reference task."""
    f, inst, ans = ref["family"], ref["instance"], ref["answer"]
    if f in ("spill", "precolored", "pipeline"):
        return _spill_cases(ref)
    if f == "chroma":
        _, a = solve_spill(inst["n"], inst["edges"], ans["chi"], [1] * inst["n"])
        good = {"k": ans["chi"], "coloring": {str(v): c for v, c in a.items()}}
        x, y = inst["edges"][0]
        conflict = copy.deepcopy(good)
        conflict["coloring"][str(x)] = conflict["coloring"][str(y)]
        return good, [{"k": ans["chi"] + 1, "coloring": good["coloring"]}, conflict,
                      {"k": ans["chi"] - 1, "coloring": good["coloring"]}]
    if f == "trap":
        if inst["colorable"]:
            _, a = solve_spill(inst["n"], inst["edges"], inst["k"], [1] * inst["n"])
            good = {"colorable": True, "coloring": {str(v): c for v, c in a.items()}}
            bad = copy.deepcopy(good)
            x, y = inst["edges"][0]
            bad["coloring"][str(x)] = bad["coloring"][str(y)]
            return good, [bad, {"colorable": False, "coloring": {}}]
        return {"colorable": False, "coloring": {}}, [{"colorable": True, "coloring": {}}]
    if f == "liveness":
        e = ans["edges"]
        return {"edges": e}, [{"edges": e[1:]}, {"edges": e + [["a", "zzz"]]}, {"edges": []}]
    raise ValueError(f)
