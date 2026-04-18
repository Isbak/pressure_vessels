# Design Basis Pipeline Contract (BL-002)

This document defines the deterministic contract for the **Design Basis Engine** vertical slice.

## Entry Point

- Python API: `pressure_vessels.design_basis_pipeline.build_design_basis(requirement_set: RequirementSet, now_utc: datetime | None = None)`

## BL-001 Handoff Gate (Required)

BL-002 proceeds only if all are true:

- `requirement_set.downstream_blocked == false`
- `requirement_set.unresolved_gaps` is empty
- Required normalized fields are present in `requirement_set.requirements`:
  - `fluid`
  - `design_pressure`
  - `design_temperature`
  - `capacity`
  - `code_standard`

If any condition fails, BL-002 raises a deterministic `ValueError`.

## Output Artifacts

`build_design_basis` returns a tuple:

1. `DesignBasis.v1`
2. `ApplicabilityMatrix.v1`

### Schema: `DesignBasis.v1`

```json
{
  "schema_version": "DesignBasis.v1",
  "generated_at_utc": "2026-04-18T00:00:00+00:00",
  "source_requirement_set_hash": "<RequirementSet.deterministic_hash>",
  "primary_standard": "ASME Section VIII Division 1",
  "primary_standard_version": "ASME_BPVC_2023",
  "secondary_standards": [],
  "assumptions": [
    "MVP assumes internal pressure service unless external pressure input is provided."
  ],
  "deterministic_signature": "<sha256 over canonical unsigned DesignBasis payload>"
}
```

### Schema: `ApplicabilityMatrix.v1`

```json
{
  "schema_version": "ApplicabilityMatrix.v1",
  "generated_at_utc": "2026-04-18T00:00:00+00:00",
  "source_requirement_set_hash": "<RequirementSet.deterministic_hash>",
  "primary_standard": "ASME Section VIII Division 1",
  "primary_standard_version": "ASME_BPVC_2023",
  "records": [
    {
      "clause_id": "UG-28",
      "applicable": false,
      "justification": "Not applicable in MVP because external pressure service is not declared and internal pressure basis is assumed.",
      "evidence_fields": ["design_pressure"]
    }
  ],
  "deterministic_hash": "<sha256 over canonical matrix payload>"
}
```

## Deterministic Controls

- Standards selection uses deterministic lookup from normalized `code_standard`.
- Clause set is deterministic MVP subset for ASME Section VIII Div 1.
- Every clause record contains:
  - `clause_id`
  - `applicable`
  - `justification` (required for both applicable/non-applicable)
  - `evidence_fields` used in the decision
- `generated_at_utc` supports injection via `now_utc` for reproducible testing.
- `DesignBasis` includes deterministic SHA-256 signature over canonicalized unsigned payload.
- `ApplicabilityMatrix` includes deterministic SHA-256 hash over canonicalized payload.
