# Full Repository Audit — 2026-04-18

## Scope

Audited the entire repository contents under `/workspace/pressure_vessels`, including root governance files, workflow configuration, and all documentation assets.

## Method

1. Enumerated repository files.
2. Reviewed all Markdown/YAML/workflow files for consistency and governance alignment.
3. Ran lightweight automated checks for local link integrity and README anchor reference validity from the backlog.

## Executive Summary

The repository is a strong **documentation-first project scaffold** with clear intent around architecture, governance, and roadmaping. The largest gaps are in:

- **traceability consistency** between backlog references and README anchors,
- **enforcement depth** in CI compared with declared governance controls,
- minor documentation hygiene issues.

Overall assessment: **Foundational baseline is solid, but operational controls are not yet fully implemented.**

## Detailed Findings

### F1 — Backlog contains broken README anchor references (Medium)

**Evidence:** automated check against README heading-derived anchors found 7 unresolved references in `docs/development_backlog.yaml`.

Broken references:

- `README.md#end-to-end-workflow`
- `README.md#calculation-engine`
- `README.md#standards-ingestion-new-codes-and-updates`
- `README.md#certification-readiness-features` (appears twice)
- `README.md#optimization-agent-optional`
- `README.md#suggested-tech-stack-example`

**Impact:** weakens machine-readable traceability and may break tooling that validates roadmap-to-doc links.

**Recommended fix:** normalize referenced anchors to README’s actual generated slug format (which currently includes section-number prefixes in headings).

---

### F2 — Governance policy is stronger than enforced CI gates (Medium)

`AGENT_GOVERNANCE.md` requires formatting/lint/tests and security/secret scanning gates, but current workflows only check file existence:

- `.github/workflows/ci.yml`: checks presence of `README.md` and `AGENT_GOVERNANCE.md`.
- `.github/workflows/agent-governance.yml`: checks presence of governance files.

**Impact:** repository claims “fail-closed” governance and security controls that are not yet technically enforced.

**Recommended fix:** add concrete CI jobs for markdown lint, YAML validation, link checking, and secret scanning (e.g., gitleaks/trufflehog) with required status checks.

---

### F3 — README section numbering has a gap (Low)

README jumps from section `12` to `14`, with no section `13`.

**Impact:** minor readability/professionalism issue; can also affect downstream tools that rely on predictable section sequencing.

**Recommended fix:** renumber “Agent Governance” and “Disclaimer” sections to maintain contiguous numbering.

---

### F4 — Positive baseline controls are present (Strength)

The repository includes meaningful governance artifacts and organizational scaffolding:

- ADRs for major technology choices,
- agent-specific instructions and playbooks,
- PR template with risk classification and governance checklist,
- incident template,
- structured backlog with dependencies and acceptance criteria.

**Impact:** gives a strong starting point for controlled implementation.

## Prioritized Remediation Plan

1. **P1:** Fix backlog anchor references in `docs/development_backlog.yaml`.
2. **P1:** Expand CI/workflow checks to enforce governance requirements described in `AGENT_GOVERNANCE.md`.
3. **P3:** Correct README numbering gap.

## Commands Run

- `rg --files`
- `sed -n '1,260p' ...` across repository docs and workflow files
- Python check for backlog `README.md#anchor` validity against README headings
- Python check for broken local Markdown links

## Audit Conclusion

The repository is governance-aware and well-structured for a planning-stage project, but should not yet be treated as governance-enforced. Closing the CI enforcement and traceability-link gaps will materially improve auditability and execution readiness.
