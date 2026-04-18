# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to generate the **next implementation step** from the backlog:

```text
You are implementing the next roadmap item for the `pressure_vessels` repository.

Context:

- Roadmap source: `docs/development_backlog.yaml`
- Current completed items: BL-001, BL-002, BL-003, BL-003a, BL-003b, BL-003c, BL-003d, BL-003e, BL-004, BL-005
- Next item to implement: BL-006
- BL-006 title: Implement full traceability graph
- BL-006 depends_on: BL-003 and BL-004 (already done)
- BL-006 acceptance criteria:

  1) Traceability graph stores requirement, clause, model, calculation, artifact, and approval links.
  2) Graph supports audit queries by revision and clause.
  3) All graph writes are revisioned and immutable by default.

- BL-006 deliverables:

  - Traceability graph schema
  - Query examples and audit report templates

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

1) Implement BL-006 full traceability graph behavior using existing repository patterns.
2) Introduce deterministic graph entities and immutable revisioned writes for traceability links.
3) Add read/query functions that support clause-level and revision-level audit retrieval.
4) Add/extend tests under `tests/` for graph writes, immutability/revision behavior, and audit query behavior.
5) Update related interface/contract docs under `docs/interfaces/` and operational notes/runbook docs as needed.
6) Persist/update BL-006 sample artifacts under `artifacts/bl-006/` if introduced.

Output format:

- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
