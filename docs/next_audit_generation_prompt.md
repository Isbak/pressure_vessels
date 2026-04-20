# Next Audit Generation Prompt (Findings-Aligned)

The next eligible audit finding is **AF-015** from
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

## Prompt — AF-015 Expand CI Python matrix to cover future versions (Low)

```text
You are fixing audit finding AF-015 in the `pressure_vessels` repo.

Problem:
CI tests run on 3.11 and 3.12 only. pyproject.toml declares >=3.11 with no
upper bound, so 3.13+ users run on an untested version.

Conventions (apply to every audit-remediation PR):
- Work on a new branch `claude/fix-AF-015` branched from `main`.
- Keep the diff minimal and scoped to this finding.
- Run `pytest`, `./markdownlint-cli2 "**/*.md"`, and
  `python scripts/check_ci_governance.py` before committing.
- Do not introduce new runtime dependencies without adding them to
  `pyproject.toml`.
- Reference this finding in the commit body: `Fixes AF-015 per
  docs/audit_findings_2026-04-20.yaml`.

Task:
1. Update `.github/workflows/ci.yml` and/or `pyproject.toml` so supported
   Python versions and CI-tested versions are explicitly aligned.
2. Add a short policy note in `AGENT_GOVERNANCE.md` describing how Python
   support is declared and when CI matrix updates are required.
3. Keep the diff minimal and avoid unrelated workflow churn.
4. Ensure CI remains green across the resulting matrix.
5. Last step before opening/merging the PR: update
   `docs/next_audit_generation_prompt.md` to the next eligible finding and
   update AF-015 status in `docs/audit_findings_2026-04-20.yaml`.

Deliverable: one PR touching only files needed for AF-015 remediation plus
`docs/next_audit_generation_prompt.md` and
`docs/audit_findings_2026-04-20.yaml` status updates in the final step.
```

## Upcoming queue

Pulled from `docs/audit_findings_2026-04-20.yaml` order and dependency gating:

1. **AF-015** — Expand CI Python matrix to cover future versions *(this prompt)*

Regenerate this file after each finding merges by re-applying the selection
rule above against the updated `status` fields.
