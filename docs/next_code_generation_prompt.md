# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to generate the **next implementation step** from the backlog:

```text
You are implementing the next roadmap item for the `pressure_vessels` repository.

Context:

- Roadmap source: `docs/development_backlog.yaml`
- Current completed items: BL-001, BL-002, BL-003, BL-003a, BL-003b, BL-003c, BL-003d, BL-003e, BL-004
- Next item to implement: BL-005
- BL-005 title: Standards ingestion pipeline
- BL-005 depends_on: BL-002 (already done)
- BL-005 acceptance criteria:

  1) Ingestion supports source intake, parsing, normalization, semantic linking, validation, and release.
  2) Standards packages are immutable and versioned.
  3) Regression examples pass before release.

- BL-005 deliverables:

  - Versioned standards package
  - Ingestion pipeline runbook

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

1) Implement BL-005 standards ingestion pipeline behavior using existing repository patterns.
2) Add deterministic, versioned package outputs for ingested standards.
3) Ensure fail-closed validation for malformed or incomplete source inputs.
4) Add/extend tests under `tests/` for ingestion flow, package versioning, and regression checks.
5) Update related interface/contract docs under `docs/interfaces/` and operational notes/runbook docs as needed.
6) Persist/update BL-005 sample artifacts under `artifacts/bl-005/` if introduced.

Output format:

- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
