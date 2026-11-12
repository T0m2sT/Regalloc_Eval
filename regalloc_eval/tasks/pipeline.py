"""Family `pipeline`: the end-to-end job. Derive the interference graph from IR, then pick the cheapest spills."""
import json

from ..core import graphs
from ..core.liveness import ir_text, liveness_edges, make_ir_local
from ..core.solver import NODE_LIMIT, chromatic, solve_spill
from .base import retry, task
from .prompts import IR_INTRO, RULE, SPILL_FMT_NAMES

SPECS = [  # (id, aspect, seed, (blocks, vars, min instr, max instr, back-edge prob, cost model))
    ("pipe_loops_loopcost", "IR with loops, loop-depth costs", 501, (6, 12, 3, 5, 0.5, "loop")),
    ("pipe_branchy_uniform", "IR forward branches, uniform costs", 502, (7, 13, 3, 5, 0.1, "uniform")),
    ("pipe_loops_degree", "IR with loops, cost grows with degree", 503, (8, 14, 3, 5, 0.5, "degree")),
    ("pipe_dense_skewed", "bigger IR, skewed costs", 504, (10, 18, 3, 6, 0.5, "skewed")),
]


def make_instance(rng, nblocks, nvars, lo, hi, back_prob, costmode):
    blocks, order, names = make_ir_local(rng, nblocks, nvars, lo, hi, back_prob)
    idx = {v: i for i, v in enumerate(names)}
    edges = sorted(tuple(sorted((idx[a], idx[b]))) for a, b in (tuple(e) for e in liveness_edges(blocks, order)))
    n = len(names)
    chi = chromatic(n, edges)
    assert chi >= 4
    k = chi - 1  # one register short: spilling is unavoidable
    w = graphs.costs(rng, n, edges, costmode)
    cost, ans = solve_spill(n, edges, k, w, max_nodes=NODE_LIMIT)
    assert cost is not None and cost >= 3
    text = ir_text(blocks, order)
    inst = dict(n=n, edges=edges, k=k, w=w, pre={}, names=names, ir=text)
    prompt = (f"{IR_INTRO}\n\n{text}\n\n{RULE}\n"
              f"The machine has k={k} registers (colors 0..{k-1}); interfering variables must get different registers. "
              f"Spill cost per variable: {json.dumps(dict(zip(names, w)))}.\n"
              "Build the interference graph, then choose which variables to spill (a spilled variable is removed from "
              "the graph entirely) so the rest can be properly colored with k registers, minimizing the TOTAL spill "
              "cost. Optimality is required: any cheaper valid solution beats yours.\n" + SPILL_FMT_NAMES)
    return inst, cost, ans, prompt


def build():
    out = []
    for tid, aspect, seed, args in SPECS:
        inst, cost, ans, prompt = retry(lambda r: make_instance(r, *args), seed)
        out.append(task(tid, "pipeline", aspect, prompt, inst, dict(cost=cost, coloring=ans)))
    return out
