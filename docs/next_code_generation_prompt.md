# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **current next roadmap item: BL-014**.

```text
You are implementing backlog item **BL-014: Add geometry/CAD interface and strict sizing-input gate** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-18):
- `BL-014` status is `todo`.
- `BL-014` dependencies are `BL-003` and `BL-013`, and both are `done`.
- Therefore `BL-014` is the next eligible item.

Restate before coding:
- Item ID/title: BL-014 — Add geometry/CAD interface and strict sizing-input gate
- depends_on: [BL-003, BL-013]
- acceptance criteria:
  1) Geometry/CAD module provides deterministic sizing inputs for shell/head/nozzle routes.
  2) Calculation pipeline can run fail-closed when required geometry/material inputs are missing.
  3) Exported geometry parameters are traceable by revision and linked to calculation evidence.
- deliverables:
  1) Geometry input schema and adapters
  2) Calculation handoff-gate update for strict sizing-input mode
  3) CAD-ready parameter export artifact

Repository constraints:
- Keep changes minimal and focused.
- Follow existing style and module patterns in `src/pressure_vessels/`.
- Add/extend tests in `tests/` for any new behavior.
- Prefer deterministic logic (no randomness/time-dependent values unless explicitly controlled).

Likely relevant files:
- `src/pressure_vessels/calculation_pipeline.py`
- `src/pressure_vessels/compliance_pipeline.py`
- `docs/interfaces/calculation_pipeline_contract.md`
- `docs/interfaces/compliance_pipeline_contract.md`
- `tests/test_calculation_pipeline.py`
- `tests/test_compliance_pipeline.py`

Task:
1) Implement BL-013 behavior using existing repository patterns.
2) Satisfy each BL-014 acceptance criterion explicitly.
3) Deliver each BL-014 deliverable with minimal, auditable changes.
4) Add/extend tests under `tests/` for new behavior.
5) Update related architecture/interface docs under `docs/`.
6) Update `docs/development_backlog.yaml` status for BL-013 when complete.
7) Update `docs/next_code_generation_prompt.md` so it points at the subsequent backlog item.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
