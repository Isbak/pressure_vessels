# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to generate the **next implementation step** from the backlog:

```text
You are implementing the next roadmap item for the `pressure_vessels` repository.

Context:

- Roadmap source: `docs/development_backlog.yaml`
- Current completed items: BL-001, BL-002, BL-003, BL-003a, BL-003b, BL-003c, BL-003d, BL-003e, BL-004, BL-005, BL-006
- Next item to implement: BL-007
- BL-007 title: Certification dossier export
- BL-007 depends_on: BL-004, BL-006 (already done)
- BL-007 acceptance criteria:

  1) Export package includes PDF + machine-readable JSON.
  2) Signed calculation snapshots and change impact report are included.
  3) Package supports inspector/regulator review workflow.

- BL-007 deliverables:

  - Exportable dossier package
  - Template catalog for report sections

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

1) Implement BL-007 certification dossier export behavior using existing repository patterns.
2) Add deterministic export packaging for both machine-readable JSON and a PDF-oriented payload/template route.
3) Include signed calculation snapshot references and a change-impact placeholder/report section suitable for future BL-008 integration.
4) Add/extend tests under `tests/` for export structure, deterministic outputs, and required evidence links.
5) Update related architecture/interface docs under `docs/` to describe export package schema and usage.
6) Persist/update BL-007 sample artifacts under `artifacts/` if introduced.

Output format:

- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
