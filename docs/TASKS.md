# Tasks

35 tasks in 6 families. Every instance is generated from a fixed seed (`./run.sh build` reproduces the files byte for byte)
and every answer is proven by an exact solver, never by a model. The model sees only the prompt; each task states
the output schema, the interference rule, and what is graded.

## Families: what each tests and why it should be hard

| Family | Tasks | The model must... | Why a strong model can still miss |
|---|---|---|---|
| `spill` | 12 | choose the minimum-cost set of live ranges to spill so the rest fit in k registers | A weighted hitting-set problem (NP-hard). Textbook Chaitin-Briggs spills cost/degree greedily and pays up to 5.5x the optimum (see `heur` column). A model that imitates the heuristic inherits its error. |
| `precolored` | 5 | the same, with registers fixed by a calling convention | Fixed colors break symmetry, so "recolor to make room" no longer works and forced conflicts propagate. |
| `chroma` | 3 | find the minimum k and a coloring that attains it | Needs a lower-bound proof, not just a coloring. Triangle-free cores (Groetzsch, its Mycielskian) have chromatic number 4 and 5 with no clique to point at. |
| `trap` | 6 | decide k-colorability | Graphs with minimum degree >= k stall the simplify phase; uncolorable ones are either one edge away from colorable or triangle-free (no small clique betrays them). |
| `liveness` | 5 | derive the interference graph from IR, loops included | Needs a dataflow fixpoint around back edges, dead definitions that still interfere, and no interference between an instruction's operand and its result unless the operand stays live. |
| `pipeline` | 4 | derive the graph from IR, then choose the cheapest spills | Composition: one derivation slip changes the optimum. |

## Aspects (what varies inside a family)

- **Cost model** (`spill`, `precolored`, `pipeline`): uniform; growing with degree (hubs expensive, so "spill the biggest-degree node" is the wrong instinct); skewed 1..32; loop-depth weights 1/10/100.
- **Structure**: random graphs, overlapping (k+1)-cliques sharing hub nodes (hitting-set structure), interval graphs (straight-line code), large sparse graphs.
- **Precolored count**: 3 vs 8 fixed registers.
- **Scale tier** (n=56-60, 5 tasks): same families at about twice the size, to measure how accuracy falls with problem size. Optima are still proven by the exact solver (150M-node limit).
- **IR shape**: one long block, forward branches, many back edges, 12 blocks; pipeline IR uses short-lived temporaries plus a few long-lived variables.

## Task table (`./run.sh stats`)

`opt` = proven optimum (total spill cost, or chromatic number for `chroma`); `heur` = what textbook Chaitin-Briggs
(spill min cost/degree when stuck, optimistic coloring) achieves.

```
task                     family       n edges  k   opt  heur prompt  aspect
chroma_grotzsch          chroma      24    52  -     4     -    916  triangle-free chi=4 core (padded)
chroma_mycielski         chroma      30    87  -     5     -   1258  triangle-free chi=5 core (padded)
chroma_planted           chroma      26    91  -     4     -   1289  dense planted 4-partite, chi=4
live_branchy             liveness     -    45  -     -     -   1374  forward branches, few loops
live_long                liveness     -    66  -     -     -   1789  long program, 12 blocks
live_loops               liveness     -    45  -     -     -   1442  many back edges
live_loops_dense         liveness     -    65  -     -     -   1486  many back edges, more variables
live_straight            liveness     -    41  -     -     -   1126  single long basic block
pipe_branchy_uniform     pipeline    13    34  4     3     5   1939  IR forward branches, uniform costs
pipe_dense_skewed        pipeline    18    54  5     4     4   2257  bigger IR, skewed costs
pipe_loops_degree        pipeline    14    40  4    11    13   1964  IR with loops, cost grows with degree
pipe_loops_loopcost      pipeline    12    29  4    10    10   1877  IR with loops, loop-depth costs
pre_cliques              precolored  26    76  4    24     -   1628  precolored + overlapping cliques
pre_few                  precolored  28   122  4     8     -   2051  precolored: 3 fixed registers
pre_interval             precolored  30   125  5    14     -   2112  precolored + interval graph
pre_many                 precolored  28   116  4    22     -   2061  precolored: 8 fixed registers, loop costs
pre_scale                precolored  56   241  4     8     -   3380  scale n=56, random, 6 precolored
spill_cliques_degree     spill       28    87  4    40    43   1604  overlapping cliques, hubs expensive
spill_cliques_uniform    spill       24    72  4     6     9   1449  overlapping cliques (hitting-set structure)
spill_interval_loop      spill       32   135  5     8     8   2093  interval graph (straight-line code), loop-depth costs
spill_rand_degree        spill       28   113  4     5    17   1857  random graph, cost grows with degree
spill_rand_loop          spill       30   191  5     4     7   2605  random graph, loop-depth costs (1/10/100), k=5
spill_rand_skewed        spill       28   109  4     4     7   1815  random graph, skewed (1..32) costs
spill_rand_uniform       spill       26   103  4     4     5   1746  random graph, uniform costs
spill_scale_degree       spill       56   237  4    16    67   3181  scale n=56, random, cost grows with degree
spill_scale_loop         spill       60   195  3     5     9   2814  scale n=60, random, loop-depth costs, k=3
spill_scale_skewed       spill       56   262  4     5    18   3416  scale n=56, random, skewed costs
spill_scale_uniform      spill       56   252  4     6    33   3314  scale n=56, random, uniform costs
spill_sparse_large       spill       40   107  3     6    14   1847  large sparse graph, k=3
trap_grotzsch_no         trap        28    73  3     -     -   1117  triangle-free uncolorable core (no small clique)
trap_grotzsch_no_big     trap        36    91  3     -     -   1295  triangle-free uncolorable core, more padding
trap_grotzsch_yes        trap        28    66  3     -     -   1060  triangle-free core minus one edge, colorable
trap_planted_k5_no       trap        34   175  5     -     -   2088  planted k=5, barely uncolorable
trap_planted_no          trap        36   139  4     -     -   1752  planted k=4, barely uncolorable
trap_planted_yes         trap        36    87  4     -     -   1259  planted k=4, colorable
```

## Grading (see `regalloc_eval/graders/`)

All graders are code. They grade the outcome and accept any valid answer, never one fixed solution.

| Family | Pass condition | Score |
|---|---|---|
| spill, precolored, pipeline | valid allocation (proper coloring, precolored nodes kept, cover all nodes that have edges) at the proven optimal cost | optimal cost / answer cost (0 if invalid) |
| chroma | k equals the chromatic number, and the coloring is complete and proper | 0 or 1 |
| trap | verdict matches, and a "colorable" verdict carries a proper coloring | 0 or 1 |
| liveness | exact edge set | Jaccard (only an exact match passes) |

Nodes with no interference edges may be omitted from a coloring (any register works). This was added after the first
screening run showed the grader rejecting valid answers that left out variables which never occur in the program;
saved transcripts were re-scored and the fix is covered by a regression test.
