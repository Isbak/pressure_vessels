# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to generate the **next implementation step** from the backlog:

```text
You are implementing the next roadmap item for the `pressure_vessels` repository.

Context:

- Roadmap source: `docs/development_backlog.yaml`
- Current completed items: BL-001, BL-002, BL-003, BL-003a
- Next item to implement: BL-003b
- BL-003b title: Implement external-pressure / buckling check
- BL-003b depends_on: BL-003 (already done)
- BL-003b acceptance criteria:

  1) External-pressure check runs when external pressure is declared in RequirementSet.
  2) Uses UG-28 chart/equation route deterministically.

- BL-003b deliverables:

  - External-pressure entries in `CalculationRecords.v1`

Repository constraints:

- Keep changes minimal and focused.
- Follow existing style and module patterns in `src/pressure_vessels/`.
- Add/extend tests in `tests/` for any new behavior.
- Prefer deterministic logic (no randomness/time-dependent values unless explicitly controlled).

Existing relevant files:

- `src/pressure_vessels/requirements_pipeline.py`
- `src/pressure_vessels/design_basis_pipeline.py`
- `src/pressure_vessels/calculation_pipeline.py`
- `src/pressure_vessels/compliance_pipeline.py`
- `tests/test_requirements_pipeline.py`
- `tests/test_design_basis_pipeline.py`
- `tests/test_calculation_pipeline.py`
- `tests/test_compliance_pipeline.py`
- `docs/interfaces/requirements_pipeline_contract.md`
- `docs/interfaces/design_basis_pipeline_contract.md`
- `docs/interfaces/calculation_pipeline_contract.md`
- `docs/interfaces/compliance_pipeline_contract.md`
- `artifacts/bl-001/`
- `artifacts/bl-002/`
- `artifacts/bl-003/`
- `artifacts/bl-004/`

Task:

1) Extend BL-003 calculations to include deterministic external-pressure / buckling checks per relevant component routes.
2) Add deterministic external-pressure / buckling checks per UG-28 only when external pressure inputs are present.
3) Ensure each external-pressure result is linked to `clause_id`, includes reproducibility hash metadata, and is integrated into `CalculationRecords.v1` deterministically.
4) Enforce/extend handoff, model-domain, and clause-coverage gates as needed without weakening current controls.
5) Persist updated sample BL-003 artifacts under `artifacts/bl-003/`.
6) Add/extend tests in `tests/test_calculation_pipeline.py` for:

   - deterministic external-pressure outputs
   - clause linkage and reproducibility metadata
   - conditional execution behavior (runs only when external pressure is declared)
   - interactions with existing pass/fail and non-conformance behavior

7) Update `docs/interfaces/calculation_pipeline_contract.md` to document external-pressure behavior and schema updates.

Output format:

- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
