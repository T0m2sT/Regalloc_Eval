"""Prompt fragments shared by several families. Everything a grader checks must be stated here or in the task."""

RULE = (
    "Rule: variables x and y interfere iff at some instruction that DEFINES x, y is live immediately after "
    "that instruction (y != x), or vice versa. Liveness is the standard backward dataflow over the whole CFG, "
    "including loops. A definition whose value is never used still interferes with every variable live after it. "
    "Terminators (goto / if / ret) define nothing; 'if c' and 'ret v' use their operand."
)
IR_INTRO = (
    "Below is a function in a simple three-address IR (no memory, no calls; every instruction is "
    "'x = y + z', 'x = y + <constant>', 'x = <constant>', or a block terminator; there are no plain copies; "
    "a variable may be read before any assignment on some path, just run the dataflow)."
)
SPILL_FMT = (
    'Final answer: end your reply with a single JSON object in a ```json block: '
    '{"spilled": [node, ...], "coloring": {"node": color, ...}}. '
    "Spilling a node removes it from the graph entirely. 'coloring' must give a color in 0..k-1 "
    "for every non-spilled node (JSON keys are node numbers as strings)."
)
SPILL_FMT_NAMES = SPILL_FMT.replace("node numbers as strings", "variable names").replace("node,", "name,").replace('"node"', '"name"')
