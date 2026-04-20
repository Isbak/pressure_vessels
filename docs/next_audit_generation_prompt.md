# Next Audit Generation Prompt (Findings-Aligned)

The next eligible audit finding is **AF-002** from
`docs/audit_findings_2026-04-20.yaml` (severity: critical, status: in_progress,
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

## Prompt — AF-002 Validate geometry adapter inputs with typed errors (Critical)

```text
You are fixing audit finding AF-002 in the `pressure_vessels` repo.

Problem:
`src/pressure_vessels/geometry_module.py:56` and `:66` cast user inputs with
raw `float(...)` conversions. Non-numeric values raise bare `ValueError`
without field-level context, and there is no upstream schema gate, so malformed
inputs crash the pipeline with unclear provenance.

Conventions (apply to every audit-remediation PR):
- Work on a new branch `claude/fix-AF-002` branched from `main`.
- Keep the diff minimal and scoped to this finding.
- Run `pytest`, `./markdownlint-cli2 "**/*.md"`, and
  `python scripts/check_ci_governance.py` before committing.
- Do not introduce new runtime dependencies without adding them to
  `pyproject.toml`.
- Reference this finding in the commit body: `Fixes AF-002 per
  docs/audit_findings_2026-04-20.yaml`.

Task:
1. Read `src/pressure_vessels/geometry_module.py` end-to-end to identify every
   numeric field conversion path for geometry inputs.
2. Introduce a typed exception `GeometryInputValidationError` in
   `src/pressure_vessels/geometry_module.py` (or the closest geometry-domain
   module) that captures field-level validation failures.
3. Add a validation helper that checks all required numeric fields before any
   float conversion and aggregates failures by field name (non-numeric, null,
   and out-of-range cases).
4. Route all geometry float conversions through the new validator so the module
   raises `GeometryInputValidationError` instead of a bare `ValueError`.
5. Update tests in `tests/test_calculation_pipeline.py` and/or a focused
   geometry test file to cover:
   - non-numeric values,
   - `None` values,
   - out-of-range values,
   - happy-path behavior unchanged for valid inputs.
6. If contract docs need clarification, minimally update
   `docs/interfaces/calculation_pipeline_contract.md` with the new error
   behavior.
7. Last step before opening/merging the PR: update
   `docs/next_audit_generation_prompt.md` to the next eligible finding and
   update AF-002 status in `docs/audit_findings_2026-04-20.yaml`.

Out of scope (tracked separately):
- MVP default fail-closed behavior (AF-004).
- Rounding precision ADR and helper extraction (AF-003).

Deliverable: one PR touching only the files needed for AF-002 remediation plus
`docs/next_audit_generation_prompt.md` and
`docs/audit_findings_2026-04-20.yaml` status updates in the final step.
```

## Upcoming queue

Pulled from `docs/audit_findings_2026-04-20.yaml` order and dependency gating:

1. **AF-002** — Validate geometry adapter inputs with typed errors *(this prompt)*
2. **AF-003** — Document and justify safety-critical rounding precision
3. **AF-004** — Fail closed on MVP geometry defaults in production mode
4. **AF-005** — Version and source material allowables from standards packages *(depends on AF-001)*
5. **AF-006** — Validate governance exception date ordering
6. **AF-008** — Replace inf utilization sentinel *(depends on AF-003)*

Regenerate this file after each finding merges by re-applying the selection
rule above against the updated `status` fields.
