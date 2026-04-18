# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to generate the **next implementation step** from the backlog:

```text
You are implementing the next roadmap item for the `pressure_vessels` repository.

Context:

- Roadmap source: `docs/development_backlog.yaml`
- Current completed items: BL-001, BL-002, BL-003, BL-003a, BL-003b, BL-003c
- Next item to implement: BL-003d
- BL-003d title: Report margins and utilization ratios
- BL-003d depends_on: BL-003 (already done)
- BL-003d acceptance criteria:

  1) Each CalculationRecord exposes provided/required margin and utilization ratio.
  2) Near-limit threshold is configurable and persisted on the record.

- BL-003d deliverables:

  - Margin/utilization fields on CalculationRecord

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

1) Extend BL-003 calculations to include explicit near-limit reporting fields on each `CalculationRecord` (deterministic and backward-compatible).
2) Add a configurable near-limit threshold (defaulted deterministically) and persist the threshold/value(s) on records needed for downstream compliance rendering.
3) Ensure margin/utilization reporting remains clause-linked and reproducibility-safe (hash behavior remains deterministic and stable).
4) Enforce/extend handoff, model-domain, and clause-coverage gates as needed without weakening current controls.
5) Persist updated sample BL-003 artifacts under `artifacts/bl-003/`.
6) Add/extend tests in `tests/test_calculation_pipeline.py` for:

   - deterministic margin/utilization outputs
   - near-limit threshold configurability and persistence
   - clause linkage and reproducibility metadata compatibility
   - interactions with existing pass/fail and non-conformance behavior

7) Update `docs/interfaces/calculation_pipeline_contract.md` to document margin/utilization behavior and schema updates.

Output format:

- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
