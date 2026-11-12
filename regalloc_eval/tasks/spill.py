"""Families `spill` and `precolored`: choose which live ranges to spill, at minimum total cost.
The grader checks validity and compares the cost to the proven optimum (never the method used)."""
import json

from ..core import graphs
from ..core.solver import NODE_LIMIT, solve_spill
from .base import retry, task
from .prompts import SPILL_FMT

SCALE_LIMIT = 150_000_000  # search-node budget for the scale tier

# (id, aspect, seed, structure, n, k, cost model, precolored count, generator kwargs)
SPECS = [
    ("spill_rand_uniform", "random graph, uniform costs", 101, "random", 26, 4, "uniform", 0, dict(p=0.35)),
    ("spill_rand_degree", "random graph, cost grows with degree", 102, "random", 28, 4, "degree", 0, dict(p=0.30)),
    ("spill_rand_skewed", "random graph, skewed (1..32) costs", 103, "random", 28, 4, "skewed", 0, dict(p=0.30)),
    ("spill_rand_loop", "random graph, loop-depth costs (1/10/100), k=5", 104, "random", 30, 5, "loop", 0, dict(p=0.42)),
    ("spill_cliques_uniform", "overlapping cliques (hitting-set structure)", 105, "cliques", 24, 4, "uniform", 0, dict(m=7)),
    ("spill_cliques_degree", "overlapping cliques, hubs expensive", 106, "cliques", 28, 4, "degree", 0, dict(m=9)),
    ("spill_interval_loop", "interval graph (straight-line code), loop-depth costs", 107, "interval", 32, 5, "loop", 0, {}),
    ("spill_sparse_large", "large sparse graph, k=3", 108, "random", 40, 3, "uniform", 0, dict(p=0.13)),
    ("pre_few", "precolored: 3 fixed registers", 111, "random", 28, 4, "uniform", 3, dict(p=0.30)),
    ("pre_many", "precolored: 8 fixed registers, loop costs", 112, "random", 28, 4, "loop", 8, dict(p=0.30)),
    ("pre_cliques", "precolored + overlapping cliques", 113, "cliques", 26, 4, "degree", 5, dict(m=8)),
    ("pre_interval", "precolored + interval graph", 114, "interval", 30, 5, "uniform", 5, {}),
    # scale tier: 2x larger, still solved exactly (about 40 s each); tests whether optimality survives at realistic size
    ("spill_scale_uniform", "scale n=56, random, uniform costs", 121, "random", 56, 4, "uniform", 0, dict(p=0.16, max_nodes=SCALE_LIMIT)),
    ("spill_scale_degree", "scale n=56, random, cost grows with degree", 122, "random", 56, 4, "degree", 0, dict(p=0.16, max_nodes=SCALE_LIMIT)),
    ("spill_scale_skewed", "scale n=56, random, skewed costs", 123, "random", 56, 4, "skewed", 0, dict(p=0.15, max_nodes=SCALE_LIMIT)),
    ("spill_scale_loop", "scale n=60, random, loop-depth costs, k=3", 124, "random", 60, 3, "loop", 0, dict(p=0.10, max_nodes=SCALE_LIMIT)),
    ("pre_scale", "scale n=56, random, 6 precolored", 126, "random", 56, 4, "uniform", 6, dict(p=0.16, max_nodes=SCALE_LIMIT)),
]


def make_instance(rng, structure, n, k, costmode, pre_n=0, p=0.3, m=8, min_cost=4, max_nodes=NODE_LIMIT):
    if structure == "random":
        edges = graphs.rand_graph(rng, n, p)
    elif structure == "cliques":
        edges = graphs.clique_graph(rng, n, k, m)
    elif structure == "interval":
        edges = graphs.interval_graph(rng, n)
    w = graphs.costs(rng, n, edges, costmode)
    pre = {v: rng.randrange(k) for v in rng.sample(range(n), pre_n)} if pre_n else {}
    cost, ans = solve_spill(n, edges, k, w, pre, max_nodes=max_nodes)
    assert cost is not None and cost >= min_cost  # needs real spilling to be interesting
    return dict(n=n, edges=edges, k=k, w=w, pre=pre), cost, ans


def prompt(inst):
    n, k = inst["n"], inst["k"]
    lines = [
        f"A compiler's register allocator has this interference graph: {n} live ranges numbered 0..{n-1}, "
        f"and the machine has k={k} registers (colors 0..{k-1}). Adjacent nodes must get different colors.",
        f"Edges: {json.dumps(inst['edges'])}",
        f"Spill cost per node (index = node): {json.dumps(inst['w'])}",
    ]
    if inst["pre"]:
        pre = {str(a): c for a, c in inst["pre"].items()}
        lines.append("Precolored nodes (fixed by the calling convention; they must keep this color and cannot be "
                     f"spilled): {json.dumps(pre)}")
    lines.append("Choose which nodes to spill so the remaining nodes can be properly colored with k registers, "
                 "minimizing the TOTAL spill cost. Optimality is required: any cheaper valid solution beats yours.")
    lines.append(SPILL_FMT)
    return "\n".join(lines)


def build():
    """Generator: yields each task as soon as it is solved (scale instances take a while)."""
    for tid, aspect, seed, structure, n, k, costmode, pre_n, extra in SPECS:
        tries = 12 if "max_nodes" in extra else 60  # scale tier: each failed attempt can cost ~40 s
        inst, cost, ans = retry(lambda r: make_instance(r, structure, n, k, costmode, pre_n, **extra), seed, tries)
        family = "precolored" if tid.startswith("pre_") else "spill"
        yield task(tid, family, aspect, prompt(inst), inst, dict(cost=cost, coloring=ans))
