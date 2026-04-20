# Next Audit Generation Prompt (Findings-Aligned)

There is currently **no eligible audit finding** in
`docs/audit_findings_2026-04-20.yaml`.

```text
Selection rule used:
1) Choose the first finding in docs/audit_findings_2026-04-20.yaml with
   status: todo (or in_progress if already claimed for active remediation).
2) Verify every depends_on entry has status: done.
3) Implement only that finding with minimal, focused changes.
4) Last step: update this prompt file and the finding status in
   docs/audit_findings_2026-04-20.yaml.
```

All findings in the current audit manifest are `status: done` as of 2026-04-20.
Regenerate this file when a new audit manifest is created or when any finding
is reopened.
