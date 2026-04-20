# Next Audit Generation Prompt (Findings-Aligned)

The next eligible audit finding is **AF-008** from
`docs/audit_findings_2026-04-20.yaml` (severity: high, status: todo,
dependencies resolved: AF-003 is done).

```text
Selection rule used:
1) Choose the first finding in docs/audit_findings_2026-04-20.yaml with
   status: todo (or in_progress if already claimed for active remediation).
2) Verify every depends_on entry has status: done.
3) Implement only that finding with minimal, focused changes.
4) Last step: update this prompt file and the finding status in
   docs/audit_findings_2026-04-20.yaml.
```

## Prompt — AF-008 Replace inf utilization sentinel with explicit invalid record (High)

```text
You are fixing audit finding AF-008 in the `pressure_vessels` repo.

Problem:
`utilization` is set to `float('inf')` when provided thickness is zero in
calculation checks. Downstream tooling can mis-handle `inf`, and JSON `inf`
serialization is non-standard.

Conventions (apply to every audit-remediation PR):
- Work on a new branch `claude/fix-AF-008` branched from `main`.
- Keep the diff minimal and scoped to this finding.
- Run `pytest`, `./markdownlint-cli2 "**/*.md"`, and
  `python scripts/check_ci_governance.py` before committing.
- Do not introduce new runtime dependencies without adding them to
  `pyproject.toml`.
- Reference this finding in the commit body: `Fixes AF-008 per
  docs/audit_findings_2026-04-20.yaml`.

Task:
1. Replace `float('inf')` utilization sentinel paths with explicit invalid
   record semantics in `src/pressure_vessels/calculation_pipeline.py`
   (for example: `utilization_ratio = null` + deterministic reason code).
2. Keep JSON output spec-compliant and deterministic.
3. Update the calculation interface contract to document the new invalid-path
   representation and any schema changes.
4. Add focused regression tests covering zero and negative provided-thickness
   behavior and threshold comparison handling.
5. Preserve existing behavior for valid (>0) provided-thickness cases.
5. Last step before opening/merging the PR: update
   `docs/next_audit_generation_prompt.md` to the next eligible finding and
   update AF-008 status in `docs/audit_findings_2026-04-20.yaml`.

Out of scope (tracked separately):
- Design-basis deterministic signature documentation/fixture work (AF-007).

Deliverable: one PR touching only files needed for AF-008 remediation plus
`docs/next_audit_generation_prompt.md` and
`docs/audit_findings_2026-04-20.yaml` status updates in the final step.
```

## Upcoming queue

Pulled from `docs/audit_findings_2026-04-20.yaml` order and dependency gating:

1. **AF-008** — Replace inf utilization sentinel *(this prompt; depends on AF-003, done)*
2. **AF-009** — Typed external-pressure requirement lookup error
3. **AF-010** — Bound temperature conversions with physical reasonability check
4. **AF-011** — Replace clause applicability status strings with an enum

Regenerate this file after each finding merges by re-applying the selection
rule above against the updated `status` fields.
