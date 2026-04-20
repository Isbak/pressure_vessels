# Next Audit Generation Prompt (Findings-Aligned)

The next eligible audit finding is **AF-012** from
`docs/audit_findings_2026-04-20.yaml` (severity: medium, status: todo,
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

## Prompt — AF-012 Bound workflow orchestrator retry configuration (Medium)

```text
You are fixing audit finding AF-012 in the `pressure_vessels` repo.

Problem:
WorkflowStageSpec accepts arbitrary max_retries and fail_first_attempts values
with no sanity limit. Pathological configs (max_retries=999999) can consume
resources and trigger unnecessary escalations.

Conventions (apply to every audit-remediation PR):
- Work on a new branch `claude/fix-AF-012` branched from `main`.
- Keep the diff minimal and scoped to this finding.
- Run `pytest`, `./markdownlint-cli2 "**/*.md"`, and
  `python scripts/check_ci_governance.py` before committing.
- Do not introduce new runtime dependencies without adding them to
  `pyproject.toml`.
- Reference this finding in the commit body: `Fixes AF-012 per
  docs/audit_findings_2026-04-20.yaml`.

Task:
1. Add `WorkflowStageSpec.__post_init__` validation for bounded retry values:
   - `max_retries <= 10`
   - `fail_first_attempts <= max_retries`
   - reject negative values for both fields
2. Raise deterministic typed `ValueError` messages on invalid configs.
3. Update `docs/interfaces/workflow_orchestrator_contract.md` with the bounds.
4. Add tests for each invalid configuration and one valid upper-bound case.
5. Last step before opening/merging the PR: update
   `docs/next_audit_generation_prompt.md` to the next eligible finding and
   update AF-012 status in `docs/audit_findings_2026-04-20.yaml`.

Out of scope (tracked separately):
- Clause applicability enum work already covered by AF-011.

Deliverable: one PR touching only files needed for AF-011 remediation plus
`docs/next_audit_generation_prompt.md` and
`docs/audit_findings_2026-04-20.yaml` status updates in the final step.
```

## Upcoming queue

Pulled from `docs/audit_findings_2026-04-20.yaml` order and dependency gating:

1. **AF-012** — Bound workflow orchestrator retry configuration *(this prompt)*
2. **AF-013** — Cite source spec for README anchor-slug algorithm
3. **AF-014** — Add clause-citation docstrings to sizing-check helpers

Regenerate this file after each finding merges by re-applying the selection
rule above against the updated `status` fields.
