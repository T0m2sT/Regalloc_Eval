# regalloc-eval: can frontier models make optimal register-allocation decisions?

An eval of one narrow compiler skill: given an interference graph (or the IR it comes from) and a register budget,
**choose which live ranges to spill, at minimum total cost.** Every task has a machine-checked answer proven by an
exact solver, so grading uses no LLM judge.

**Short description.** Domain: compiler register allocation. Gap: models handle the *mechanical* parts well (deriving
interference from IR, deciding k-colorability, finding chromatic numbers, even on triangle-free adversarial graphs) but
return **valid, not optimal** spill choices when costs are non-uniform (Haiku) or the graph is large (Sonnet, n=56): they
spill what blocks them instead of solving the weighted hitting-set problem. 35 tasks, 6 families, code-only graders.
Two Claude models tested; see [Results](#models-tested-and-results).

**Video walkthrough:** https://drive.google.com/file/d/1jd-HQhMc2jXAHWiW5FlW9q9NzifgLGF7/view?usp=sharing

## Domain and expertise

Compilers, specifically register allocation. The author built a full register allocator in C++17 for the FEUP
"Desenho de Algoritmos" course (2025/26, grade 19.5/20): live-range and web construction, interference graphs,
Chaitin-style simplification, DSATUR, spilling and live-range splitting, plus a hybrid heuristic of their own.
The task design (which traps matter, e.g. dead definitions that still interfere, calling-convention precoloring,
hitting-set structure of overlapping cliques, cost models such as loop-depth weights) comes from that work.
No code from that project is used here: the solver, generators and graders are new Python.

## What it tests and why it matters

- **Tests:** (1) spill selection and precoloring at minimum cost, (2) lower-bound reasoning (chromatic number) and
  colorability decisions, (3) liveness dataflow over loops, (4) the end-to-end composition of (3) and (1).
- **Who relies on this:** compiler and JIT engineers. A bad spill choice puts loads and stores in hot loops, so a
  "valid but suboptimal" allocation costs real runtime; a wrong interference graph yields silently miscompiled code.
- **Why a model is expected to struggle:** optimal spilling is NP-hard, and the textbook heuristic is far from optimal
  (it pays up to 5.5x the optimum on this set, see [docs/TASKS.md](docs/TASKS.md)). A model that imitates the heuristic inherits its error.

Task families, aspects and why each should be hard: [docs/TASKS.md](docs/TASKS.md). Architecture: [docs/DESIGN.md](docs/DESIGN.md).

## Setup and run

Developed and tested on Python 3.14. Pinned dependencies are in `requirements.txt`.

```bash
./run.sh setup                    # venv + dependencies
cp .env.example .env              # then put your keys in .env (never commit it)
./run.sh test                     # 12 offline tests: solver vs brute force, graders on right AND wrong answers
./run.sh build                    # regenerate dataset/ (deterministic, byte-identical)
./run.sh stats                    # task table: proven optimum vs textbook heuristic (no API)

# reproduce a run (USES API KEYS, costs money)
./run.sh run --models anthropic:claude-haiku-5-5 --trials 2 --name repro
./run.sh report repro

# no keys needed: re-score the included transcripts and re-print the results
./run.sh regrade screening && ./run.sh report screening
```

Keys: `ANTHROPIC_API_KEY` and/or `GEMINI_API_KEY` (see `.env.example`). Provider syntax is `provider:model-id`.

**Runtime and cost (measured).** The 60-trial Haiku run used 753k output tokens and 52k input tokens, about **$0.4**,
and took roughly an hour (calls are sequential and the model thinks for thousands of tokens). Thinking tokens are billed
as output, so cost is dominated by hidden reasoning, not the visible answer. The harness logs tokens per trial and
caps output at 30,000 tokens per call (`--max-tokens`).

## Models tested and results

All runs use default sampling (the SDK exposes no temperature for these models) and the IDs below. Hidden thinking
tokens count toward the output cap.

| Model ID | Tier / run | Trials | Gradable | Pass | Mean score | Output cap |
|---|---|---|---|---|---|---|
| `claude-haiku-5-5` | 30 base tasks, 2 trials (`screening`) | 60 | 53 | 38/53 (72%) | 0.90 | 30k (5 early trials 60k) |
| `claude-sonnet-5-5` | 12 weighted base tasks, 1 trial (`sonnet_weighted`) | 12 | 12 | 12/12 | 1.00 | 30k |
| `claude-sonnet-5-5` | 2 calibration calls (`sonnet_calibration`) | 2 | 2 | 2/2 | 1.00 | 30k |
| `claude-sonnet-5-5` | 5 scale tasks, n=56-60, 1 trial (`sonnet_scale`) | 5 | 4 | 1/4 | 0.55 | 30k, then 60k for reruns |

Run dates: 2026-11-01 and 2026-11-02. `pass^k` = share of tasks passed on **every** trial. Trials that hit the output cap
before giving an answer are **excluded** from the scores and reported separately. In the Haiku run, 7 of 60 trials hit
the 30k cap; they concentrate on the hardest tasks, so its table is optimistic (both `chroma_mycielski` trials are among
them). Five early Haiku trials ran under a 60k cap before it was lowered to bound cost; transcripts record the settings.

Sonnet on the scale tier (n=56-60, 1 trial per task, `results/runs/sonnet_scale/`; `pre_scale` hit even the 60k cap with no answer and is excluded). Optimum and textbook heuristic (`heur`) cost shown for comparison:

| Task | Sonnet cost | Optimum | `heur` | Score |
|---|---|---|---|---|
| `spill_scale_uniform` | 15 | 6 | 33 | 0.40 |
| `spill_scale_degree` | 63 | 16 | 67 | 0.25 |
| `spill_scale_skewed` | 9 | 5 | 18 | 0.56 |
| `spill_scale_loop` (k=3) | 5 | 5 | 9 | 1.00 (pass) |
| `pre_scale` | no answer (60k cap) | 8 | n/a | excluded |

The same model scored 12/12 at the proven optimum on the n<=40 weighted tasks (`results/runs/sonnet_weighted/`), so
accuracy falls with problem size. One trial per task, so treat this as indicative, not a rate.

By family (Haiku): chroma 4/4, trap 10/10, liveness 8/9, pipeline 7/8, **precolored 3/7, spill 6/15**.

Inside `spill`, the cost model is what separates the cases:

| Aspect | Pass | Mean score |
|---|---|---|
| random graph with uniform costs; overlapping cliques with uniform costs | 4/4 | 1.00 |
| cost grows with degree | 0/2 | 0.41 |
| skewed (1..32) costs | 0/2 | 0.44 |
| loop-depth costs (1/10/100) | 0/2 | 0.69 |
| large sparse graph | 0/1 | 0.26 |

Raw outputs: `results/runs/screening/transcripts/`. Aggregate: `results/runs/screening/summary.txt`.

## Failure analysis

Read from the saved transcripts (`results/runs/*/transcripts/`). In short: the models do not misunderstand the task, they
settle for a good valid answer where an optimal one needs search.

1. **Valid but not optimal, and the model knows it.** Every spill failure is a *valid* allocation (no conflicts) at a
   higher cost; the model typically says it "could not prove this is optimal". It never claims a false optimum.
2. **Conflict-driven greedy instead of global optimization.** The model colors, hits a node with no free color, and
   spills "the cheapest node that resolves the conflict". On `spill_rand_skewed` it spilled five cost-1 nodes plus two
   cost-2 nodes (total 9) where the optimum is 4. On `spill_rand_degree` it applied a Chaitin-style cost/degree rule
   and paid 16 against an optimum of 5, the same family of heuristic that the `heur` column shows is far from optimal.
3. **Structure helps, costs hurt.** When all costs are equal, or the structure (overlapping cliques) exposes the
   hitting set, the model succeeds. Non-uniform costs on random graphs break it.
4. **Mechanical tasks are largely solved.** Liveness, colorability and chromatic-number tasks pass (one liveness miss: the
   model added an interference edge between an instruction's operand and its result although the operand was dead
   afterwards; verified by hand against the stated rule).
5. **Scale breaks the strongest model I tested.** Sonnet is optimal on all 12 weighted tasks with n<=40 but misses three of
   four gradable n=56 tasks. All three misses are valid allocations that cost 1.8x to 3.9x the optimum, though better than
   the textbook heuristic (15 vs 33, 9 vs 18, 63 vs 67). It reasons toward a good solution but cannot prove optimality
   at this size. The one pass (`spill_scale_loop`, k=3) used 36k tokens. One trial per task: indicative only.
6. **Cost of difficulty.** The hardest instances exhaust the token budget with hidden reasoning and return nothing.

## Grader validation

- Reference answers come from an exact branch-and-bound solver, itself tested against brute force on 30 random graphs.
- `tests/test_graders.py` checks, for all 35 tasks, that the reference answer **passes** and several deliberately wrong
  answers (conflicts, suboptimal cost, spill-everything, missing fields, no JSON) **fail**, and that an alternative
  optimal answer (recolored) also passes.
- A grader false-fail was found during the first screening run (it rejected valid answers that omitted variables with
  no interference edges). It was fixed, covered by a regression test, and saved transcripts were re-scored with
  `./run.sh regrade`. No LLM judge is used anywhere.

## Prior work and sources

- The register-allocation course project (FEUP, C++17) is prior work that informed the domain; no code is reused.
- The Groetzsch and Mycielski graphs are standard constructions (they also appear in that project's adversarial dataset).
- No existing benchmark or dataset is used; all instances are synthetic and generated by `regalloc_eval/tasks/`.

## AI use

The harness, generators, solver, graders, tests and the first drafts of the docs were written with Claude Code
(Claude Sonnet 5.5). I chose the domain, defined the allocation concepts and rules, and directed the design.
I then reviewed each aspect of the tasks and the corresponding reference answers, including the interference rule in
`regalloc_eval/tasks/prompts.py`, and everything checked out. I did this review using what I learned in the FEUP
"Desenho de Algoritmos" course and while building my register allocator for it (interference graphs, liveness,
graph coloring, spilling). That course and project are prior work that informed my review; no code or data from them
is used in this eval. I also ran the available commands myself (build, tests, stats, reports) and checked that the
workflow matched what I wanted and was the approach I judged best for these tasks.
All references are proven by the exact solver, and every grader is tested on correct and wrong answers, so the code does
not rely on that manual review alone.

## Layout

```
run.sh                 setup | build | test | stats | run | report | regrade | package
regalloc_eval/         core (solver, graphs, liveness) | tasks (6 families) | graders | providers | runner | report
dataset/               tasks/ (prompts only) and reference/ (hidden answers), generated
results/runs/          transcripts + summary per run
tests/  docs/
```
