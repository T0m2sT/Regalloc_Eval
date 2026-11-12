"""Textbook baseline, used only to explain task difficulty (never to grade)."""


def chaitin_briggs(n, edges, k, w):
    """Simplify nodes of degree < k; when stuck push the node minimizing cost/degree; color optimistically.
    Returns the total spill cost of the nodes that end up uncolored."""
    adj = [set() for _ in range(n)]
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    live, stack = set(range(n)), []
    while live:
        low = [v for v in live if len(adj[v] & live) < k]
        v = low[0] if low else min(live, key=lambda x: w[x] / max(1, len(adj[x] & live)))
        stack.append(v)
        live.discard(v)
    color, cost = {}, 0
    for v in reversed(stack):
        free = [c for c in range(k) if c not in {color[u] for u in adj[v] if u in color}]
        if free:
            color[v] = free[0]
        else:
            cost += w[v]
    return cost
