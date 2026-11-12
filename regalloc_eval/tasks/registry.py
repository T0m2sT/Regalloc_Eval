"""The task catalogue: one module per family, each exposing build() -> [task dict]."""
from . import chroma, liveness, pipeline, spill, trap

FAMILIES = [spill, chroma, trap, liveness, pipeline]


def iter_all():
    for fam in FAMILIES:
        yield from fam.build()


def build_all():
    return list(iter_all())
