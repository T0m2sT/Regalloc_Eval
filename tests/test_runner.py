"""End-to-end harness check with a fake provider (no API): run -> grade -> transcripts -> report -> resume."""
import json
import tempfile
import unittest
from pathlib import Path

from regalloc_eval import providers, report, runner
from regalloc_eval.paths import REFERENCE
from tests.helpers import cases, fence


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.calls = 0
        self.orig = dict(providers.PROVIDERS)
        refs = {json.loads(p.read_text())["id"]: json.loads(p.read_text()) for p in REFERENCE.glob("*.json")}
        by_prompt = {}
        for tid, ref in refs.items():
            by_prompt[json.loads((REFERENCE.parent / "tasks" / f"{tid}.json").read_text())["prompt"]] = ref

        def fake(model, prompt, max_tokens, temperature):
            self.calls += 1
            good, bads = cases(by_prompt[prompt])
            answer = good if model == "perfect" else bads[0]
            finish = "MAX_TOKENS" if model == "cutoff" else "end_turn"
            return fence(answer), finish, {"input": 10, "output": 20}

        providers.PROVIDERS["fake"] = fake

    def tearDown(self):
        providers.PROVIDERS.clear()
        providers.PROVIDERS.update(self.orig)

    def test_run_report_resume(self):
        with tempfile.TemporaryDirectory() as d:
            run_dir = Path(d)
            runner.run(["fake:perfect", "fake:wrong", "fake:cutoff"], 2, ["spill_rand_uniform", "trap_planted_yes"], 1.0, 1000, run_dir)
            self.assertEqual(self.calls, 3 * 2 * 2)
            text = report.summarize(run_dir)
            self.assertIn("fake:perfect", text)
            self.assertIn("4/4 pass", text)               # perfect model passes every trial
            self.assertIn("0/4 pass", text)               # wrong model passes none
            self.assertIn("4 truncated, excluded", text)  # cut-off trials are not counted as failures
            before = self.calls
            runner.run(["fake:perfect", "fake:wrong"], 2, ["spill_rand_uniform", "trap_planted_yes"], 1.0, 1000, run_dir)
            self.assertEqual(self.calls, before)          # finished trials are reused, nothing re-requested


if __name__ == "__main__":
    unittest.main()
