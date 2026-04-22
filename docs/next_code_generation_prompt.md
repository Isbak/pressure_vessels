# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **next queued roadmap item: BL-047 — Implement production backend integration adapters for platform services**.

```text
You are implementing backlog item **BL-047: Implement production backend integration adapters for platform services** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-21):
- `BL-042` status is `done`.
- `BL-043` status is `done`.
- `BL-047` status is `todo`.
- `BL-047` dependencies (`BL-043`, `BL-034`) are both `done`.
- Therefore `BL-047` is the next queued item.

Restate before coding:
- Item ID/title: BL-047 — Implement production backend integration adapters for platform services
- depends_on: [BL-043, BL-034]
- acceptance criteria:
  1) Backend design-run execution path persists and reads runtime state using approved adapters (PostgreSQL and Redis at minimum) instead of deterministic in-memory placeholder behavior.
  2) Backend integration points for Neo4j, Qdrant, OpenSearch, Temporal, and LLM serving are explicit interfaces with deterministic fallback/error semantics documented in the service contract.
  3) Integration tests validate that adapter wiring is environment-driven and fails closed when required service credentials/endpoints are missing.
- deliverables:
  1) Backend adapter interfaces and concrete runtime implementations.
  2) Updated backend API/runtime contract documentation.
  3) Integration test coverage for adapter wiring and failure modes.

Repository constraints:
- Keep changes minimal and focused; implement BL-047 only.
- Follow contract-driven integration and avoid undocumented interface drift.
- Preserve governance-by-default controls from `AGENT_GOVERNANCE.md`.
- Prefer incremental delivery over broad rewrites; keep behavior deterministic.

Likely relevant files:
- `services/backend/src/main.ts`
- `services/backend/src/adapters/`
- `docs/interfaces/backend_prompt_api_contract.md`
- `tests/`
- `infra/platform/environment.bootstrap.yaml`

Task:
1) Implement BL-047 adapter integration with deterministic failure semantics.
2) Keep interface contracts and runtime registry documentation aligned.
3) Add or update integration tests for adapter wiring and missing-configuration fail-closed behavior.
4) Keep backlog metadata unchanged except where implementation evidence requires it.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test/verification commands and expected results.
```
