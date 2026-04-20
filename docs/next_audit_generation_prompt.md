# Next Audit Generation Prompt (Findings-Aligned)

The next eligible audit finding is **AF-003** from
`docs/audit_findings_2026-04-20.yaml` (severity: critical, status: todo,
no open dependencies).

```text
Selection rule used:
1) Choose the first finding in docs/audit_findings_2026-04-20.yaml with
   status: todo (or in_progress if already claimed for active remediation).
2) Verify every depends_on entry has status: done.
3) Implement only that finding with minimal, focused changes.
4) Last step: update this prompt file and the finding status in
   docs/audit_findings_2026-04-20.yaml.
```

## Prompt — AF-003 Document and justify safety-critical rounding precision (Critical)

```text
You are fixing audit finding AF-003 in the `pressure_vessels` repo.

Problem:
`src/pressure_vessels/calculation_pipeline.py` uses `round(..., 9)` in multiple
safety-critical thickness/pressure/utilization calculations without a documented
rationale in code or ADR. This makes the precision choice non-auditable and
fragile to unreviewed changes.

Conventions (apply to every audit-remediation PR):
- Work on a new branch `claude/fix-AF-003` branched from `main`.
- Keep the diff minimal and scoped to this finding.
- Run `pytest`, `./markdownlint-cli2 "**/*.md"`, and
  `python scripts/check_ci_governance.py` before committing.
- Do not introduce new runtime dependencies without adding them to
  `pyproject.toml`.
- Reference this finding in the commit body: `Fixes AF-003 per
  docs/audit_findings_2026-04-20.yaml`.

Task:
1. Read `src/pressure_vessels/calculation_pipeline.py` and identify every
   direct `round(..., 9)` usage in sizing logic.
2. Add a single named rounding helper in the calculation module that centralizes
   this precision behavior and includes a docstring rationale suitable for audit
   review.
3. Replace direct `round(..., 9)` calls in safety-critical sizing calculations
   with the helper (minimal diff, no behavior changes).
4. Add/extend tests in `tests/test_calculation_pipeline.py` (or focused tests)
   to pin the helper behavior and at least one boundary-sensitive sizing path.
5. Add an ADR entry under `docs/decision-log/` documenting:
   - why 9 decimal places are used,
   - how this maps to engineering/manufacturing precision expectations,
   - how future changes must be reviewed.
6. If needed, minimally update `docs/interfaces/calculation_pipeline_contract.md`
   to reference the documented rounding policy.
7. Last step before opening/merging the PR: update
   `docs/next_audit_generation_prompt.md` to the next eligible finding and
   update AF-003 status in `docs/audit_findings_2026-04-20.yaml`.

Out of scope (tracked separately):
- MVP default fail-closed behavior (AF-004).
- Geometry typed input validation (AF-002).

Deliverable: one PR touching only the files needed for AF-003 remediation plus
`docs/next_audit_generation_prompt.md` and
`docs/audit_findings_2026-04-20.yaml` status updates in the final step.
```

## Upcoming queue

Pulled from `docs/audit_findings_2026-04-20.yaml` order and dependency gating:

1. **AF-003** — Document and justify safety-critical rounding precision *(this prompt)*
2. **AF-004** — Fail closed on MVP geometry defaults in production mode
3. **AF-005** — Version and source material allowables from standards packages *(depends on AF-001)*
4. **AF-006** — Validate governance exception date ordering
5. **AF-007** — Document and test design_basis deterministic_signature
6. **AF-008** — Replace inf utilization sentinel *(depends on AF-003)*

Regenerate this file after each finding merges by re-applying the selection
rule above against the updated `status` fields.
