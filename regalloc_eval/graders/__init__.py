"""Code-based graders. They grade the OUTCOME (validity + optimality), never the reasoning path."""
from . import chroma, liveness, spill, trap

GRADERS = {
    "spill": spill.grade, "precolored": spill.grade, "pipeline": spill.grade,
    "chroma": chroma.grade, "trap": trap.grade, "liveness": liveness.grade,
}


def grade(ref, text):
    return GRADERS[ref["family"]](ref, text)
