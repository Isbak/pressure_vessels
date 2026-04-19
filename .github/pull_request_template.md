## Summary

## Risk Class

- [ ] Low
- [ ] Medium
- [ ] High

## Agent Attribution

- [ ] Codex
- [ ] Claude Code
- [ ] Both

## Governance Checklist (AGENT_GOVERNANCE.md#10)

- [ ] Risk class selected (low/medium/high)
- [ ] Agent author identified (Codex / Claude Code / both)
- [ ] Independent cross-agent review complete (required for medium/high)
- [ ] Required tests executed and attached
- [ ] Security/secret scan passed
- [ ] Required human approvals obtained
- [ ] Rollback plan included (required for medium/high)

## Governance Evidence Artifacts (DX-007)

- CI workflow artifact bundle: `governance-gate-report`
- Machine-readable checklist payload: `artifacts/ci/GovernanceChecklistEvidence.v1.json`
- Governance gate report: `artifacts/ci/GovernanceGateReport.v1.json`
- Gate status payload: `artifacts/ci/job-results.json`
- [ ] Linked evidence artifact(s) in PR comments/description (or attached equivalent)
