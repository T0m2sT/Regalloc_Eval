"""Exact solvers: the ground truth behind every reference answer and grader."""

NODE_LIMIT = 4_000_000  # generator guard: abort instances the exact solver cannot settle quickly


def solve_spill(n, edges, k, w, pre=None, max_nodes=None):
    """Min total spill weight so the non-spilled nodes are properly k-colored.

    pre: {node: color} precolored nodes (fixed, cannot be spilled).
    Returns (cost, {node: color or None}) or (None, None) if infeasible.
    max_nodes: raise TimeoutError after this many search nodes (generator guard).
    Branch and bound; fine for the n <= ~40 instances used here.
    """
    pre = pre or {}
    adj = [set() for _ in range(n)]
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    for a in pre:
        for b in adj[a]:
            if b in pre and pre[a] == pre[b]:
                return None, None
    free = sorted((v for v in range(n) if v not in pre), key=lambda v: -len(adj[v]))
    best = [float("inf"), None]
    assign = dict(pre)  # node -> color or None (spilled)
    seen = [0]

    def rec(i, cost, used):
        seen[0] += 1
        if max_nodes and seen[0] > max_nodes:
            raise TimeoutError
        if cost >= best[0]:
            return
        if i == len(free):
            best[0], best[1] = cost, dict(assign)
            return
        v = free[i]
        taken = {assign[u] for u in adj[v] if assign.get(u) is not None}
        # symmetry breaking (only valid without precolored nodes): open at most one new color
        for c in range(k if pre else min(k, used + 1)):
            if c in taken:
                continue
            assign[v] = c
            rec(i + 1, cost, max(used, c + 1))
            del assign[v]
        assign[v] = None
        rec(i + 1, cost + w[v], used)
        del assign[v]

    rec(0, 0, 0)
    if best[1] is None:
        return None, None
    return best[0], {v: best[1].get(v) for v in range(n)}


def is_colorable(n, edges, k, max_nodes=None):
    cost, _ = solve_spill(n, edges, k, [1] * n, max_nodes=max_nodes)
    return cost == 0


def chromatic(n, edges, top=8, max_nodes=NODE_LIMIT):
    """Smallest k for which the graph is colorable (raises AssertionError above `top`)."""
    for k in range(1, top):
        if is_colorable(n, edges, k, max_nodes):
            return k
    raise AssertionError("chromatic number too large")
