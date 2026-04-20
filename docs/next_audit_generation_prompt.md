# Next Audit Generation Prompt (Findings-Aligned)

The next eligible audit finding is **AF-013** from
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

## Prompt — AF-013 Cite source spec for README anchor-slug algorithm (Low)

```text
You are fixing audit finding AF-013 in the `pressure_vessels` repo.

Problem:
The GitHub anchor-slug algorithm is reimplemented manually with no comment
linking to the upstream spec or documenting the de-dup suffix rule.

Conventions (apply to every audit-remediation PR):
- Work on a new branch `claude/fix-AF-013` branched from `main`.
- Keep the diff minimal and scoped to this finding.
- Run `pytest`, `./markdownlint-cli2 "**/*.md"`, and
  `python scripts/check_ci_governance.py` before committing.
- Do not introduce new runtime dependencies without adding them to
  `pyproject.toml`.
- Reference this finding in the commit body: `Fixes AF-013 per
  docs/audit_findings_2026-04-20.yaml`.

Task:
1. Add a docstring in `scripts/check_readme_anchors.py` that cites the
   upstream GitHub rendering/spec behavior used for anchor generation.
2. Explicitly document the duplicate-suffix rule (`-1`, `-2`, …) in the same
   docstring.
3. Keep behavior unchanged; this finding is documentation/traceability only.
4. Optionally add a focused property/regression test if it improves clarity.
5. Last step before opening/merging the PR: update
   `docs/next_audit_generation_prompt.md` to the next eligible finding and
   update AF-013 status in `docs/audit_findings_2026-04-20.yaml`.

Deliverable: one PR touching only files needed for AF-013 remediation plus
`docs/next_audit_generation_prompt.md` and
`docs/audit_findings_2026-04-20.yaml` status updates in the final step.
```

## Upcoming queue

Pulled from `docs/audit_findings_2026-04-20.yaml` order and dependency gating:

1. **AF-013** — Cite source spec for README anchor-slug algorithm *(this prompt)*
2. **AF-014** — Add clause-citation docstrings to sizing-check helpers
3. **AF-015** — Expand CI Python matrix to cover future versions

Regenerate this file after each finding merges by re-applying the selection
rule above against the updated `status` fields.
