# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to generate the **next implementation step** from the backlog:

```text
You are implementing the next roadmap item for the `pressure_vessels` repository.

Context:

- Roadmap source: `docs/development_backlog.yaml`
- Current completed items: BL-001, BL-002
- Next item to implement: BL-003
- BL-003 title: Implement core ASME Div 1 sizing checks
- BL-003 depends_on: BL-001, BL-002 (already done)
- BL-003 acceptance criteria:

  1) Deterministic sizing checks run for shell/head/nozzle and related checks.
  2) All calculations are unit-safe with reproducibility hashes.
  3) Pass/fail records and non-conformance list are stored.

- BL-003 deliverables:

  - CalculationRecords
  - Non-conformance list

Repository constraints:

- Keep changes minimal and focused.
- Follow existing style and module patterns in `src/pressure_vessels/`.
- Add/extend tests in `tests/` for any new behavior.
- Prefer deterministic logic (no randomness/time-dependent values unless explicitly controlled).

Existing relevant files:

- `src/pressure_vessels/requirements_pipeline.py`
- `src/pressure_vessels/design_basis_pipeline.py`
- `tests/test_requirements_pipeline.py`
- `tests/test_design_basis_pipeline.py`
- `artifacts/bl-001/`
- `artifacts/bl-002/`

Task:

1) Implement a new calculation pipeline module for BL-003 (e.g., `src/pressure_vessels/calculation_pipeline.py`).
2) Define typed input/output structures and artifact schema for:

   - calculation records
   - pass/fail status
   - non-conformance entries
   - reproducibility hash metadata

3) Add deterministic placeholder ASME Div 1 checks for shell, head, and nozzle sizing, with clear extension points for full formulas.
4) Ensure unit normalization/safety in all calculations.
5) Persist sample BL-003 artifacts under `artifacts/bl-003/`.
6) Add tests (e.g., `tests/test_calculation_pipeline.py`) that validate:

   - deterministic outputs
   - correct pass/fail behavior
   - non-conformance generation
   - reproducibility hash stability

Output format:

- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
