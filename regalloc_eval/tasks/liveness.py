"""Family `liveness`: derive the interference graph from IR (the model must run the dataflow, loops included)."""
from ..core.liveness import ir_text, liveness_edges, make_ir
from .base import retry, task
from .prompts import IR_INTRO, RULE

SPECS = [  # (id, aspect, seed, (blocks, vars, min instr, max instr, back-edge prob))
    ("live_straight", "single long basic block", 401, (1, 10, 22, 28, 0.0)),
    ("live_branchy", "forward branches, few loops", 402, (7, 10, 3, 5, 0.1)),
    ("live_loops", "many back edges", 403, (8, 10, 3, 5, 0.6)),
    ("live_loops_dense", "many back edges, more variables", 404, (9, 12, 3, 5, 0.6)),
    ("live_long", "long program, 12 blocks", 405, (12, 12, 4, 6, 0.5)),
]


def prompt(text):
    return (f"{IR_INTRO} Compute its register interference graph.\n\n{text}\n\n{RULE}\n"
            'End your reply with a single JSON object in a ```json block: {"edges": [["a","b"], ...]} listing each '
            "interfering pair once, using the variable names.")


def build():
    out = []
    for tid, aspect, seed, args in SPECS:
        blocks, order, _ = retry(lambda r: make_ir(r, *args), seed)
        edges = sorted(sorted(e) for e in liveness_edges(blocks, order))
        text = ir_text(blocks, order)
        out.append(task(tid, "liveness", aspect, prompt(text), dict(ir=text), dict(edges=edges)))
    return out
