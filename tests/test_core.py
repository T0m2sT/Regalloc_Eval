"""Independent known-answer checks of the exact solver and the liveness code (not circular with the dataset)."""
import random
import unittest

from regalloc_eval.core import graphs
from regalloc_eval.core.liveness import liveness_edges
from regalloc_eval.core.solver import chromatic, is_colorable, solve_spill


class SolverTests(unittest.TestCase):
    def test_triangle_two_registers_spills_cheapest(self):
        cost, ans = solve_spill(3, [(0, 1), (1, 2), (0, 2)], 2, [5, 1, 3])
        self.assertEqual(cost, 1)
        self.assertIsNone(ans[1])

    def test_precolored_conflict_is_infeasible(self):
        self.assertEqual(solve_spill(2, [(0, 1)], 2, [1, 1], pre={0: 0, 1: 0}), (None, None))

    def test_precolored_forces_spill(self):
        cost, _ = solve_spill(3, [(0, 2), (1, 2)], 2, [1, 1, 9], pre={0: 0, 1: 1})
        self.assertEqual(cost, 9)  # node 2 sees both colors; only a free node can be spilled

    def test_known_chromatic_numbers(self):
        self.assertEqual(chromatic(5, graphs.C5), 3)
        n, groetzsch = graphs.mycielski(5, graphs.C5)
        self.assertEqual((n, chromatic(n, groetzsch)), (11, 4))
        self.assertFalse(is_colorable(n, groetzsch, 3))
        for i in range(len(groetzsch)):  # 4-critical: removing any single edge makes it 3-colorable
            self.assertTrue(is_colorable(n, groetzsch[:i] + groetzsch[i + 1:], 3))
        n2, m2 = graphs.mycielski(n, groetzsch)
        self.assertEqual((n2, chromatic(n2, m2)), (23, 5))

    def test_solver_matches_brute_force(self):
        rng = random.Random(7)
        for _ in range(30):
            n, k = 7, 2
            edges = graphs.rand_graph(rng, n, 0.5)
            w = [rng.randint(1, 5) for _ in range(n)]
            best = min(
                sum(w[v] for v in range(n) if mask >> v & 1)
                for mask in range(1 << n)
                if self._two_colorable([v for v in range(n) if not mask >> v & 1], edges)
            )
            self.assertEqual(solve_spill(n, edges, k, w)[0], best)

    @staticmethod
    def _two_colorable(nodes, edges):
        keep = set(nodes)
        adj = {v: [] for v in keep}
        for a, b in edges:
            if a in keep and b in keep:
                adj[a].append(b)
                adj[b].append(a)
        color = {}
        for s in keep:
            if s in color:
                continue
            color[s], stack = 0, [s]
            while stack:
                u = stack.pop()
                for v in adj[u]:
                    if v not in color:
                        color[v] = 1 - color[u]
                        stack.append(v)
                    elif color[v] == color[u]:
                        return False
        return True


class LivenessTests(unittest.TestCase):
    def test_dead_definition_still_interferes(self):
        blocks = {"B0": dict(ins=[("def", "a", []), ("def", "b", ["a"]), ("def", "c", []), ("use", None, ["b"])], succ=[])}
        self.assertEqual(liveness_edges(blocks, ["B0"]), {frozenset("bc")})  # c is never used but is defined while b lives

    def test_loop_keeps_value_live_around_back_edge(self):
        blocks = {
            "B0": dict(ins=[("def", "a", []), ("use", None, [])], succ=["B1"]),
            "B1": dict(ins=[("def", "t", ["a"]), ("use", None, ["t"])], succ=["B1", "B2"]),
            "B2": dict(ins=[("use", None, [])], succ=[]),
        }
        # a is read on every iteration, so it is live after `t = a + 1`; a one-pass analysis would miss this edge
        self.assertEqual(liveness_edges(blocks, ["B0", "B1", "B2"]), {frozenset("at")})


if __name__ == "__main__":
    unittest.main()
