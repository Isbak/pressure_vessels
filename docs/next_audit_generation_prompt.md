# Next Audit Generation Prompt (Findings-Aligned)

The next eligible audit finding is **AF-007** from
`docs/audit_findings_2026-04-20.yaml` (severity: high, status: todo,
dependencies resolved: none).

```text
Selection rule used:
1) Choose the first finding in docs/audit_findings_2026-04-20.yaml with
   status: todo (or in_progress if already claimed for active remediation).
2) Verify every depends_on entry has status: done.
3) Implement only that finding with minimal, focused changes.
4) Last step: update this prompt file and the finding status in
   docs/audit_findings_2026-04-20.yaml.
```

## Prompt — AF-007 Document and test design_basis deterministic_signature (High)

```text
You are fixing audit finding AF-007 in the `pressure_vessels` repo.

Problem:
`design_basis.deterministic_signature` is consumed by downstream calculation
logic but its construction (input fields, hashing algorithm, ordering rules)
is not documented and has no frozen regression fixture.

Conventions (apply to every audit-remediation PR):
- Work on a new branch `claude/fix-AF-007` branched from `main`.
- Keep the diff minimal and scoped to this finding.
- Run `pytest`, `./markdownlint-cli2 "**/*.md"`, and
  `python scripts/check_ci_governance.py` before committing.
- Do not introduce new runtime dependencies without adding them to
  `pyproject.toml`.
- Reference this finding in the commit body: `Fixes AF-007 per
  docs/audit_findings_2026-04-20.yaml`.

Task:
1. Document deterministic signature construction in
   `src/pressure_vessels/design_basis_pipeline.py` and
   `docs/interfaces/compliance_pipeline_contract.md`.
2. Add a regression test with a frozen canonical fixture to pin signature
   output.
3. If renaming the field is necessary, keep backward-compatible aliasing for
   one release.
4. Keep behavior deterministic and avoid changing unrelated pipelines.
5. Last step before opening/merging the PR: update
   `docs/next_audit_generation_prompt.md` to the next eligible finding and
   update AF-007 status in `docs/audit_findings_2026-04-20.yaml`.

Out of scope (tracked separately):
- Calculation utilization sentinel refactor (AF-008).

Deliverable: one PR touching only files needed for AF-007 remediation plus
`docs/next_audit_generation_prompt.md` and
`docs/audit_findings_2026-04-20.yaml` status updates in the final step.
```

## Upcoming queue

Pulled from `docs/audit_findings_2026-04-20.yaml` order and dependency gating:

1. **AF-007** — Document and test design_basis deterministic_signature *(this prompt)*
2. **AF-008** — Replace inf utilization sentinel *(depends on AF-003)*
3. **AF-009** — Typed external-pressure requirement lookup error
4. **AF-010** — Bound temperature conversions with physical reasonability check

Regenerate this file after each finding merges by re-applying the selection
rule above against the updated `status` fields.
