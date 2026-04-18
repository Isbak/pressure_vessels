# Standards Ingestion Pipeline Contract (BL-005)

This document defines the deterministic contract for the standards ingestion pipeline.

## Entry Points

- Python API: `pressure_vessels.standards_ingestion_pipeline.run_standards_ingestion(...)`
- Persistence helper: `pressure_vessels.standards_ingestion_pipeline.write_standards_package(package, directory)`

## Pipeline Stages

BL-005 ingestion runs these fail-closed stages in order:

1. Source intake validation
2. Clause parsing
3. Clause normalization
4. Semantic linking
5. Consistency validation
6. Regression gating
7. Immutable release packaging

## Source Intake Requirements

Each `StandardSource` must provide non-empty:

- `source_id`
- `title`
- `publisher`
- `edition`
- `revision`
- `content_text`

If any field is missing or empty, ingestion raises `ValueError`.

## Release Gate Requirements

Release is blocked unless all conditions are true:

- At least one source document exists.
- Every non-empty source line must match clause syntax: `CLAUSE-ID: clause body`.
- At least one clause is parsed from source text.
- Clause IDs must be unique across all source inputs.
- Parsed and normalized clause IDs match exactly.
- Every semantic link references known clause IDs.
- At least one regression example is provided.
- Every regression example passes (required clauses and required link pairs are present).

If any condition fails, ingestion raises `ValueError` and no package is released.

## Output Artifact: `StandardsPackage.v1`

```json
{
  "schema_version": "StandardsPackage.v1",
  "generated_at_utc": "2026-04-18T00:00:00+00:00",
  "package_id": "ASME_VIII_1_2025.2_r1",
  "standard_key": "ASME_VIII_1",
  "standard_version": "2025.2",
  "release_label": "r1",
  "immutable": true,
  "source_fingerprints": [
    {
      "source_id": "ASME_BPVC_VIII_DIV1_2025_MAIN",
      "content_sha256": "<sha256>"
    }
  ],
  "parsed_clauses": [
    {
      "clause_id": "UG-27",
      "text": "Cylindrical shell thickness for internal pressure; equation = t = (P*R)/(S*E-0.6*P); See UG-16.",
      "equation": "t = (P*R)/(S*E-0.6*P)",
      "cross_references": ["UG-16"]
    }
  ],
  "normalized_clauses": [
    {
      "clause_id": "UG-27",
      "canonical_text": "cylindrical shell thickness for internal pressure; equation = t = (p*r)/(s*e-0.6*p); see ug-16.",
      "canonical_equation": "t=(P*R)/(S*E-0.6*P)",
      "canonical_variables": ["E", "P", "R", "S", "t"]
    }
  ],
  "semantic_links": [
    {
      "from_clause_id": "UG-27",
      "to_clause_id": "UG-16",
      "link_type": "cross_reference",
      "reason": "Cross-reference found in clause text."
    }
  ],
  "regression_results": [
    {
      "example_id": "REG-001",
      "passed": true,
      "details": "pass"
    }
  ],
  "deterministic_hash": "<sha256 over canonical unsigned package payload>"
}
```

## Immutability and Versioning

- Package ID is deterministic: `{standard_key}_{standard_version}_{release_label}`.
- `write_standards_package` persists file name `{package_id}.json`.
- Persistence uses exclusive create mode (`x`), so writing the same package ID twice raises `FileExistsError`.
