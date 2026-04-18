# Design Basis Pipeline Contract (BL-002 + BL-009)

This document defines the deterministic contract for the **Design Basis Engine** vertical slice.

## Entry Point

- Python API: `pressure_vessels.design_basis_pipeline.build_design_basis(requirement_set: RequirementSet, now_utc: datetime | None = None, route_configs: tuple[StandardRouteConfig, ...] | None = None)`

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

If any condition fails, the pipeline raises a deterministic `ValueError`.

## BL-009 Multi-Standard Route Selection

- Route selection is deterministic from normalized `code_standard` aliases.
- Default configured routes include:
  - `route_asme_viii_div1` (`ASME Section VIII Division 1`, `ASME_BPVC_2023`)
  - `route_ped_en13445` (`PED (EN 13445)`, `PED_2014_68_EU_EN13445_2021`)
- Additional standards can be introduced by passing deterministic `StandardRouteConfig` entries via `route_configs`.
- If multiple routes match, selection tie-break is deterministic: `route_priority` then `route_id`.
- Route audit is embedded in `DesignBasis.route_selection_audit` for traceability.

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
  "selected_route_id": "route_asme_viii_div1",
  "secondary_standards": ["PED (EN 13445):PED_2014_68_EU_EN13445_2021"],
  "route_selection_audit": [
    {
      "route_id": "route_asme_viii_div1",
      "standard_name": "ASME Section VIII Division 1",
      "standard_version": "ASME_BPVC_2023",
      "route_priority": 100,
      "matched_input": true,
      "selected": true,
      "selection_reason": "Selected: matched input and won deterministic priority/order tie-break."
    }
  ],
  "assumptions": [
    "Deterministic route selection uses priority then route_id tie-break with canonical code_standard aliases.",
    "Internal pressure basis is assumed unless external pressure input is provided."
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
  "selected_route_id": "route_asme_viii_div1",
  "records": [
    {
      "clause_id": "UG-28",
      "standard_route_id": "route_asme_viii_div1",
      "applicable": false,
      "justification": "Not applicable because external pressure service is not declared and internal pressure basis is assumed.",
      "evidence_fields": ["design_pressure"]
    }
  ],
  "deterministic_hash": "<sha256 over canonical matrix payload>"
}
```

## Deterministic Controls

- Standards and routes are selected using canonicalized input and deterministic route ordering.
- Clause sets are route-specific and deterministic for ASME and PED defaults.
- Every clause record includes `clause_id`, `standard_route_id`, `applicable`, `justification`, and `evidence_fields`.
- `generated_at_utc` supports injection via `now_utc` for reproducible testing.
- `DesignBasis` includes deterministic SHA-256 signature over canonicalized unsigned payload.
- `ApplicabilityMatrix` includes deterministic SHA-256 hash over canonicalized payload.
