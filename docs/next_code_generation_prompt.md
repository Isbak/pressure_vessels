# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **next queued roadmap item: BL-050 — Deploy LLM/Neo4j/Qdrant/OpenSearch/Temporal services on Railway**.

```text
You are the Codex implementation agent for `pressure_vessels`.
Task: Implement backlog item BL-050 — Deploy LLM/Neo4j/Qdrant/OpenSearch/Temporal services on Railway.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-22):
- `BL-047` status is `done`.
- `BL-049` status is `done`.
- `BL-050` status is `todo` and all dependencies are satisfied.
- `BL-050` is therefore the next queued implementation item.

Restate before coding:
- Item ID/title: BL-050 — Deploy LLM/Neo4j/Qdrant/OpenSearch/Temporal services on Railway
- depends_on:
  - BL-047
  - BL-049
- acceptance criteria:
  1) Railway environment provisions dedicated services for LLM serving, Neo4j, Qdrant, OpenSearch, and Temporal with documented networking and credential wiring to backend adapters.
  2) Backend runtime configuration uses Railway-provided endpoints/secrets for all five services and fails closed when any required integration variable is missing.
  3) Deployment runbook defines service-by-service smoke tests, rollback steps, and evidence capture for these integrations in staging.
- deliverables:
  1) Railway deployment manifests/checklists for the five platform services.
  2) Backend env-var matrix and secret wiring updates for Railway.
  3) Staging smoke-test and rollback evidence template.

Repository constraints:
- Keep changes minimal and focused on BL-050 scope.
- Follow contract-driven integration and avoid undocumented interface drift.
- Preserve governance-by-default controls from `AGENT_GOVERNANCE.md`.
- Prefer incremental delivery over broad rewrites; keep behavior deterministic.

Likely relevant files:
- `docs/development_backlog.yaml`
- `docs/cloud_getting_started.md`
- `docs/runbooks/platform_runtime_stack_operations.md`
- `docs/platform_runtime_stack_registry.yaml`
- `infra/platform/environment.bootstrap.yaml`

Task:
1) Implement BL-050 deliverables with minimal, reviewable patches.
2) Update Railway operations documentation for the five dependent services.
3) Update runtime configuration references so backend adapter wiring is explicit and fail-closed.
4) Add/update verification artifacts (smoke tests, rollback checklist, evidence template).
5) Refresh this file for the next queued backlog item after BL-050.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test/verification commands and expected results.
- Then provide backlog progression summary (what moved to done/todo/blocked and next item).
```
