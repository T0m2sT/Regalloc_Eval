"""Every grader must accept the reference answer and reject every deliberately wrong answer (no API calls)."""
import json
import unittest

from regalloc_eval.graders import grade
from regalloc_eval.paths import REFERENCE
from tests.helpers import cases, fence


class GraderTests(unittest.TestCase):
    def test_reference_accepted_and_wrong_rejected(self):
        files = sorted(REFERENCE.glob("*.json"))
        self.assertGreaterEqual(len(files), 30)
        for p in files:
            ref = json.loads(p.read_text())
            good, bads = cases(ref)
            with self.subTest(task=ref["id"]):
                self.assertTrue(grade(ref, fence(good))["passed"], "reference answer rejected")
                for b in bads:
                    self.assertFalse(grade(ref, fence(b))["passed"], f"wrong answer accepted: {b}")
                self.assertFalse(grade(ref, "I think it is colorable.")["passed"], "no JSON must fail")

    def test_alternative_optimal_answer_is_accepted(self):
        """Graders must not demand one fixed solution: renaming colors is another valid optimum."""
        ref = json.loads((REFERENCE / "spill_rand_uniform.json").read_text())
        good, _ = cases(ref)
        k = ref["instance"]["k"]
        swapped = {"spilled": good["spilled"], "coloring": {v: (c + 1) % k for v, c in good["coloring"].items()}}
        self.assertTrue(grade(ref, fence(swapped))["passed"])

    def test_isolated_nodes_may_be_omitted(self):
        """Regression (false fail found in the screening run): a node with no edges needs no register entry."""
        ref = json.loads((REFERENCE / "pipe_loops_loopcost.json").read_text())
        inst = ref["instance"]
        touched = {v for e in inst["edges"] for v in e}
        isolated = [inst["names"][v] for v in range(inst["n"]) if v not in touched]
        self.assertTrue(isolated, "this task is expected to contain a variable that never interferes")
        good, _ = cases(ref)
        trimmed = {"spilled": good["spilled"], "coloring": {v: c for v, c in good["coloring"].items() if v not in isolated}}
        self.assertTrue(grade(ref, fence(trimmed))["passed"])
        # ...but a NON-isolated node may not be omitted
        victim = next(v for v in good["coloring"] if v not in isolated)
        short = {"spilled": good["spilled"], "coloring": {v: c for v, c in good["coloring"].items() if v != victim}}
        self.assertFalse(grade(ref, fence(short))["passed"])

    def test_json_extraction_prefers_last_block(self):
        ref = json.loads((REFERENCE / "live_straight.json").read_text())
        good, _ = cases(ref)
        text = fence({"edges": []}) + "\nactually, corrected:\n" + fence(good)
        self.assertTrue(grade(ref, text)["passed"])


if __name__ == "__main__":
    unittest.main()
