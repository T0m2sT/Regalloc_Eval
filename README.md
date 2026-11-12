# Regalloc_Eval

> Can frontier models make optimal register-allocation decisions?

An eval of one narrow compiler skill: given an interference graph and a register budget, **choose which live ranges to spill at minimum cost.** Every answer is proven by an exact solver. No LLM judge.

**Core finding:** Models handle the mechanical parts well (deriving interference from IR, deciding k-colorability, finding chromatic numbers, even on triangle-free adversarial graphs) but return **valid, not optimal** spill choices when costs are non-uniform or the graph is large. They spill what blocks them instead of solving the weighted hitting-set problem.

**Video walkthrough:** https://drive.google.com/file/d/1jd-HQhMc2jXAHWiW5FlW9q9NzifgLGF7/view?usp=sharing

---

## Domain

Compilers assign program variables to a fixed set of CPU registers. When more variables are live at once than registers are available, some must be spilled to memory. The choice of which to spill at what cost is equivalent to a weighted hitting-set problem - NP-hard.

The textbook Chaitin-Briggs heuristic spills by cost/degree greedily when stuck. On this dataset it pays up to **5.5x the proven optimum.** A model that imitates the heuristic inherits its error.

The author built a full register allocator in C++17 for the FEUP "Desenho de Algoritmos" course (2025/26, grade 19.5/20): live-range and web construction, interference graphs, Chaitin-style simplification, DSATUR, spilling and live-range splitting, plus a hybrid heuristic. The task design comes from that work. No code from that project is used here: the solver, generators and graders are new Python.

---

## Benchmark - 6 Families, 35 Tasks

Every instance is generated from a fixed seed (`./run.sh build` reproduces byte-for-byte). Reference answers come from an exact branch-and-bound solver, itself tested against brute force on 30 random graphs.

| Family | Tasks | The model must... | Why it should be hard |
|---|---|---|---|
| `spill` | 12 | choose the minimum-cost set of live ranges to spill so the rest fit in k registers | Weighted hitting-set (NP-hard). Textbook Chaitin-Briggs pays up to 5.5x the optimum. |
| `precolored` | 5 | same, with registers fixed by a calling convention | Fixed colors break symmetry; forced conflicts propagate. |
| `chroma` | 3 | find the minimum k and a coloring that attains it | Needs a lower-bound proof. Triangle-free cores (Groetzsch, Mycielski) have no clique to cite. |
| `trap` | 6 | decide k-colorability | Min degree >= k stalls simplification; uncolorable ones are triangle-free. |
| `liveness` | 5 | derive the interference graph from IR, loops included | Needs a dataflow fixpoint around back edges; dead definitions still interfere. |
| `pipeline` | 4 | derive the graph from IR, then choose the cheapest spills | Composition: one derivation slip changes the optimum. |

### Aspects (what varies inside a family)

- **Cost model** (`spill`, `precolored`, `pipeline`): uniform; growing with degree; skewed 1..32; loop-depth weights 1/10/100.
- **Structure**: random graphs, overlapping (k+1)-cliques, interval graphs, large sparse graphs.
- **Scale tier** (n=56-60, 5 tasks): same families at ~2x size; optima still proven by the exact solver.
- **IR shape**: long block, forward branches, many back edges, 12 blocks.

### Full task table (`./run.sh stats`)

`opt` = proven optimum; `heur` = textbook Chaitin-Briggs baseline.

```
task                     family       n edges  k   opt  heur  aspect
chroma_grotzsch          chroma      24    52  -     4     -   triangle-free chi=4 core (padded)
chroma_mycielski         chroma      30    87  -     5     -   triangle-free chi=5 core (padded)
chroma_planted           chroma      26    91  -     4     -   dense planted 4-partite, chi=4
live_branchy             liveness     -    45  -     -     -   forward branches, few loops
live_long                liveness     -    66  -     -     -   long program, 12 blocks
live_loops               liveness     -    45  -     -     -   many back edges
live_loops_dense         liveness     -    65  -     -     -   many back edges, more variables
live_straight            liveness     -    41  -     -     -   single long basic block
pipe_branchy_uniform     pipeline    13    34  4     3     5   IR forward branches, uniform costs
pipe_dense_skewed        pipeline    18    54  5     4     4   bigger IR, skewed costs
pipe_loops_degree        pipeline    14    40  4    11    13   IR with loops, cost grows with degree
pipe_loops_loopcost      pipeline    12    29  4    10    10   IR with loops, loop-depth costs
pre_cliques              precolored  26    76  4    24     -   precolored + overlapping cliques
pre_few                  precolored  28   122  4     8     -   precolored: 3 fixed registers
pre_interval             precolored  30   125  5    14     -   precolored + interval graph
pre_many                 precolored  28   116  4    22     -   precolored: 8 fixed registers, loop costs
pre_scale                precolored  56   241  4     8     -   scale n=56, random, 6 precolored
spill_cliques_degree     spill       28    87  4    40    43   overlapping cliques, hubs expensive
spill_cliques_uniform    spill       24    72  4     6     9   overlapping cliques (hitting-set structure)
spill_interval_loop      spill       32   135  5     8     8   interval graph, loop-depth costs
spill_rand_degree        spill       28   113  4     5    17   random graph, cost grows with degree
spill_rand_loop          spill       30   191  5     4     7   random graph, loop-depth costs, k=5
spill_rand_skewed        spill       28   109  4     4     7   random graph, skewed (1..32) costs
spill_rand_uniform       spill       26   103  4     4     5   random graph, uniform costs
spill_scale_degree       spill       56   237  4    16    67   scale n=56, cost grows with degree
spill_scale_loop         spill       60   195  3     5     9   scale n=60, loop-depth costs, k=3
spill_scale_skewed       spill       56   262  4     5    18   scale n=56, skewed costs
spill_scale_uniform      spill       56   252  4     6    33   scale n=56, uniform costs
spill_sparse_large       spill       40   107  3     6    14   large sparse graph, k=3
trap_grotzsch_no         trap        28    73  3     -     -   triangle-free uncolorable core
trap_grotzsch_no_big     trap        36    91  3     -     -   triangle-free uncolorable core, more padding
trap_grotzsch_yes        trap        28    66  3     -     -   triangle-free core minus one edge, colorable
trap_planted_k5_no       trap        34   175  5     -     -   planted k=5, barely uncolorable
trap_planted_no          trap        36   139  4     -     -   planted k=4, barely uncolorable
trap_planted_yes         trap        36    87  4     -     -   planted k=4, colorable
```

---

## Results

All runs use default sampling. Hidden thinking tokens count toward the output cap and are billed as output. Trials that hit the cap before returning an answer are **excluded** from scores.

| Model | Run | Gradable | Pass | Mean score |
|---|---|---|---|---|
| `claude-haiku-5-5` | screening (30 tasks, 2 trials) | 53 / 60 | 38/53 (72%) | 0.90 |
| `claude-sonnet-5-5` | sonnet_weighted (12 tasks, 1 trial) | 12 / 12 | 12/12 (100%) | 1.00 |
| `claude-sonnet-5-5` | sonnet_calibration (2 tasks) | 2 / 2 | 2/2 (100%) | 1.00 |
| `claude-sonnet-5-5` | sonnet_scale (n=56-60, 5 tasks) | 4 / 5 | 1/4 (25%) | 0.55 |

Run dates: 2026-11-01 and 2026-11-02.

### Haiku - by family

| Family | Pass | Mean score |
|---|---|---|
| chroma | 4/4 | 1.00 |
| trap | 10/10 | 1.00 |
| liveness | 8/9 | ~0.98 |
| pipeline | 7/8 | ~0.95 |
| precolored | 3/7 | ~0.80 |
| spill | 6/15 | ~0.80 |

### Haiku - spill family by cost model

| Aspect | Pass | Mean score |
|---|---|---|
| uniform costs | 4/4 | 1.00 |
| cost grows with degree | 0/2 | 0.41 |
| skewed (1..32) costs | 0/2 | 0.44 |
| loop-depth costs (1/10/100) | 0/2 | 0.69 |

### Sonnet - scale tier (n=56-60) vs optimum and heuristic

| Task | Sonnet cost | Optimum | Heuristic | Score |
|---|---|---|---|---|
| `spill_scale_uniform` | 15 | 6 | 33 | 0.40 |
| `spill_scale_degree` | 63 | 16 | 67 | 0.25 |
| `spill_scale_skewed` | 9 | 5 | 18 | 0.56 |
| `spill_scale_loop` | 5 | 5 | 9 | 1.00 |
| `pre_scale` | no answer (60k cap) | 8 | - | excluded |

Sonnet scores 12/12 at the proven optimum on n<=40 weighted tasks but misses 3 of 4 gradable n=56 tasks. All misses are valid allocations (1.8x to 3.9x the optimum), better than the heuristic. One trial per task: indicative only.

---

## Failure Analysis

Read from saved transcripts in `results/runs/*/transcripts/`. Models do not misunderstand the task; they settle for valid answers where optimal ones need search.

1. **Valid but not optimal, and the model knows it.** Every spill failure is a valid allocation at a higher cost. The model typically says it "could not prove this is optimal." It never claims a false optimum.

2. **Conflict-driven greedy instead of global optimization.** The model colors, hits a node with no free color, and spills "the cheapest node that resolves the conflict." On `spill_rand_skewed` it spilled 7 nodes (total cost 9) where the optimum is 4. On `spill_rand_degree` it applied a Chaitin-style cost/degree rule and paid 16 against an optimum of 5.

3. **Structure helps, non-uniform costs hurt.** When all costs are equal, or the structure (overlapping cliques) exposes the hitting set, the model succeeds. Non-uniform costs on random graphs break it.

4. **Mechanical tasks are largely solved.** Liveness, colorability and chromatic-number tasks pass. One liveness miss: the model added an interference edge between an instruction's operand and its result although the operand was dead afterwards.

5. **Scale breaks the strongest model tested.** Sonnet is optimal on all 12 weighted n<=40 tasks but misses 3 of 4 gradable n=56 tasks. The hardest instances exhaust the token budget with hidden reasoning and return nothing.

---

## Grading

All graders are code. They grade the outcome and accept any valid answer, never one fixed solution.

| Family | Pass condition | Score |
|---|---|---|
| spill, precolored, pipeline | valid allocation at the proven optimal cost | optimal cost / answer cost (0 if invalid) |
| chroma | k equals the chromatic number and the coloring is proper | 0 or 1 |
| trap | verdict matches; a "colorable" verdict carries a proper coloring | 0 or 1 |
| liveness | exact interference edge set | Jaccard (exact match only passes) |

Nodes with no interference edges may be omitted from a coloring (any register works). Added after the first screening run showed the grader rejecting valid answers that left out variables which never appear in the program; saved transcripts were re-scored and the fix is covered by a regression test.

---

## Architecture

```
core/ (pure algorithms)       tasks/ (one module per family)      dataset/
  graphs.py   generators  -->   spill / chroma / trap /      -->  tasks/<id>.json      prompt only
  liveness.py IR dataflow       liveness / pipeline               reference/<id>.json  proven answer
  solver.py   exact B&B

providers/ (anthropic, gemini) <-- runner.py <-- tasks/<id>.json
        |
        v
   raw response --> graders/<family>.py <-- reference/<id>.json
                          |
                          v
          results/runs/<name>/transcripts/*.json --> report.py --> summary.txt
```

| Layer | Path | Rule |
|---|---|---|
| Core | `regalloc_eval/core/` | Pure functions, explicit `random.Random`, no I/O. Solver is ground truth. |
| Tasks | `regalloc_eval/tasks/` | One module per family: `SPECS` and `build()`. All seeds live here. |
| Graders | `regalloc_eval/graders/` | One module per family. Grade the outcome, accept any valid optimal answer. |
| Providers | `regalloc_eval/providers/` | One module per vendor, same `complete()` signature. |
| Harness | `runner.py`, `report.py` | Runs trials, saves a transcript per trial, summarizes. Resumable. |

**Invariants:**
- `./run.sh build` always produces byte-identical files (seeds are fixed in each family's `SPECS`).
- Reference answers never reach the model - only `tasks/<id>.json` is sent.
- Graders are tested on right and wrong answers (`tests/test_graders.py`).
- Truncated responses are excluded from scores, not failed.

---

## Setup

Developed and tested on Python 3.14. Pinned dependencies in `requirements.txt`.

```bash
./run.sh setup                    # venv + dependencies
cp .env.example .env              # then add your keys (ANTHROPIC_API_KEY and/or GEMINI_API_KEY)

# no keys needed
./run.sh test                     # 12 offline tests: solver vs brute force, graders on right + wrong answers
./run.sh build                    # regenerate dataset/ (deterministic, byte-identical)
./run.sh stats                    # task table: proven optimum vs textbook heuristic

# reproduce a run (uses API keys, costs money)
./run.sh run --models anthropic:claude-haiku-5-5 --trials 2 --name repro
./run.sh report repro

# re-score included transcripts (no keys needed)
./run.sh regrade screening && ./run.sh report screening
```

**Runtime and cost (measured):** The 60-trial Haiku run used 753k output tokens and 52k input tokens, about **$0.40**, and took roughly an hour. Thinking tokens are billed as output, so cost is dominated by hidden reasoning. The harness logs tokens per trial and caps output at 30,000 tokens per call (`--max-tokens`).

---

## Repository Layout

```
run.sh                 setup | build | test | stats | run | report | regrade | package
regalloc_eval/         core/ | tasks/ | graders/ | providers/ | runner | report | stats
dataset/               tasks/ (prompts only) and reference/ (hidden answers), generated
results/runs/          transcripts + summary per run
tests/                 offline tests: solver vs brute-force, graders on right + wrong answers
docs/                  TASKS.md (full task table + grading) | DESIGN.md (architecture)
```

---

## Prior Work and AI Use

The register-allocation course project (FEUP, C++17) is prior work that informed the domain; no code is reused. The Groetzsch and Mycielski graphs are standard constructions. No existing benchmark or dataset is used; all instances are synthetic.

The harness, generators, solver, graders, tests and first drafts of the docs were written with Claude Code (Claude Sonnet 5.5). The domain, allocation concepts and rules, and overall design direction came from the author. All reference answers are proven by the exact solver, and every grader is tested on correct and wrong answers.
