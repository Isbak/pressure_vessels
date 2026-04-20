# Next Audit Generation Prompt (Findings-Aligned)

The next eligible audit finding is **AF-010** from
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

## Prompt — AF-010 Bound temperature conversions with physical reasonability check (Medium)

```text
You are fixing audit finding AF-010 in the `pressure_vessels` repo.

Problem:
The requirements pipeline accepts any normalized temperature value without
physical reasonability bounds, allowing implausible design temperatures to pass
as valid.

Conventions (apply to every audit-remediation PR):
- Work on a new branch `claude/fix-AF-010` branched from `main`.
- Keep the diff minimal and scoped to this finding.
- Run `pytest`, `./markdownlint-cli2 "**/*.md"`, and
  `python scripts/check_ci_governance.py` before committing.
- Do not introduce new runtime dependencies without adding them to
  `pyproject.toml`.
- Reference this finding in the commit body: `Fixes AF-010 per
  docs/audit_findings_2026-04-20.yaml`.

Task:
1. Add a configurable physical reasonability bounds check after temperature
   conversion in requirements processing.
2. Default bounds to a sensible engineering range (e.g., -196 C to 650 C) and
   fail closed when outside bounds.
3. Document how bounds are configured/overridden.
4. Add tests for interior, boundary, and out-of-range inputs.
5. Last step before opening/merging the PR: update
   `docs/next_audit_generation_prompt.md` to the next eligible finding and
   update AF-010 status in `docs/audit_findings_2026-04-20.yaml`.

Out of scope (tracked separately):
- Any standards-ingestion concurrency work already covered by AF-009.

Deliverable: one PR touching only files needed for AF-010 remediation plus
`docs/next_audit_generation_prompt.md` and
`docs/audit_findings_2026-04-20.yaml` status updates in the final step.
```

## Upcoming queue

Pulled from `docs/audit_findings_2026-04-20.yaml` order and dependency gating:

1. **AF-010** — Bound temperature conversions with physical reasonability check *(this prompt)*
2. **AF-011** — Replace clause applicability status strings with an enum
3. **AF-012** — Add strict schema checks for dossier export payload completeness

Regenerate this file after each finding merges by re-applying the selection
rule above against the updated `status` fields.
