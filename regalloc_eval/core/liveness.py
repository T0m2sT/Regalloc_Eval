"""Tiny three-address IR: generators, pretty-printer, and the liveness-based interference computation.

A program is {block: {"ins": [(kind, def, uses)], "succ": [blocks], "term": str}} plus a block order.
kind is 'def' (defines `def`, reads `uses`) or 'use' (terminator operand reads, defines nothing)."""


def liveness_edges(blocks, order):
    """Standard backward dataflow to a fixpoint, then: at every instruction defining d, d interferes with
    everything live immediately after it. Returns a set of frozenset({a, b})."""
    live_in = {b: set() for b in blocks}
    live_out = {b: set() for b in blocks}
    changed = True
    while changed:
        changed = False
        for b in reversed(order):
            out = set()
            for s in blocks[b]["succ"]:
                out |= live_in[s]
            cur = set(out)
            for kind, d, uses in reversed(blocks[b]["ins"]):
                if d is not None:
                    cur.discard(d)
                cur |= set(uses)
            if out != live_out[b] or cur != live_in[b]:
                live_out[b], live_in[b] = out, cur
                changed = True
    edges = set()
    for b in order:
        cur = set(live_out[b])
        for kind, d, uses in reversed(blocks[b]["ins"]):
            if d is not None:
                for x in cur:
                    if x != d:
                        edges.add(frozenset((d, x)))
                cur.discard(d)
            cur |= set(uses)
    return edges


def make_ir(rng, nblocks, nvars, lo, hi, back_prob):
    """Dense random IR: any variable can be used anywhere, so interference is heavy (hard liveness tasks)."""
    names = [chr(ord("a") + i) for i in range(nvars)]
    order = [f"B{i}" for i in range(nblocks)]
    blocks = {}
    for i, b in enumerate(order):
        ins = []
        for _ in range(rng.randint(lo, hi)):
            d = rng.choice(names)
            ins.append(("def", d, rng.sample(names, rng.choice([0, 1, 2]))))
        if i == nblocks - 1:
            u = rng.choice(names)
            ins.append(("use", None, [u]))
            succ, term = [], f"ret {u}"
        else:
            nxt = order[i + 1]
            earlier = order[:i]
            if earlier and rng.random() < back_prob:
                other = rng.choice(earlier)
            else:
                other = rng.choice([x for x in order if x not in (b, nxt)] or [nxt])
            if rng.random() < 0.25:
                succ, term = [nxt], f"goto {nxt}"
                ins.append(("use", None, []))
            else:
                c = rng.choice(names)
                succ, term = [nxt, other], f"if {c} goto {nxt} else {other}"
                ins.append(("use", None, [c]))
        blocks[b] = dict(ins=ins, succ=succ, term=term)
    return blocks, order, names


def make_ir_local(rng, nblocks, nvars, lo, hi, back_prob, n_global=3):
    """Realistic IR: short-lived temporaries (rotating names, operands taken from recent defs) plus a few
    long-lived 'global' variables (loop counters / accumulators) touched throughout."""
    names = [chr(ord("a") + i) for i in range(nvars)]
    glob, temps = names[:n_global], names[n_global:]
    order = [f"B{i}" for i in range(nblocks)]
    blocks, t = {}, 0
    for i, b in enumerate(order):
        ins, recent = [], []
        for _ in range(rng.randint(lo, hi)):
            if rng.random() < 0.2:
                d = rng.choice(glob)
            else:
                d, t = temps[t % len(temps)], t + rng.randint(1, 2)
            pool = recent[-4:] + ([rng.choice(glob)] if rng.random() < 0.35 else [])
            uses = rng.sample(pool, min(len(pool), rng.choice([0, 1, 2, 2])))
            ins.append(("def", d, uses))
            recent.append(d)
        cond = (recent[-1:] or glob)[0]
        if i == nblocks - 1:
            ins.append(("use", None, [cond]))
            succ, term = [], f"ret {cond}"
        else:
            nxt, earlier = order[i + 1], order[:i]
            if earlier and rng.random() < back_prob:
                other = rng.choice(earlier)
            else:
                other = rng.choice([x for x in order if x not in (b, nxt)] or [nxt])
            succ, term = [nxt, other], f"if {cond} goto {nxt} else {other}"
            ins.append(("use", None, [cond]))
        blocks[b] = dict(ins=ins, succ=succ, term=term)
    return blocks, order, names


def ir_text(blocks, order):
    out = []
    for b in order:
        out.append(f"{b}:")
        for kind, d, uses in blocks[b]["ins"][:-1]:
            rhs = "1" if not uses else (f"{uses[0]} + 1" if len(uses) == 1 else " + ".join(uses))
            out.append(f"  {d} = {rhs}")
        out.append(f"  {blocks[b]['term']}")
    return "\n".join(out)
