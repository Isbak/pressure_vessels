# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to generate the **next implementation step** from the backlog:

```text
You are implementing the next roadmap item for the `pressure_vessels` repository.

Context:

- Roadmap source: `docs/development_backlog.yaml`
- Current completed items: BL-001, BL-002, BL-003, BL-003a, BL-003b, BL-003c, BL-003d
- Next item to implement: BL-003e
- BL-003e title: Enforce model-domain / validity-envelope gate
- BL-003e depends_on: BL-003 (already done)
- BL-003e acceptance criteria:

  1) Each engineering model declares a validity envelope.
  2) Pipeline fails closed when inputs fall outside the declared envelope.

- BL-003e deliverables:

  - Validity envelope metadata on CalculationRecord

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

1) Add explicit validity-envelope metadata to BL-003 calculation records so each check declares the model-domain bounds it assumes.
2) Enforce deterministic fail-closed model-domain gating when caller inputs violate validity-envelope limits.
3) Keep clause linkage and reproducibility hashing deterministic after schema updates.
4) Extend handoff/model-domain/clause-coverage gates only as needed, without weakening existing controls.
5) Persist updated sample BL-003 artifacts under `artifacts/bl-003/`.
6) Add/extend tests in `tests/test_calculation_pipeline.py` for:

   - deterministic validity-envelope metadata outputs
   - fail-closed behavior for out-of-envelope inputs
   - clause linkage and reproducibility metadata compatibility
   - interactions with existing pass/fail and non-conformance behavior

7) Update `docs/interfaces/calculation_pipeline_contract.md` to document validity-envelope behavior and schema updates.

Output format:

- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
