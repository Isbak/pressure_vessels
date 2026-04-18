# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to generate the **next implementation step** from the backlog:

```text
You are implementing the next roadmap item for the `pressure_vessels` repository.

Context:

- Roadmap source: `docs/development_backlog.yaml`
- Current completed items: BL-001, BL-002, BL-003, BL-003a, BL-003b, BL-003c, BL-003d, BL-003e, BL-004, BL-005, BL-006, BL-007, BL-008, BL-009
- Next item to implement: BL-010
- BL-010 title: Add optimization for cost and manufacturability
- BL-010 depends_on: BL-003, BL-009 (already done)
- BL-010 acceptance criteria:

  1) Optimization objective supports weight/cost/manufacturability trade-offs.
  2) All optimization outputs remain inside hard compliance constraints.
  3) Pareto candidate set is exported with justification metadata.

- BL-010 deliverables:

  - Optimization service
  - Candidate ranking report

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

1) Implement BL-010 optimization behavior using existing repository patterns.
2) Add deterministic multi-objective trade-off scoring (weight/cost/manufacturability) guarded by compliance constraints.
3) Export a deterministic Pareto candidate set with rationale metadata and stable ranking.
4) Add/extend tests under `tests/` for objective calculations, compliance guardrails, and candidate ranking determinism.
5) Update related architecture/interface docs under `docs/` to describe BL-010 schema and usage, and persist sample artifacts under `artifacts/` if introduced.

Output format:

- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
