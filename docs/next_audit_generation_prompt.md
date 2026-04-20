# Next Audit Generation Prompt (Findings-Aligned)

The next eligible audit finding is **AF-005** from
`docs/audit_findings_2026-04-20.yaml` (severity: high, status: todo,
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

## Prompt — AF-005 Version and source material allowables from standards packages (High)

```text
You are fixing audit finding AF-005 in the `pressure_vessels` repo.

Problem:
`src/pressure_vessels/materials_module.py` currently uses hardcoded material
allowables with no standards package version/effective-date metadata.
Allowables can drift from ASME updates without traceable provenance.

Conventions (apply to every audit-remediation PR):
- Work on a new branch `claude/fix-AF-005` branched from `main`.
- Keep the diff minimal and scoped to this finding.
- Run `pytest`, `./markdownlint-cli2 "**/*.md"`, and
  `python scripts/check_ci_governance.py` before committing.
- Do not introduce new runtime dependencies without adding them to
  `pyproject.toml`.
- Reference this finding in the commit body: `Fixes AF-005 per
  docs/audit_findings_2026-04-20.yaml`.

Task:
1. Replace hardcoded allowables with standards-package-backed material data.
2. Add `standards_package_id` and `effective_date` (or equivalent deterministic
   provenance fields) to each material record.
3. Surface these provenance fields in calculation/compliance artifacts.
4. Add/adjust tests for missing/expired package paths and metadata propagation.
5. Update docs/contracts to describe standards-backed material resolution.
6. Last step before opening/merging the PR: update
   `docs/next_audit_generation_prompt.md` to the next eligible finding and
   update AF-005 status in `docs/audit_findings_2026-04-20.yaml`.

Out of scope (tracked separately):
- Governance exception date ordering (AF-006).
- Deterministic design-basis signature docs/tests (AF-007).

Deliverable: one PR touching only files needed for AF-005 remediation plus
`docs/next_audit_generation_prompt.md` and
`docs/audit_findings_2026-04-20.yaml` status updates in the final step.
```

## Upcoming queue

Pulled from `docs/audit_findings_2026-04-20.yaml` order and dependency gating:

1. **AF-005** — Version and source material allowables from standards packages *(this prompt; depends on AF-001 done)*
2. **AF-006** — Validate governance exception date ordering
3. **AF-007** — Document and test design_basis deterministic_signature
4. **AF-008** — Replace inf utilization sentinel *(depends on AF-003)*
5. **AF-009** — Typed external-pressure requirement lookup error

Regenerate this file after each finding merges by re-applying the selection
rule above against the updated `status` fields.
