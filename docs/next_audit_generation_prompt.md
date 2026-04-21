# Next Audit Generation Prompt (Findings-Aligned)
 
There is currently **no eligible audit finding** in
`docs/audit_findings_2026-04-20.yaml`.
Use this prompt to implement the **next queued audit finding: AF-016 — Restore green pytest baseline by triaging 2026-04-21 failing tests**, recorded in `docs/audit_findings_2026-04-21.yaml`.
 
> Note: As of 2026-04-21, `docs/audit_findings_2026-04-20.yaml` is fully remediated (all entries `status: done`). The 2026-04-21 full-repo audit produced a fresh manifest at `docs/audit_findings_2026-04-21.yaml` with AF-016..AF-025 (1 critical, 2 high, 4 medium, 3 low).
 
```text
You are implementing audit finding AF-016: Restore green pytest baseline by
triaging 2026-04-21 failing tests for the `pressure_vessels` repository.
 
Authoritative sources:
- docs/audit_findings_2026-04-21.yaml
- docs/development_backlog.yaml (BL-043 umbrella item)
 
Selection rule used:
1) Choose the first finding in docs/audit_findings_2026-04-20.yaml with
   status: todo (or in_progress if already claimed for active remediation).
2) Verify every depends_on entry has status: done.
3) Implement only that finding with minimal, focused changes.
4) Last step: update this prompt file and the finding status in
   docs/audit_findings_2026-04-20.yaml.
1) Choose the first finding in docs/audit_findings_2026-04-21.yaml with
   status: todo whose depends_on entries are all status: done (or empty).
2) Implement only that finding with minimal, focused changes.
3) Last step: update this prompt file and the finding status in
   docs/audit_findings_2026-04-21.yaml.
 
Finding context (resolved as of 2026-04-21):
- id: AF-016
- severity: critical
- area: quality
- depends_on: []
- related sub-findings: AF-017 (QA harness reject category), AF-018
  (frontend/backend contract drift), AF-019 (sentinel-test pattern)
- backlog linkage: BL-043 (umbrella), BL-044 (AF-017), BL-045 (AF-021)
 
Failing tests observed at audit start (pytest -q on claude/audit-setup-update-docs-PmLuP):
- tests/test_backend_api_contract_dx005.py::test_bl040_is_done_and_next_prompt_advances_to_bl041
- tests/test_contract_interfaces_dx009.py::test_frontend_backend_contract_shapes_remain_compatible
- tests/test_qa_benchmark_harness.py::test_cross_verification_harness_is_deterministic_and_passing
- tests/test_qa_benchmark_harness.py::test_quality_gate_report_artifact_is_written_with_stable_payload
 
Task:
1) Classify each failure as stale-test vs. real-code regression.
2) Fix real-code regressions (AF-017: QA harness handles reject-category
   fixtures without KeyError('input')).
3) Rewrite stale tests so they are not pinned to sprint-local sentinels
   (AF-018: contract test realigned to DesignRunRequest; AF-019:
   next-prompt test derives the expected BL id from the backlog).
4) Confirm `pytest -q` exits 0 on the audit branch.
5) Set AF-016 (and the closed sub-findings) status to `done` in
   docs/audit_findings_2026-04-21.yaml.
6) Regenerate this file to point to the next eligible finding.
 
Repository constraints:
- Keep changes minimal and focused; AF-016 only plus its unblocked children.
- Follow contract-driven integration; do not rewrite the contracts to match
  stale tests. Update the tests to match the current contracts and modules.
- Preserve governance-by-default controls from AGENT_GOVERNANCE.md.
- Do not introduce new runtime dependencies without adding them to
  pyproject.toml.
 
Required checks before closing AF-016:
- pytest
- ./markdownlint-cli2 "**/*.md"
- python scripts/check_ci_governance.py
 
Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test/verification commands and expected results.
```
 
All findings in the current audit manifest are `status: done` as of 2026-04-20.
Regenerate this file when a new audit manifest is created or when any finding
is reopened.
## Upcoming audit queue (first-todo-first)
 
Selection rule: pick the first `status: todo` finding in
`docs/audit_findings_2026-04-21.yaml` whose `depends_on` are all `done`.
 
1. **AF-016** — Restore green pytest baseline (critical, deps: none).
2. **AF-017** — Handle reject-category fixtures in QA benchmark harness (high, deps: AF-016).
3. **AF-018** — Realign frontend/backend contract test with DesignRunRequest (high, deps: AF-016).
4. **AF-019** — Decouple next-prompt sentinel tests from sprint-local BL ids (medium, deps: AF-016).
5. **AF-020** — Narrow broad Exception catch in standards ingestion write (medium, deps: none).
6. **AF-021** — Record BL-042 unblock decision in governance policy backlog (medium, deps: none).
7. **AF-022** — Document reject benchmark category in the quality-gate contract (medium, deps: AF-017).
8. **AF-023** — Surface temperature-envelope env vars in `.env.example` (low, deps: none).
9. **AF-024** — Add stub README/boundary markers to skeleton infra modules (low, deps: none).
10. **AF-025** — Configure coverage reporting for safety-critical pipelines (low, deps: none).
Regenerate this file whenever any finding changes status.
