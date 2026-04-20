# Next Audit Generation Prompt (Findings-Aligned)

The next eligible audit finding is **AF-011** from
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

## Prompt — AF-011 Replace clause applicability status strings with an enum (Medium)

```text
You are fixing audit finding AF-011 in the `pressure_vessels` repo.

Problem:
The compliance pipeline emits clause applicability statuses as unbounded strings
(`"applicable"`, `"not_applicable"`, `"not_evaluated"`), so typo/drift can
silently propagate into downstream audit artifacts.

Conventions (apply to every audit-remediation PR):
- Work on a new branch `claude/fix-AF-011` branched from `main`.
- Keep the diff minimal and scoped to this finding.
- Run `pytest`, `./markdownlint-cli2 "**/*.md"`, and
  `python scripts/check_ci_governance.py` before committing.
- Do not introduce new runtime dependencies without adding them to
  `pyproject.toml`.
- Reference this finding in the commit body: `Fixes AF-011 per
  docs/audit_findings_2026-04-20.yaml`.

Task:
1. Introduce a `ClauseApplicabilityStatus` enum for:
   - `applicable`
   - `not_applicable`
   - `not_evaluated`
2. Enforce enum usage in compliance pipeline outputs and any
   design-basis/applicability matrix producers that feed it.
3. Update contract documentation to list authoritative allowed values.
4. Add tests that fail on invalid status values and cover serialization.
5. Last step before opening/merging the PR: update
   `docs/next_audit_generation_prompt.md` to the next eligible finding and
   update AF-011 status in `docs/audit_findings_2026-04-20.yaml`.

Out of scope (tracked separately):
- Temperature reasonability bounds work already covered by AF-010.

Deliverable: one PR touching only files needed for AF-011 remediation plus
`docs/next_audit_generation_prompt.md` and
`docs/audit_findings_2026-04-20.yaml` status updates in the final step.
```

## Upcoming queue

Pulled from `docs/audit_findings_2026-04-20.yaml` order and dependency gating:

1. **AF-011** — Replace clause applicability status strings with an enum *(this prompt)*
2. **AF-012** — Bound workflow orchestrator retry configuration
3. **AF-013** — Cite source spec for README anchor-slug algorithm

Regenerate this file after each finding merges by re-applying the selection
rule above against the updated `status` fields.
