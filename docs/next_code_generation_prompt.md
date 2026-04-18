# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to generate the **next implementation step** from the backlog:

```text
You are implementing the next roadmap item for the `pressure_vessels` repository.

Context:

- Roadmap source: `docs/development_backlog.yaml`
- Current completed items: BL-001, BL-002, BL-003, BL-003a, BL-003b, BL-003c, BL-003d, BL-003e, BL-004, BL-005, BL-006, BL-007, BL-008, BL-009, BL-010
- Next item to implement: BL-011
- BL-011 title: Integrate enterprise systems (PLM/ERP/QMS)
- BL-011 depends_on: BL-007 (already done)
- BL-011 acceptance criteria:

  1) Artifacts and approvals sync with configured enterprise systems.
  2) Traceability links are preserved across system boundaries.
  3) Integration retries and failure handling are observable.

- BL-011 deliverables:

  - Integration adapters
  - Operational runbooks

Repository constraints:

- Keep changes minimal and focused.
- Follow existing style and module patterns in `src/pressure_vessels/`.
- Add/extend tests in `tests/` for any new behavior.
- Prefer deterministic logic (no randomness/time-dependent values unless explicitly controlled).

Existing relevant files:

- `scripts/`
- `docs/`
- `src/pressure_vessels/`
- `tests/`
- `README.md`

Task:

1) Implement BL-011 enterprise integration behavior using existing repository patterns.
2) Add deterministic adapters for syncing certification artifacts and approvals to configurable PLM/ERP/QMS targets.
3) Preserve and validate traceability links across integration boundaries with auditable mappings.
4) Add/extend tests under `tests/` for sync flows, retry/failure observability, and traceability preservation.
5) Update related architecture/interface docs under `docs/` to describe BL-011 schemas, integration configuration, and operational runbook expectations.

Output format:

- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
