# Aggregation, Statistics, Tables, and Figures

## Core rule

No paper number should be manually typed from terminal output. Every number must flow from retained raw results -> aggregation script -> generated summary/table/plot -> manuscript input.

## Common output layout

Prefer the repository's existing evidence-bundle convention. If a new convention is needed, each run directory should contain at least:

- `manifest.json`
- `raw.jsonl` or per-cell raw JSON files
- `result.json`
- `summary.csv`
- `summary.md`
- `checksums.sha256`
- `rerun.txt`
- `claim-boundary.md`

Use existing schema names/paths instead if already canonical.

## Required aggregate tables

### T1: Historical SLED compression

Columns:

- environment;
- raw traces;
- canonical states;
- compression ratio;
- finite verdict;
- runtime where available.

Include total 1,462,607 -> 31.

### T2: Verification backend agreement

Columns:

- fixture family;
- safe/unsafe;
- native/reference verdict;
- Z3 verdict;
- COI-Z3 verdict;
- witness lifted/replayed;
- timeout/unavailable.

### T3: Mutation benchmark

Grouped by property family:

- number of mutants;
- detected native;
- detected Z3;
- detected reduced Z3;
- median witness length;
- median runtime.

### T4: Provenance precision

Rows by provenance condition. Columns:

- secure completion;
- false blocks;
- vulnerable effects;
- mean PC size;
- max PC size;
- blocked effects.

### T5: AgentDojo

Rows by defence. Separate columns for benign and attacked:

- upstream utility;
- upstream security;
- executed unauthorised-effect rate;
- model/parse failures;
- blocked malicious proposals;
- task count.

Stratify by model if more than one model is included.

### T6: Planning

Rows by planning mode:

- completion;
- authority violations;
- max PC;
- unnecessary reads;
- model calls;
- tool calls;
- latency.

## Required figures

### F1: Trace/state scaling

Use log y-axis if needed. Show trace enumeration vs canonical-state exploration.

### F2: COI/Z3 scaling

Runtime or model size vs irrelevant-variable count.

### F3: Provenance precision utility

Completion rate vs possible-author count or provenance over-approximation factor.

### F4: Planning utility/security exposure

Completion vs one authority-exposure metric.

AgentDojo may remain a table if sample size is modest.

## Statistical guidance

- Deterministic exhaustive/model-checking results do not need confidence intervals.
- For rate estimates over independent benchmark tasks, report numerator/denominator; add bootstrap 95% confidence intervals if sample size is large enough to be useful.
- For stochastic LLM runs, report seeds and either per-seed values or confidence intervals.
- Never average away unavailable/model-failed cells. Report failure counts separately.
- Runtime comparisons should use the same machine where possible and record hardware/software identity.
- Do not make strong speed claims from single runs on different hardware.

## Plot generation

Use a deterministic script under the existing research/evidence tooling. All figures should be regenerable from committed or retained result bundles without re-running models.

Use publication-readable labels and avoid embedding claims such as `PROVEN SECURE` into graphics. Prefer exact bounded language in captions.

## Visual review checklist

For every central figure/table:

- labels match terminology in `docs/reference/SECURITY_MODEL.md`;
- safe vs blocked vs failed are visually distinct;
- sample sizes are visible;
- bounds/model/backend are stated in caption or nearby text;
- plots do not truncate axes misleadingly;
- manual spot-check against raw JSON succeeds for at least 3 cells;
- generated file path and source bundle are recorded.
