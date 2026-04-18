# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to generate the **next implementation step** from the backlog:

```text
You are implementing the next roadmap item for the `pressure_vessels` repository.

Context:

- Roadmap source: `docs/development_backlog.yaml`
- Current completed items: BL-001, BL-002, BL-003, BL-003a, BL-003b, BL-003c, BL-003d, BL-003e, BL-004, BL-005, BL-006, BL-007, BL-008
- Next item to implement: BL-009
- BL-009 title: Support multi-standard design routes
- BL-009 depends_on: BL-005, BL-006 (already done)
- BL-009 acceptance criteria:

  1) System supports ASME + PED + additional standards as configured routes.
  2) Applicability and evidence mapping remain clause-level and traceable.
  3) Route selection logic is deterministic and auditable.

- BL-009 deliverables:

  - Multi-standard routing engine
  - Compatibility test matrix

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

1) Implement BL-009 multi-standard design routing behavior using existing repository patterns.
2) Add deterministic route selection for at least ASME and PED, and allow extension for additional standards.
3) Preserve clause-level applicability and evidence traceability across selected standard routes.
4) Add/extend tests under `tests/` for deterministic route selection, cross-standard traceability integrity, and compatibility matrix behavior.
5) Update related architecture/interface docs under `docs/` to describe BL-009 schema and usage, and persist sample artifacts under `artifacts/` if introduced.

Output format:

- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
