"""Interference-graph generators and spill-cost models (all take an explicit `random.Random`)."""

C5 = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 4)]


def rand_graph(rng, n, p):
    return sorted((a, b) for a in range(n) for b in range(a + 1, n) if rng.random() < p)


def clique_graph(rng, n, k, m):
    """m overlapping (k+1)-cliques sharing a few 'hub' nodes, plus light noise: every clique forces a spill,
    so the optimum is a weighted hitting-set problem, not a per-node greedy choice."""
    hubs = rng.sample(range(n), max(3, n // 6))
    rest = [v for v in range(n) if v not in hubs]
    es = set()
    for _ in range(m):
        members = rng.sample(hubs, 2) + rng.sample(rest, k - 1)
        es |= {tuple(sorted((a, b))) for i, a in enumerate(members) for b in members[i + 1:]}
    es |= {e for e in rand_graph(rng, n, 0.04)}
    return sorted(es)


def interval_graph(rng, n, horizon=60):
    """Live ranges of straight-line code: nodes are intervals, edges are overlaps."""
    iv = []
    for _ in range(n):
        s = rng.randint(0, horizon - 4)
        iv.append((s, s + rng.randint(3, horizon // 4)))
    return sorted((a, b) for a in range(n) for b in range(a + 1, n) if iv[a][0] < iv[b][1] and iv[b][0] < iv[a][1])


def mycielski(n, edges):
    """Mycielskian: triangle-free-preserving construction that raises the chromatic number by one."""
    es = list(edges) + [(a, n + b) for a, b in edges] + [(b, n + a) for a, b in edges] + [(n + i, 2 * n) for i in range(n)]
    return 2 * n + 1, sorted(tuple(sorted(e)) for e in es)


def pad_and_shuffle(rng, n, edges, n_total, lo=2, hi=4):
    """Attach extra nodes to a core graph, then relabel randomly so the core is not recognizable by index."""
    es = set(edges)
    for v in range(n, n_total):
        for u in rng.sample(range(v), rng.randint(lo, hi)):
            es.add((u, v))
    perm = list(range(n_total))
    rng.shuffle(perm)
    return sorted(tuple(sorted((perm[a], perm[b]))) for a, b in es)


def planted_kpartite(rng, n, k, min_deg):
    """Graph with a hidden proper k-coloring where every node has degree >= min_deg."""
    part = [i % k for i in range(n)]
    rng.shuffle(part)
    cand = [(a, b) for a in range(n) for b in range(a + 1, n) if part[a] != part[b]]
    rng.shuffle(cand)
    edges, deg = set(), [0] * n
    for a, b in cand:
        if deg[a] < min_deg or deg[b] < min_deg:
            edges.add((a, b))
            deg[a] += 1
            deg[b] += 1
    return sorted(edges), part


def degrees(n, edges):
    d = [0] * n
    for a, b in edges:
        d[a] += 1
        d[b] += 1
    return d


def costs(rng, n, edges, mode):
    """Spill-cost models. 'degree' makes hubs expensive, so 'spill the highest-degree node' is the wrong instinct."""
    d = degrees(n, edges)
    if mode == "uniform":
        return [rng.randint(1, 9) for _ in range(n)]
    if mode == "degree":
        return [max(1, round(d[v] * rng.uniform(0.6, 1.4))) for v in range(n)]
    if mode == "skewed":
        return [rng.choice([1, 1, 2, 2, 4, 8, 16, 32]) for _ in range(n)]
    if mode == "loop":  # loop-depth style weights 10^depth
        return [rng.choice([1, 1, 1, 10, 10, 100]) for _ in range(n)]
    raise ValueError(mode)
