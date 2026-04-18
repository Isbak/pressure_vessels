# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to generate the **next implementation step** from the backlog:

```text
You are implementing the next roadmap item for the `pressure_vessels` repository.

Context:

- Roadmap source: `docs/development_backlog.yaml`
- Current completed items: BL-001, BL-002, BL-003, BL-003a, BL-003b, BL-003c, BL-003d, BL-003e
- Next item to implement: BL-004
- BL-004 title: Generate basic compliance report
- BL-004 depends_on: BL-003 (already done)
- BL-004 acceptance criteria:

  1) Clause-by-clause compliance matrix is produced.
  2) Evidence links map requirement -> clause -> model -> result -> artifact.
  3) Review checklist is included for human approvers.

- BL-004 deliverables:

  - ComplianceDossier (human-readable)
  - ComplianceDossier (machine-readable)

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

1) Implement deterministic BL-004 dossier generation in `src/pressure_vessels/compliance_pipeline.py` to produce:
   - clause-by-clause compliance matrix
   - requirement -> clause -> model -> result -> artifact evidence links
   - human-review checklist entries
2) Ensure handoff gates validate consistency across RequirementSet, DesignBasis, ApplicabilityMatrix, CalculationRecords, and NonConformanceList artifacts (fail closed on mismatch).
3) Keep outputs deterministic and hash-stable (including canonical JSON serialization and reproducibility metadata fields).
4) Preserve compatibility with existing BL-003 artifacts and clause linkage assumptions.
5) Persist/update BL-004 sample artifacts under `artifacts/bl-004/` as needed.
6) Add/extend tests in `tests/test_compliance_pipeline.py` for:
   - deterministic dossier outputs
   - clause matrix and evidence-link completeness
   - checklist generation and required flags
   - handoff-gate failure behavior and hash-link validation
7) Update `docs/interfaces/compliance_pipeline_contract.md` to document BL-004 behavior and schema updates.

Output format:

- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
