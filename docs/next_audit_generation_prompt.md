# Next Audit Generation Prompt (Findings-Aligned)

The next eligible audit finding is **AF-006** from
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

## Prompt — AF-006 Validate governance exception date ordering (High)

```text
You are fixing audit finding AF-006 in the `pressure_vessels` repo.

Problem:
`scripts/check_ci_governance.py` validates ISO-8601 parsing but does not assert
that `approved_at <= expires_at` for exception entries.

Conventions (apply to every audit-remediation PR):
- Work on a new branch `claude/fix-AF-006` branched from `main`.
- Keep the diff minimal and scoped to this finding.
- Run `pytest`, `./markdownlint-cli2 "**/*.md"`, and
  `python scripts/check_ci_governance.py` before committing.
- Do not introduce new runtime dependencies without adding them to
  `pyproject.toml`.
- Reference this finding in the commit body: `Fixes AF-006 per
  docs/audit_findings_2026-04-20.yaml`.

Task:
1. Add date-ordering validation for exception windows in
   `scripts/check_ci_governance.py`.
2. Fail with clear messages for `approved_at == expires_at` and
   `approved_at > expires_at`.
3. Preserve strict ISO-8601 validation behavior.
4. Add tests for equal, reversed, and malformed date cases in
   `tests/test_policy_exceptions.py`.
5. Keep behavior deterministic and avoid silently normalizing invalid data.
6. Last step before opening/merging the PR: update
   `docs/next_audit_generation_prompt.md` to the next eligible finding and
   update AF-006 status in `docs/audit_findings_2026-04-20.yaml`.

Out of scope (tracked separately):
- Deterministic design-basis signature docs/tests (AF-007).
- Calculation utilization sentinel refactor (AF-008).

Deliverable: one PR touching only files needed for AF-006 remediation plus
`docs/next_audit_generation_prompt.md` and
`docs/audit_findings_2026-04-20.yaml` status updates in the final step.
```

## Upcoming queue

Pulled from `docs/audit_findings_2026-04-20.yaml` order and dependency gating:

1. **AF-006** — Validate governance exception date ordering *(this prompt)*
2. **AF-007** — Document and test design_basis deterministic_signature
3. **AF-008** — Replace inf utilization sentinel *(depends on AF-003)*
4. **AF-009** — Typed external-pressure requirement lookup error

Regenerate this file after each finding merges by re-applying the selection
rule above against the updated `status` fields.
