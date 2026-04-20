# Next Audit Generation Prompt (Findings-Aligned)

The next eligible audit finding is **AF-009** from
`docs/audit_findings_2026-04-20.yaml` (severity: medium, status: todo,
dependencies resolved: AF-001 is done).

```text
Selection rule used:
1) Choose the first finding in docs/audit_findings_2026-04-20.yaml with
   status: todo (or in_progress if already claimed for active remediation).
2) Verify every depends_on entry has status: done.
3) Implement only that finding with minimal, focused changes.
4) Last step: update this prompt file and the finding status in
   docs/audit_findings_2026-04-20.yaml.
```

## Prompt — AF-009 Add concurrent-write stress test for standards ingestion (Medium)

```text
You are fixing audit finding AF-009 in the `pressure_vessels` repo.

Problem:
The standards ingestion pipeline has no regression test for concurrent writes
to the same `package_id`; race behavior is not validated in CI.

Conventions (apply to every audit-remediation PR):
- Work on a new branch `claude/fix-AF-009` branched from `main`.
- Keep the diff minimal and scoped to this finding.
- Run `pytest`, `./markdownlint-cli2 "**/*.md"`, and
  `python scripts/check_ci_governance.py` before committing.
- Do not introduce new runtime dependencies without adding them to
  `pyproject.toml`.
- Reference this finding in the commit body: `Fixes AF-009 per
  docs/audit_findings_2026-04-20.yaml`.

Task:
1. Add a deterministic concurrency test for standards ingestion:
   create two near-simultaneous writes for the same `package_id`.
2. Assert exactly one succeeds and the other fails with the documented
   collision/path-exists behavior.
3. Assert no partial artifact/corruption remains on failure.
4. Keep test isolated (`tmp_path`) and fast enough for CI.
5. Last step before opening/merging the PR: update
   `docs/next_audit_generation_prompt.md` to the next eligible finding and
   update AF-009 status in `docs/audit_findings_2026-04-20.yaml`.

Out of scope (tracked separately):
- Temperature-conversion bounds/physical reasonability policy work (AF-010).

Deliverable: one PR touching only files needed for AF-009 remediation plus
`docs/next_audit_generation_prompt.md` and
`docs/audit_findings_2026-04-20.yaml` status updates in the final step.
```

## Upcoming queue

Pulled from `docs/audit_findings_2026-04-20.yaml` order and dependency gating:

1. **AF-009** — Add concurrent-write stress test for standards ingestion *(this prompt; depends on AF-001, done)*
3. **AF-010** — Bound temperature conversions with physical reasonability check
4. **AF-011** — Replace clause applicability status strings with an enum

Regenerate this file after each finding merges by re-applying the selection
rule above against the updated `status` fields.
