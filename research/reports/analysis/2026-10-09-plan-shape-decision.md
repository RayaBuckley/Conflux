# What shape should a plan be? Graph, code, or both

Date: 2026-10-09. Status: decision support, not a decision. Read-only analysis of recorded runs;
no source, suite or result file was modified to produce it.

Owner's question: should the plan language be a graph, or something as expressive as CaMeL's
arbitrary Python code - and should we test several shapes or simply pick the most expressive one?

## 1. The three shapes already in play

| Shape | Where it lives in this repository | What it can express |
| --- | --- | --- |
| Typed plan graph | `src/conflux/planning/model.py` - `NodeKind` = `model_call`, `action_template`, `branch`, `loop`, `continue_planning`, `approval`, `delegation`, `subplan`, `terminal`; immutable `Plan` | Sequence, branch, loop, subplan, delegation, approval, re-planning |
| Inert validated code | `dynamic_code` mode emitting `ModeledProgram` (`src/conflux/planning/modeled_program.py`), parsed by `parse_modeled_program` before anything runs | Effects with declared arguments, validated against a schema; nothing executes |
| Capability-typed arbitrary code | Not present. This is CaMeL's design: a privileged model emits Python over capability-tagged values, executed by a custom interpreter that enforces policies at tool calls | Arbitrary computation over untrusted data, with the guarantee enforced per tool call |

CaMeL's own abstract (`arXiv:2503.18813`, fetched 2026-10-09) says it: "explicitly extracts the
control and data flows from the (trusted) query; therefore, the untrusted data retrieved by the LLM
can never impact the program flow", and it "uses a notion of a capability to prevent the exfiltration
of private data over unauthorized data flows by enforcing security policies when tools are called".
Its own trade-off: 77% of AgentDojo tasks solved with the guarantee against 84% undefended.

The important part for us is not "Python", it is where the guarantee lives. In CaMeL the guarantee is
**interpreter-enforced at the moment of each tool call**. That is exactly what Conflux's ITES
mediation and the capability guard already do. The plan shape does not create the guarantee in either
system; it decides what can be **validated before execution** and what can be **quantified over by a
checker**.

## 2. What the recorded runs already say

Every recorded planning run (`research/output/runs/planning-pilot-*`, plus the H100 expanded suite)
carries one observation per cell per mode. Aggregating all 30 runs (256 cells, 64 per mode):

| Mode | Cells | Utility | Security violations | Legitimate blocks | Mean authority footprint | Mean plan nodes | Mean replans | Mean output tokens | Parse failures | Program-validation failures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `reactive` | 64 | 47 | 0 | 23 | 1.83 | 1.78 | 0.44 | 15.9 | 12 | 0 |
| `dynamic` | 64 | 49 | 0 | 26 | 1.95 | 1.75 | 0.41 | 16.5 | 9 | 0 |
| `static` | 64 | 44 | 0 | 11 | 1.34 | 1.17 | 0.00 | 10.0 | 4 | 0 |
| `dynamic_code` | 64 | 29 | 0 | 4 | 0.81 | 0.73 | 0.06 | 71.9 | 0 | 7 |

Restricting to the 23 runs that reached at least four completed cells (200 cells, 50 per mode) does
not change the order: utility 45 (`reactive`), 45 (`dynamic`), 41 (`static`), 29 (`dynamic_code`);
output tokens 13.2, 12.9, 9.7, 86.8; program-validation failures 0, 0, 0, 5.

Three readings, with the caveats attached:

1. **Shape did not move security at all.** Zero security violations in every mode. This is a statement
   about mediation integrity, not about attack resistance: every recorded run models effects in
   memory ("All effects were modeled in memory" in each `table.md`), so there is no real sink to
   attack. The security property comes from mediating effects, and all four shapes are mediated.
2. **Expressiveness lost on this suite.** The code arm has the lowest utility (29/64) and the highest
   token cost by roughly 6.6x, because its extra power is mostly unused: mean plan size 0.73 nodes
   against 1.78 for `reactive`. Its failures are its own validator rejecting the emitted program
   (7 cases), not the planner failing to parse JSON.
3. **The suite cannot answer the question.** Mean plan size is between 0.7 and 1.8 nodes and the
   maximum observed anywhere is 9. A task set whose plans are one or two nodes does not reward
   expressiveness, so it cannot distinguish a graph from code. Any decision made on these numbers
   alone would be a decision about cost, not about capability.

## 3. Recommendation

**Do not choose by expressiveness, and do not choose from the current numbers.** Fix the guarantee
first, then pick the least expressive shape that can carry it.

1. **Keep the typed plan graph as the semantic core.** It is what the executor mediates, what the
   plan and delegation IR abstract, and what the bounded checker can quantify over. A fixed node
   vocabulary with bounded depth is the reason a formal result is available at all. Arbitrary code
   has no such abstraction: CaMeL's guarantee is per-call enforcement, not a property proven over
   programs.
2. **Keep code as an input syntax, never as the runtime.** The repository already does this -
   `dynamic_code` emits a `ModeledProgram` that is parsed into trusted types before anything is
   authorised - and that normalisation step is the thing to protect in tests, because it is where an
   expressive input is made safe.
3. **Run one cheap, decisive experiment before committing to a shape.** Add a control-flow-heavy
   suite where the graph and code arms can actually diverge, and run it locally (no GPU rental):
   - tasks: retry-until-success loops, data-dependent branching over untrusted values, subplan
     fan-out and join, delegation handoff with authority attenuation, plan repair after revocation,
     an ordered multi-effect chain (8 tasks);
   - arms: `reactive`, `static`, `dynamic`, `dynamic_code`, same model and prompt per task;
   - model: the local NF4 model that already completes 7/8 cells; 3 seeds; 96 cells, well within
     laptop budget;
   - metrics: utility, security violations, authority footprint per completed task, plan nodes,
     validator rejections, output tokens, replans.
4. **Decision rule.** Adopt code-as-input as the preferred planner output only if it gains at least
   20% relative utility on that suite with validator rejections at or below 10% and no increase in
   authority footprint per completed task. Otherwise the graph stays the planning language and code
   remains a tested input path.
5. **Record the outcome as an ADR.** The decision series is at `026`; this would be `027`, one page,
   carrying the measured table and the falsifier thresholds above.

## 4. Falsifiers that would change the recommendation

- The control-flow suite shows the graph arm cannot express a task at all (not just that it loses on
  utility) while code solves it: then the graph needs extending, not replacing - most likely through
  `subplan` and `continue_planning`, which already exist.
- Code wins utility at equal rejection and equal authority: adopt code as the input syntax, keep the
  graph as the authorisation and analysis core.
- Validator rejections stay above 10% for capable models: the code path is a research liability and
  should be dropped from the comparison rather than reported as a candidate.

## 5. Reproduction

```bash
python scripts/generate_flmsec_tables.py --check          # generated tables match their sources
python -m pytest tests/test_plan_ir_extensions.py -q      # plan IR surface
python -m pytest tests/test_z3_agreement_evidence.py -q   # solver/agreement evidence
```

The per-mode aggregation in section 2 reads `research/output/runs/*/result.json` directly; each
observation carries `mode`, `utility_completed`, `security_violations`, `cumulative_authority_footprint`,
`plan_nodes`, `replans`, `output_tokens`, `parse_failures` and `modeled_program_failures`.
