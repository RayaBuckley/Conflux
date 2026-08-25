# Review finding

```yaml
title: <concise title>
category: <confirmed_defect | research_gap | design_hypothesis | documentation_drift | cleanup | rejected>
affected_owners:
  - <canonical owner path>
evidence:
  - <path or description>
relevant_invariant: <invariant or claim ID>
why_it_matters: <1-2 sentences>
proposed_falsification: <how to test or disprove>
confidence: <high | medium | low>
likely_scope: <file | module | subsystem | repository>
external_research_needed: <true | false>
```

## Notes

- Speculative findings cannot silently become confirmed defects.
- A finding that cannot be deterministically falsified may still proceed
  as a research or design hypothesis, but must be labelled accordingly.
- The Scout must not implement findings.
