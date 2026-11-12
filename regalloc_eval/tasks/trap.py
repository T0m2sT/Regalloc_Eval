"""Family `trap`: decide k-colorability of graphs built so that greedy simplification stalls (min degree >= k)
or so that no small clique betrays an uncolorable graph (triangle-free 4-critical core)."""
import json

from ..core import graphs
from ..core.solver import NODE_LIMIT, is_colorable
from .base import retry, task

SPECS = [  # (id, aspect, seed, builder name, n, k, colorable)
    ("trap_planted_yes", "planted k=4, colorable", 301, "planted", 36, 4, True),
    ("trap_planted_no", "planted k=4, barely uncolorable", 302, "planted", 36, 4, False),
    ("trap_planted_k5_no", "planted k=5, barely uncolorable", 303, "planted", 34, 5, False),
    ("trap_grotzsch_yes", "triangle-free core minus one edge, colorable", 304, "grotzsch", 28, 3, True),
    ("trap_grotzsch_no", "triangle-free uncolorable core (no small clique)", 305, "grotzsch", 28, 3, False),
    ("trap_grotzsch_no_big", "triangle-free uncolorable core, more padding", 306, "grotzsch", 36, 3, False),
]


def make_planted(rng, n, k, colorable):
    edges, part = graphs.planted_kpartite(rng, n, k, k)  # min degree k: nothing is trivially simplifiable
    if not colorable:  # add same-part edges until just barely uncolorable
        es = set(edges)
        same = [(a, b) for a in range(n) for b in range(a + 1, n) if part[a] == part[b] and (a, b) not in es]
        rng.shuffle(same)
        for e in same:
            es.add(e)
            if not is_colorable(n, sorted(es), k, NODE_LIMIT):
                break
        edges = sorted(es)
    assert is_colorable(n, edges, k, NODE_LIMIT) == colorable
    return dict(n=n, edges=edges, k=k, colorable=colorable)


def make_grotzsch(rng, n_total, colorable):
    """k=3. Core = Groetzsch graph (triangle-free, chromatic number 4, 4-critical: deleting any edge makes it
    3-colorable), padded with extra nodes."""
    cn, core = graphs.mycielski(5, graphs.C5)
    if colorable:
        drop = rng.randrange(len(core))
        core = core[:drop] + core[drop + 1:]
    edges = graphs.pad_and_shuffle(rng, cn, core, n_total)
    assert is_colorable(n_total, edges, 3, NODE_LIMIT) == colorable
    return dict(n=n_total, edges=edges, k=3, colorable=colorable)


def prompt(inst):
    n, k = inst["n"], inst["k"]
    return (
        f"Interference graph with {n} live ranges numbered 0..{n-1} and k={k} registers (colors 0..{k-1}). "
        "Adjacent nodes must get different colors. No spilling is allowed.\n"
        f"Edges: {json.dumps(inst['edges'])}\n"
        f"Decide whether the whole graph can be properly colored with {k} colors. "
        'End your reply with a single JSON object in a ```json block: {"colorable": true/false, "coloring": {"node": color, ...}}. '
        "If colorable is true, 'coloring' must color every node; if false, use an empty object."
    )


def build():
    out = []
    for tid, aspect, seed, kind, n, k, colorable in SPECS:
        make = (lambda r: make_planted(r, n, k, colorable)) if kind == "planted" else (lambda r: make_grotzsch(r, n, colorable))
        inst = retry(make, seed)
        out.append(task(tid, "trap", aspect, prompt(inst), inst, dict(colorable=inst["colorable"])))
    return out
