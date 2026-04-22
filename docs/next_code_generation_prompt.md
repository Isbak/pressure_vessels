# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **next queued roadmap item: BL-048 — Harden backend authentication and authorization for enterprise runtime**.

```text
You are implementing backlog item **BL-048: Harden backend authentication and authorization for enterprise runtime** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-22):
- `BL-047` status is `done`.
- `BL-043` status is `done`.
- `BL-048` status is `todo`.
- `BL-048` dependencies (`BL-043`, `BL-047`) are both `done`.
- Therefore `BL-048` is the next queued item.

Restate before coding:
- Item ID/title: BL-048 — Harden backend authentication and authorization for enterprise runtime
- depends_on: [BL-043, BL-047]
- acceptance criteria:
  1) Replace bootstrap token parsing with provider-backed verification (for example OIDC/JWT via Keycloak) while preserving deterministic role/scope enforcement for design-run APIs.
  2) Secret retrieval and rotation paths are documented for runtime operations, including break-glass and revocation procedures.
  3) Security regression tests cover expired token, invalid audience/issuer, insufficient scope, and key-rotation scenarios.
- deliverables:
  1) Production authn/authz integration in backend runtime.
  2) Security runbook updates for token and secret lifecycle operations.
  3) Automated security regression test suite for backend auth paths.

Repository constraints:
- Keep changes minimal and focused; implement BL-048 only.
- Follow contract-driven integration and avoid undocumented interface drift.
- Preserve governance-by-default controls from `AGENT_GOVERNANCE.md`.
- Prefer incremental delivery over broad rewrites; keep behavior deterministic.

Likely relevant files:
- `services/backend/src/main.ts`
- `services/backend/src/secrets.ts`
- `docs/interfaces/backend_prompt_api_contract.md`
- `docs/runbooks/runtime_security_hardening_checklist.md`
- `tests/`

Task:
1) Implement BL-048 provider-backed auth verification with deterministic fail-closed behavior.
2) Keep backend auth interfaces/contracts aligned with runtime documentation.
3) Add or update security regression tests for token validity, audience/issuer checks, scope enforcement, and key rotation handling.
4) As the final implementation step, update `docs/development_backlog.yaml` to reflect BL-048 status and implementation evidence.
5) As the final documentation step, generate the next `docs/next_code_generation_prompt.md` for the next eligible backlog item using the same template structure previously used for BL-032-style roadmap prompts (title line, authoritative source, backlog context, restate-before-coding, task list, output format).

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test/verification commands and expected results.
- Then provide the backlog/progression update summary (BL-048 status change + newly selected next queued backlog item).
```
