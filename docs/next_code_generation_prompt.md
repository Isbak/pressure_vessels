# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **next queued roadmap item: BL-043 — Restore green pytest baseline after 2026-04-21 audit regressions**.

```text
You are implementing backlog item **BL-043: Restore green pytest baseline after 2026-04-21 audit regressions** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-21):
- `BL-042` status is `done`.
- `BL-043` status is `todo`.
- `BL-043` has no dependencies (`depends_on: []`).
- Therefore `BL-043` is the next queued item.

Restate before coding:
- Item ID/title: BL-043 — Restore green pytest baseline after 2026-04-21 audit regressions
- depends_on: []
- acceptance criteria:
  1) `pytest -q` returns 0 failures on the audit branch before any other BL-04X work is merged.
  2) Every fix is attributable to a concrete AF-016/AF-017/AF-018/AF-019 sub-finding.
  3) CI `python-tests` and `contract-tests` jobs pass on all matrix cells.
- deliverables:
  1) Green pytest run evidence attached to the PR.
  2) Fixes routed under AF-017 (QA harness), AF-018 (contract), AF-019 (sentinel test).

Repository constraints:
- Keep changes minimal and focused; implement BL-043 only.
- Follow contract-driven integration and avoid undocumented interface drift.
- Preserve governance-by-default controls from `AGENT_GOVERNANCE.md`.
- Prefer incremental delivery over broad rewrites; keep behavior deterministic.

Likely relevant files:
- `docs/audit_findings_2026-04-21.yaml`
- `tests/test_backend_api_contract_dx005.py`
- `tests/test_contract_interfaces_dx009.py`
- `tests/test_qa_benchmark_harness.py`
- `.github/workflows/ci.yml`

Task:
1) Restore a fully green `pytest -q` baseline.
2) Map each code/test fix to AF-016/AF-017/AF-018/AF-019 in commit/PR notes.
3) Verify CI matrix expectations for `python-tests` and `contract-tests` are met.
4) Keep backlog metadata unchanged except where implementation evidence requires it.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test/verification commands and expected results.
```
