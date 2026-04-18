# Codex Agent Instructions (Repository Scope)

## 1) Scope and Out-of-Scope Tasks

### In scope (allowlist)
- Implement scoped backlog items with minimal, reviewable patches following the standard workflow in `AGENT_GOVERNANCE.md` §5.
- Author or update tests and docs whenever behavior changes, per Definition of Done in §9.
- Perform routine refactors that do not alter intended behavior and stay inside approved task boundaries (§7 Shared guardrails).
- Prepare PR governance metadata and evidence required by §8 (audit logging) and §10 (starter checklist).

### Out of scope (denylist)
- Direct pushes to protected branches or any merge without required human approvals (§6 Branch/PR controls, §4 merge gates).
- Disabling, bypassing, or weakening tests/security checks to get CI green (§6 CI controls, §7 Shared guardrails).
- Unapproved high-risk edits in compliance calculations, security controls, CI/CD permissions, or schema/data migrations (§4 High risk).
- Policy exceptions without the documented exception workflow and explicit non-author human approval (Exception Request & Approval Workflow).
- Tasks requiring legal/regulatory interpretation beyond repository policy; escalate to human reviewers.

## 2) Canonical Prompt Templates

Use these templates verbatim as a starting point. Fill bracketed fields.

### A) Backlog implementation
```text
You are the Codex implementation agent for pressure_vessels.
Task: Implement backlog item [ID/TITLE].
Constraints:
- Follow AGENT_GOVERNANCE.md §5 workflow (plan → implement → cross-check → human review → merge).
- Classify risk per §4 and satisfy approvals/checks for that class.
- Meet Definition of Done in §9, including docs/tests updates.
- Respect guardrails in §7 and controls in §6.
Deliverables:
- Minimal patch, tests, PR checklist from §10, rollback notes for medium/high risk (§9).
```

### B) Bug fix
```text
You are the Codex implementation agent for pressure_vessels.
Task: Diagnose and fix bug [BUG-ID/SUMMARY].
Requirements:
- Reproduce and document failure before fix; include evidence for §8 audit logging.
- Apply least-risk fix and assign risk class using §4.
- Add/adjust regression tests and run required CI checks per §6.
- Update PR checklist items in §10 and DoD requirements in §9.
```

### C) Documentation update
```text
You are the Codex implementation agent for pressure_vessels.
Task: Update documentation for [TOPIC].
Requirements:
- Keep changes documentation-only unless explicitly approved otherwise.
- Ensure traceability per §8 (agent/task summary, files changed, evidence).
- Classify risk (usually low) per §4 and complete §10 checklist items.
- If governance/policy behavior changes, ensure §9 documentation expectations are met.
```

### D) Audit task
```text
You are the Codex implementation agent for pressure_vessels.
Task: Execute audit finding remediation [FINDING-ID].
Requirements:
- Map proposed edits to governance controls in §6, §7, §8, §9, and §10.
- Preserve separation of duties and approval gates in §3 and §4.
- Provide explicit rationale for risky edits per §7.
- Include evidence and decision trail artifacts needed by §8.
```

### E) Incident response
```text
You are the Codex implementation agent for pressure_vessels.
Task: Support incident response for [INCIDENT-ID].
Requirements:
- Prioritize containment-safe changes; classify risk via §4.
- Do not bypass controls in §6 or guardrails in §7.
- Document timeline, actions, tests, and rollback plan per §8 and §9.
- Route approvals to required human roles in §3 before merge.
```

## 3) Escalation Triggers and Human Reviewer to Page

Escalate immediately when any trigger matches:

- **Risk class trigger:** change is Medium or High risk per `AGENT_GOVERNANCE.md` §4.
  - **Page:** Engineering Reviewer (medium/high), plus Domain Reviewer for compliance-calculation impact, plus Security Reviewer for security/permission/supply-chain scope (§3, §4).
- **Touched file trigger:** edits to governance/policy files, CI/workflow permissions, dependency/lockfiles, schema migrations, or compliance calculation logic.
  - **Page:** Engineering Reviewer + Domain Reviewer and/or Security Reviewer depending on affected area (§3, §4, §6).
- **Test/scan trigger:** any failing format/lint/test/security/secret/dependency scan check.
  - **Page:** Engineering Reviewer first; add Security Reviewer for security/secret/dependency failures (§6).
- **Uncertainty trigger:** ambiguous requirements, potential policy exception, or inability to prove correctness.
  - **Page:** Repo Owner for scope/exception decision; relevant domain/security reviewer for risk adjudication (Exception workflow, §3).

## 4) Rollback Procedure (Merged Agent Change)

1. **Stabilize and classify**
   - Open incident/backlog record, assign risk class using §4, and notify Engineering Reviewer.
2. **Prepare revert branch**
   - `git fetch origin`
   - `git checkout -b revert/<pr-or-incident-id> origin/main`
   - `git revert <merge_commit_sha> --no-edit`
     (or revert a range/cherry-picked commits as needed)
3. **Validate revert**
   - Run required checks from §6 (format/lint/test/security scans).
   - Collect logs/artifacts for §8 audit requirements.
4. **Approval chain before merge**
   - Minimum: Engineering Reviewer approval.
   - Add Domain Reviewer for compliance impact and Security Reviewer for security/permissions/dependency impact (§3, §4).
   - Repo Owner confirms exception handling if standard gates are bypassed (Exception workflow).
5. **Required notices**
   - Post rollback notice in PR and linked incident/backlog item including impact window, reverted SHA(s), validation evidence, and follow-up actions.
   - Update governance checklist entries per §10 and DoD/rollback notes per §9.

## 5) Required Artifacts per Run

Every Codex-authored run must produce:

- **Commit message format**
  - `type(scope): summary [risk:<low|medium|high>] [agent:codex] [task:<id>]`
  - Body must include: rationale, files/areas affected, tests run, and rollback hint for medium/high risk (§4, §8, §9).
- **PR template completion**
  - Fill all governance checklist items from `AGENT_GOVERNANCE.md` §10.
  - Include risk class, agent identity, test evidence, approvals needed, and rollback plan (medium/high) (§4, §9).
- **Backlog updates**
  - Link the backlog/incident/audit item.
  - Record what was implemented, deferred, or escalated, and reference any policy exception entry if used (Exception workflow).
  - Ensure traceability fields needed for audit logging are present (§8).
