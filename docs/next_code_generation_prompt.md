# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to generate the **next implementation step** from the backlog:

```text
You are implementing the next roadmap item for the `pressure_vessels` repository.

Context:

- Roadmap source: `docs/development_backlog.yaml`
- Current completed items: BL-001, BL-002, BL-003
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
- `tests/test_requirements_pipeline.py`
- `tests/test_design_basis_pipeline.py`
- `tests/test_calculation_pipeline.py`
- `docs/interfaces/requirements_pipeline_contract.md`
- `docs/interfaces/design_basis_pipeline_contract.md`
- `docs/interfaces/calculation_pipeline_contract.md`
- `artifacts/bl-001/`
- `artifacts/bl-002/`
- `artifacts/bl-003/`

Task:

1) Implement a new compliance-report module for BL-004 (e.g., `src/pressure_vessels/compliance_pipeline.py`).
2) Define typed input/output structures and artifact schemas for:

   - clause-by-clause compliance matrix
   - evidence links (requirement -> clause -> model -> result -> artifact)
   - human approver review checklist
   - human-readable and machine-readable dossier payloads

3) Re-use `RequirementSet.v1`, `DesignBasis.v1`, `ApplicabilityMatrix.v1`, `CalculationRecords.v1`, and `NonConformanceList.v1` as inputs. Enforce handoff gates consistent with the BL-001/BL-002/BL-003 patterns.
4) Persist sample BL-004 artifacts under `artifacts/bl-004/`.
5) Add tests (e.g., `tests/test_compliance_pipeline.py`) that validate:

   - deterministic outputs
   - correct evidence wiring
   - review checklist generation
   - schema shape of both dossier forms

6) Add `docs/interfaces/compliance_pipeline_contract.md` following the BL-001/BL-002/BL-003 pattern.

Output format:

- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
