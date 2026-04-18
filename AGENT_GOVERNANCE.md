# Agent Governance Starter (Codex + Claude Code)

This document defines a practical starting point for governing two coding agents in this repository:

- **Codex-based agent** (planning, implementation, refactoring, test authoring)
- **Claude Code-based agent** (analysis, review, hardening, and secondary implementation)

It is intentionally lightweight so teams can adopt it immediately and evolve it with real project experience.

---

## 1) Governance Objectives

1. **Safety first**: prevent destructive or non-compliant changes.
2. **Traceability**: every code change must have an attributable agent + human reviewer trail.
3. **Quality**: preserve engineering correctness with repeatable checks.
4. **Separation of duties**: no single agent can independently merge risky changes.
5. **Continuous improvement**: measure outcomes and tighten controls over time.

---

## 2) Scope & Applicability

This policy applies to:

- Code, docs, tests, and workflow files in this repository.
- All pull requests where either Codex or Claude Code contributes changes.
- Local, CI, and cloud execution contexts.

Out of scope (for now):

- Third-party infrastructure governance outside this repository.
- Organization-wide IAM policies (should be referenced from corporate standards).

---

## 3) Roles and Responsibilities

### Human Roles

- **Repo Owner**: accountable for governance settings and branch protections.
- **Engineering Reviewer**: validates technical correctness and maintainability.
- **Domain Reviewer (Pressure Vessel SME)**: validates safety/code-compliance intent.
- **Security Reviewer**: required for permission model, secrets, or supply-chain changes.

### Agent Roles

- **Codex Agent**:
  - Primary implementation agent for scoped tasks.
  - Generates tests and updates docs with each behavior change.
- **Claude Code Agent**:
  - Secondary implementation/review agent.
  - Performs independent risk review on substantial changes.

> Either agent may author code. Neither agent may self-approve for merge.

---

## 4) Change Classification and Merge Gates

Classify every PR as one of:

- **Low risk**: docs, comments, non-executable metadata.
- **Medium risk**: business logic, validation rules, normal dependency updates.
- **High risk**: calculation logic tied to compliance, security controls, CI/CD permissions, data/schema migrations.

### Minimum approvals

- **Low risk**: 1 human reviewer.
- **Medium risk**: 1 engineering reviewer + passing CI.
- **High risk**: 2 humans (engineering + domain/security as applicable) + passing CI + explicit checklist completion.

---

## 5) Standard Workflow (Dual-Agent Friendly)

1. **Plan**
   - Create a short task plan with assumptions and affected files.
2. **Implement**
   - One agent produces the patch.
3. **Cross-check**
   - The other agent performs an independent review and flags:
     - correctness issues,
     - safety/compliance risks,
     - missing tests.
4. **Human review**
   - Required reviewer(s) approve according to risk class.
5. **Merge**
   - Only after all required checks and approvals pass.

---

## 6) Required Controls (Baseline)

### Branch and PR controls

- Protect `main` from direct pushes.
- Require pull requests for all changes.
- Require status checks before merge.
- Require at least one non-author human approval.

### CI controls

- Run formatting, linting, and tests on every PR.
- Fail closed on broken checks.
- Store build/test artifacts for auditability.

### Secret and dependency controls

- Enable secret scanning in CI.
- Block commits that introduce plaintext secrets.
- Require lockfile updates and vulnerability scan on dependency changes.

---

## 7) Agent Guardrails

### Shared

- Agents must work only within task scope.
- Agents must not exfiltrate repository data.
- Agents must provide explicit rationale for risky edits.
- Agents must avoid disabling tests/security checks to pass CI.

### Codex-specific

- Prefer small, incremental commits with tests.
- Include file-level rationale in PR description.

### Claude Code-specific

- Perform adversarial review for edge cases on medium/high risk PRs.
- Explicitly call out uncertainty and required human validation.

---

## 8) Audit Logging Requirements

For each agent-authored PR, record:

- Agent name and model/runtime identifier.
- Prompt/task summary (no secrets).
- Files changed and test evidence.
- Review outcomes and approval identity.
- Final merge decision and timestamp.

Store logs in PR metadata and CI artifacts for a minimum retention period defined by your organization.

---

## 9) Definition of Done (Agent-Contributed PR)

A PR is done only when all are true:

- Risk class assigned.
- Required tests pass.
- Required human approvals completed.
- Documentation updated when behavior/policy changes.
- For technology selection changes: `docs/tech-stack.md` updated + ADR added in `docs/decision-log/`.
- Rollback approach noted for medium/high risk changes.

---

## 10) Starter Governance Checklist

Use this checklist in every PR description:

- [ ] Risk class selected (low/medium/high)
- [ ] Agent author identified (Codex / Claude Code / both)
- [ ] Independent cross-agent review completed (for medium/high)
- [ ] Required tests executed and attached
- [ ] Security/secret scan passed
- [ ] Required human approvals obtained
- [ ] Rollback plan included (for medium/high)

---

## 11) 30/60/90-Day Rollout

### First 30 days

- Enable branch protections + required CI checks.
- Adopt the checklist and risk classification.
- Start collecting basic metrics (PR cycle time, escaped defects).

### By 60 days

- Add dependency + secret scanning gates.
- Require cross-agent review for medium/high risk changes.
- Introduce incident review template for agent-related regressions.

### By 90 days

- Add policy-as-code checks for PR metadata completeness.
- Establish quarterly governance review with engineering + domain stakeholders.
- Tune controls based on observed failure patterns.

---

### Exception Request & Approval Workflow

- **Request**: author opens/updates a backlog item and proposes an exception entry in `.github/governance/policy_exceptions.v1.json` including scope, justification, approver, and expiration.
- **Approval**: one non-author human reviewer listed as `approver` approves the linked backlog item/PR before merge; exceptions without explicit approval are rejected.
- **Validation**: CI validates exception payloads against `docs/governance/policy_exceptions_schema.v1.json` and applies only unexpired scope-matching exceptions.
- **Timeline alignment**:
  - **First 30 days**: adopt schema and empty baseline exception registry (`version=1`, no active exceptions).
  - **By 60 days**: require linked backlog IDs for every exception and weekly review of nearing expirations.
  - **By 90 days**: track exception aging metrics and enforce auto-cleanup for expired entries in governance reviews.

## 12) Metrics to Track

- PR lead time by risk class.
- Reopen/revert rate.
- Post-merge defect rate.
- Security finding count/severity.
- % PRs with complete governance checklist.

Use trends to improve prompts, review depth, and gate strictness.

---

## 13) Is This "Best Practice" Yet?

Short answer: **this is a strong starter baseline, not the final best-practice end state**.

Use this repository as **Level 1 (Foundational)** governance. Move toward best practice by adding:

- **Level 2 (Controlled):** enforced CI gates (lint/test/security), mandatory CODEOWNERS routing, signed commits, and environment protections.
- **Level 3 (Assured):** policy-as-code for PR metadata/risk labels, SBOM + dependency provenance, reproducible builds, and incident drill cadence.
- **Level 4 (Optimized):** measured risk-based autonomy (agent permissions vary by task risk), automated rollback validation, and quarterly control tuning from defect/security trends.

### Practical benchmark for "best practice"

You are close to best practice when all of the following are true:

1. Every agent PR is risk-labeled and blocked from merge without required human approvals.
2. Security checks (secrets, SAST, dependency scanning) are enforced and cannot be bypassed.
3. Build/test results are reproducible and retained for audit.
4. Agent identity, prompts (sanitized), and decision trail are logged for each change.
5. Regular governance reviews produce policy improvements with evidence.

---

## 13) Repository Conventions for This Governance

- Keep this file as the single source of governance baseline.
- Reference this file from `README.md`.
- Keep agent-specific instructions in `.agents/codex/AGENTS.md` and `.agents/claude/CLAUDE.md`.
- Keep PR governance checks in `.github/pull_request_template.md`.
- Revisit quarterly or after any major incident.
