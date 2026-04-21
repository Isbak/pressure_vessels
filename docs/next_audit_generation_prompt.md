# Next Audit Generation Prompt (Findings-Aligned)

Use this prompt to implement the **next queued audit finding: AF-020 — Narrow broad Exception catch in standards ingestion write**, recorded in `docs/audit_findings_2026-04-21.yaml`.

> Note: As of 2026-04-21, AF-016/AF-017/AF-018/AF-019 are remediated and marked `status: done` in `docs/audit_findings_2026-04-21.yaml`.

```text
You are implementing audit finding AF-020: Narrow broad Exception catch in standards ingestion write for the `pressure_vessels` repository.

Authoritative source:
- docs/audit_findings_2026-04-21.yaml

Selection rule used:
1) Choose the first finding in docs/audit_findings_2026-04-21.yaml with
   status: todo whose depends_on entries are all status: done (or empty).
2) Implement only that finding with minimal, focused changes.
3) Last step: update this prompt file and the finding status in
   docs/audit_findings_2026-04-21.yaml.

Finding context (resolved as of 2026-04-21):
- id: AF-020
- severity: medium
- area: knowledge
- depends_on: []
- file_path: src/pressure_vessels/standards_ingestion_pipeline.py
- line_numbers: [421]

Task:
1) Refactor the AF-001 atomic-write cleanup path to avoid an undocumented broad `except Exception:` pattern.
2) Keep cleanup behavior deterministic and fail-closed.
3) Preserve AF-001 concurrency guarantees and existing behavior.
4) Confirm required checks pass.
5) Set AF-020 status to `done` in docs/audit_findings_2026-04-21.yaml.
6) Regenerate this file to point to the next eligible finding.

Repository constraints:
- Keep changes minimal and focused; AF-020 only.
- Preserve governance-by-default controls from AGENT_GOVERNANCE.md.
- Do not introduce new runtime dependencies without adding them to pyproject.toml.

Required checks:
- pytest
- ./markdownlint-cli2 "**/*.md"
- python scripts/check_ci_governance.py

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test/verification commands and expected results.
```

## Upcoming audit queue (first-todo-first)

Selection rule: pick the first `status: todo` finding in
`docs/audit_findings_2026-04-21.yaml` whose `depends_on` are all `done`.

1. **AF-020** — Narrow broad Exception catch in standards ingestion write (medium, deps: none).
2. **AF-021** — Record BL-042 unblock decision in governance policy backlog (medium, deps: none).
3. **AF-023** — Surface temperature-envelope env vars in `.env.example` (low, deps: none).
4. **AF-024** — Add stub README/boundary markers to skeleton infra modules (low, deps: none).
5. **AF-025** — Configure coverage reporting for safety-critical pipelines (low, deps: none).
6. **AF-022** — Document reject benchmark category in the quality-gate contract (medium, deps: AF-017).
