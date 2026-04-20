# Next Audit Generation Prompt (Findings-Aligned)

The next eligible audit finding is **AF-014** from
`docs/audit_findings_2026-04-20.yaml` (severity: low, status: todo,
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

## Prompt — AF-014 Add clause-citation docstrings to sizing-check helpers (Low)

```text
You are fixing audit finding AF-014 in the `pressure_vessels` repo.

Problem:
_build_shell_check, _build_head_check, and sibling helpers have no
docstrings linking the formula to its ASME clause (UG-27, UG-32, UG-37,
etc.). Traceability requires cross-referencing the ADR by hand.

Conventions (apply to every audit-remediation PR):
- Work on a new branch `claude/fix-AF-014` branched from `main`.
- Keep the diff minimal and scoped to this finding.
- Run `pytest`, `./markdownlint-cli2 "**/*.md"`, and
  `python scripts/check_ci_governance.py` before committing.
- Do not introduce new runtime dependencies without adding them to
  `pyproject.toml`.
- Reference this finding in the commit body: `Fixes AF-014 per
  docs/audit_findings_2026-04-20.yaml`.

Task:
1. Add one-line docstrings to each `_build_*_check` helper in
   `src/pressure_vessels/calculation_pipeline.py` and cite the governing ASME
   clause for each formula.
2. Keep behavior unchanged (documentation/traceability only).
3. Ensure each docstring is specific enough for an auditor to map helper →
   clause without reading ADR prose.
4. Optionally add a focused regression test that asserts docstrings are present.
5. Last step before opening/merging the PR: update
   `docs/next_audit_generation_prompt.md` to the next eligible finding and
   update AF-014 status in `docs/audit_findings_2026-04-20.yaml`.

Deliverable: one PR touching only files needed for AF-014 remediation plus
`docs/next_audit_generation_prompt.md` and
`docs/audit_findings_2026-04-20.yaml` status updates in the final step.
```

## Upcoming queue

Pulled from `docs/audit_findings_2026-04-20.yaml` order and dependency gating:

1. **AF-014** — Add clause-citation docstrings to sizing-check helpers *(this prompt)*
2. **AF-015** — Expand CI Python matrix to cover future versions

Regenerate this file after each finding merges by re-applying the selection
rule above against the updated `status` fields.
