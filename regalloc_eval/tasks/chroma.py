"""Family `chroma`: find the minimum register count (a lower-bound proof) and a coloring that attains it."""
import json

from ..core import graphs
from ..core.solver import chromatic
from .base import retry, task

SPECS = [  # (id, aspect, seed, kind, n_total)
    ("chroma_grotzsch", "triangle-free chi=4 core (padded)", 201, "grotzsch", 24),
    ("chroma_mycielski", "triangle-free chi=5 core (padded)", 202, "mycielski2", 30),
    ("chroma_planted", "dense planted 4-partite, chi=4", 203, "planted", 26),
]


def make_instance(rng, kind, n_total):
    if kind == "grotzsch":
        cn, core = graphs.mycielski(5, graphs.C5)
        edges, want = graphs.pad_and_shuffle(rng, cn, core, n_total, 2, 3), 4
    elif kind == "mycielski2":  # Mycielskian of Groetzsch: 23 nodes, triangle-free, chromatic number 5
        cn, core = graphs.mycielski(*graphs.mycielski(5, graphs.C5))
        edges, want = graphs.pad_and_shuffle(rng, cn, core, n_total, 2, 3), 5
    else:  # planted 4-partite, dense enough that chi is exactly 4
        edges, _ = graphs.planted_kpartite(rng, n_total, 4, 6)
        want = 4
    chi = chromatic(n_total, edges)
    assert chi == want, (kind, chi)
    return dict(n=n_total, edges=edges), dict(chi=chi)


def prompt(inst):
    return (
        f"Interference graph with {inst['n']} live ranges numbered 0..{inst['n']-1}. Adjacent nodes must get different "
        "registers. No spilling is allowed.\n"
        f"Edges: {json.dumps(inst['edges'])}\n"
        "Find the MINIMUM number of registers k for which the whole graph can be properly colored, and give such a "
        'coloring using colors 0..k-1. End your reply with a single JSON object in a ```json block: '
        '{"k": <int>, "coloring": {"node": color, ...}} covering every node. Reporting a k that is not the true minimum fails.'
    )


def build():
    out = []
    for tid, aspect, seed, kind, n_total in SPECS:
        inst, ans = retry(lambda r: make_instance(r, kind, n_total), seed)
        out.append(task(tid, "chroma", aspect, prompt(inst), inst, ans))
    return out
