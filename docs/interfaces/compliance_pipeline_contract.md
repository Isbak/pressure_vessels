# Compliance Pipeline Contract (BL-004)

This document defines the deterministic contract for the **Compliance Dossier** vertical slice.

## Entry Point

- Python API: `pressure_vessels.compliance_pipeline.generate_compliance_dossier(requirement_set, design_basis, applicability_matrix, calculation_records, non_conformance_list, now_utc=None)`

- Persistence helper: `pressure_vessels.compliance_pipeline.write_compliance_artifacts(human_dossier, machine_dossier, directory)`


## BL-003 Handoff Gate (Required)

BL-004 proceeds only if all are true:

- `requirement_set.schema_version == "RequirementSet.v1"`
- `design_basis.schema_version == "DesignBasis.v1"`
- `applicability_matrix.schema_version == "ApplicabilityMatrix.v1"`
- `calculation_records.schema_version == "CalculationRecords.v1"`
- `non_conformance_list.schema_version == "NonConformanceList.v1"`
- `requirement_set.downstream_blocked == false`
- `requirement_set.unresolved_gaps` is empty
- `design_basis.source_requirement_set_hash == requirement_set.deterministic_hash`
- `applicability_matrix.source_requirement_set_hash == requirement_set.deterministic_hash`
- `calculation_records.source_requirement_set_hash == requirement_set.deterministic_hash`
- `calculation_records.source_design_basis_signature == design_basis.deterministic_signature`
- `calculation_records.source_applicability_matrix_hash == applicability_matrix.deterministic_hash`
- `non_conformance_list.source_calculation_records_hash == calculation_records.deterministic_hash`
- Every `CalculationRecords.checks[].clause_id` exists in `ApplicabilityMatrix.records[].clause_id`
- Every `NonConformanceList.entries[].check_id` references a **failed** `CalculationRecords.checks[].check_id`


If any condition fails, BL-004 raises a deterministic `ValueError` (fail closed).

## Output Artifacts

`generate_compliance_dossier` returns a tuple:

1. `ComplianceDossierHuman.v1`
2. `ComplianceDossierMachine.v1`


### Schema: `ComplianceDossierMachine.v1`

```json
{
  "schema_version": "ComplianceDossierMachine.v1",
  "generated_at_utc": "2026-04-18T00:00:00+00:00",
  "source_requirement_set_hash": "<RequirementSet.deterministic_hash>",
  "source_design_basis_signature": "<DesignBasis.deterministic_signature>",
  "source_applicability_matrix_hash": "<ApplicabilityMatrix.deterministic_hash>",
  "source_calculation_records_hash": "<CalculationRecords.deterministic_hash>",
  "source_non_conformance_hash": "<NonConformanceList.deterministic_hash>",
  "compliance_matrix_schema_version": "ComplianceMatrix.v1",
  "evidence_link_set_schema_version": "EvidenceLinkSet.v1",
  "review_checklist_schema_version": "ReviewChecklist.v1",
  "reproducibility": {
    "canonicalization": "json.sort_keys+compact",
    "hash_algorithm": "sha256"
  },
  "compliance_matrix": [
    {
      "clause_id": "UG-27",
      "applicable": true,
      "check_ids": ["UG-27-shell", "UG-27-shell-mawp"],
      "status": "pass",
      "justification": "Applicable because cylindrical shell thickness under internal pressure must be verified."
    }
  ],
  "evidence_links": [
    {
      "requirement_field": "design_pressure",
      "clause_id": "UG-27",
      "model_id": "t = (P*D)/(2*(S*E-0.6P)) + CA",
      "result_id": "UG-27-shell:pass=true",
      "artifact_ref": "CalculationRecords.v1#<hash>:UG-27-shell"
    }
  ],
  "review_checklist": [
    {
      "item_id": "CHK-001",
      "prompt": "Confirm requirement-to-clause evidence links cover all applicable clauses.",
      "required": true,
      "evidence_refs": ["evidence_links"]
    }
  ],
  "applied_defaults": {
    "applied_mvp_defaults": true,
    "values": {"allowable_stress_Pa": 138000000.0},
    "source": "BL-003 MVP placeholder; replace with Materials Module outputs."
  },
  "deterministic_hash": "<sha256 over canonical unsigned ComplianceDossierMachine payload>"
}
```

### Schema: `ComplianceDossierHuman.v1`

```json
{
  "schema_version": "ComplianceDossierHuman.v1",
  "generated_at_utc": "2026-04-18T00:00:00+00:00",
  "title": "BL-004 Compliance Dossier",
  "source_requirement_set_hash": "<RequirementSet.deterministic_hash>",
  "source_design_basis_signature": "<DesignBasis.deterministic_signature>",
  "source_applicability_matrix_hash": "<ApplicabilityMatrix.deterministic_hash>",
  "source_calculation_records_hash": "<CalculationRecords.deterministic_hash>",
  "source_non_conformance_hash": "<NonConformanceList.deterministic_hash>",
  "reproducibility": {
    "canonicalization": "json.sort_keys+compact",
    "hash_algorithm": "sha256"
  },
  "summary_lines": [
    "Primary standard: ASME Section VIII Division 1 (ASME_BPVC_2023)",
    "Clause outcomes: pass=4, fail=1, not_applicable=2, not_evaluated=2"
  ],
  "clause_matrix_rows": [
    {
      "clause_id": "UG-45",
      "status": "fail",
      "check_ids": "UG-45-nozzle, UG-45-nozzle-mawp",
      "justification": "Applicable because nozzle neck minimum thickness must be verified."
    }
  ],
  "evidence_trace_lines": [
    "design_pressure -> UG-45 -> t = (0.5*P*d)/(S*E-0.4P) + CA -> UG-45-nozzle:pass=false -> CalculationRecords.v1#<hash>:UG-45-nozzle"
  ],
  "review_checklist_lines": [
    "[CHK-001] Confirm requirement-to-clause evidence links cover all applicable clauses."
  ],
  "deterministic_hash": "<sha256 over canonical unsigned ComplianceDossierHuman payload>"
}
```

## Deterministic Controls

- `generated_at_utc` supports injection via `now_utc` for reproducible testing.
- `compliance_matrix` is generated in applicability-matrix order; `check_ids` are sorted by `check_id`.
- `evidence_links` are sorted by `(requirement_field, clause_id, model_id, result_id, artifact_ref)`.
- Each requirement-to-clause pair present in `ApplicabilityMatrix.evidence_fields` (where the requirement exists) must have at least one evidence link.
- Each applicable clause must have at least one evidence link.
- `review_checklist` is generated as deterministic fixed IDs (`CHK-001`..`CHK-003`).
- Both dossier hashes are sha256 over canonical unsigned payloads (`json.dumps(..., sort_keys=True, separators=(",",":"))`).


## Acceptance-Criteria Mapping

- **Clause-by-clause compliance matrix**: delivered as `compliance_matrix` and `clause_matrix_rows`.
- **Evidence links requirement -> clause -> model -> result -> artifact**: delivered as `evidence_links` and human `evidence_trace_lines`.
- **Human approver checklist**: delivered as `review_checklist` and `review_checklist_lines`.
