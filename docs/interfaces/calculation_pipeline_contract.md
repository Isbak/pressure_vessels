# Calculation Pipeline Contract (BL-003)

This document defines the deterministic contract for the **Calculation Engine** vertical slice.

## Entry Point

- Python API: `pressure_vessels.calculation_pipeline.run_calculation_pipeline(requirement_set, design_basis, applicability_matrix, sizing_input=None, now_utc=None)`

- Persistence helper: `pressure_vessels.calculation_pipeline.write_calculation_artifacts(calc_artifact, non_conformance_artifact, directory)`

## BL-002 Handoff Gate (Required)

BL-003 proceeds only if all are true:

- `requirement_set.downstream_blocked == false`

- `requirement_set.unresolved_gaps` is empty

- `design_basis.primary_standard == "ASME Section VIII Division 1"`

- `applicability_matrix.source_requirement_set_hash == requirement_set.deterministic_hash`

- For every canonical field listed in `pressure_vessels.requirements_pipeline.CANONICAL_UNITS` that is present in `requirement_set.requirements`, the stored unit matches the canonical unit.

If any condition fails, BL-003 raises a deterministic `ValueError`.

## Clause-Coverage Gate

Each produced `CalculationRecord.clause_id` must be present and marked `applicable: true` in the provided `ApplicabilityMatrix`. If not, `run_calculation_pipeline` raises a deterministic `ValueError` ("BL-003 clause-coverage gate failed: ..."). This closes Workflow D Quality Gate #3 (Clause coverage) and Gate #4 (Traceability).

## Applied Defaults

When `sizing_input=None`, the pipeline injects MVP placeholder values (allowable stress, joint efficiency, geometry) so smoke-tests against the canonical prompt remain runnable. Every default value is recorded verbatim in `CalculationRecordsArtifact.applied_defaults` so that pass/fail outcomes are fully traceable. Callers that want fail-closed behavior should pass a `SizingCheckInput` built from the Materials and Geometry modules.

## Output Artifacts

`run_calculation_pipeline` returns a tuple:

1. `CalculationRecords.v1`

2. `NonConformanceList.v1`

### Schema: `CalculationRecords.v1`

```json
{
  "schema_version": "CalculationRecords.v1",
  "generated_at_utc": "2026-04-18T00:00:00+00:00",
  "source_requirement_set_hash": "<RequirementSet.deterministic_hash>",
  "source_design_basis_signature": "<DesignBasis.deterministic_signature>",
  "source_applicability_matrix_hash": "<ApplicabilityMatrix.deterministic_hash>",
  "applied_defaults": {
    "applied_mvp_defaults": false,
    "values": {},
    "source": "caller-provided"
  },
  "checks": [
    {
      "check_id": "UG-27-shell",
      "clause_id": "UG-27",
      "component": "shell",
      "formula": "t = (P*D)/(2*(S*E-0.6P)) + CA",
      "inputs": {"P_Pa": 1800000.0, "S_Pa": 138000000.0, "E": 0.85, "D_m": 2.0, "CA_m": 0.003},
      "required_thickness_m": 0.018487868,
      "provided_thickness_m": 0.02,
      "margin_m": 0.001512132,
      "utilization_ratio": 0.9243934,
      "design_pressure_pa": null,
      "computed_mawp_pa": null,
      "pressure_margin_pa": null,
      "pass_status": true,
      "reproducibility": {
        "canonical_payload_sha256": "<sha256 over canonical check payload>",
        "hash_algorithm": "sha256"
      }
    }
  ],
  "deterministic_hash": "<sha256 over canonical unsigned CalculationRecords payload>"
}
```

### Schema: `NonConformanceList.v1`

```json
{
  "schema_version": "NonConformanceList.v1",
  "generated_at_utc": "2026-04-18T00:00:00+00:00",
  "source_calculation_records_hash": "<CalculationRecords.deterministic_hash>",
  "entries": [
    {
      "check_id": "UG-45-nozzle",
      "clause_id": "UG-45",
      "component": "nozzle",
      "observed": "provided=0.004000 m",
      "required": "minimum=0.005702 m",
      "severity": "major"
    }
  ],
  "deterministic_hash": "<sha256 over canonical NonConformanceList payload>"
}
```

## Deterministic Controls

- `generated_at_utc` supports injection via `now_utc` for reproducible testing.

- Every check record carries:

  - `check_id` (engine-internal key), `clause_id` (link to `ApplicabilityMatrix`)

  - `formula` string (human-readable)

  - `inputs` snapshot in canonical SI units (`Pa`, `m`, dimensionless)

  - `required_thickness_m`, `provided_thickness_m`, `margin_m`, `utilization_ratio`

  - `design_pressure_pa`, `computed_mawp_pa`, `pressure_margin_pa` (populated for MAWP checks)

  - `pass_status`

  - `reproducibility.canonical_payload_sha256` (sha256 over the canonical JSON of the check record, sorted-keys, compact separators)

- `CalculationRecords.deterministic_hash` is sha256 over the canonical unsigned artifact (excluding the `deterministic_hash` field itself).

- `NonConformanceList.deterministic_hash` is sha256 over the canonical unsigned NC artifact (excluding its own `deterministic_hash`).

- All canonical hashing uses `json.dumps(..., sort_keys=True, separators=(",",":"))`.

## MAWP Check (BL-003a)

In addition to thickness checks, BL-003a adds MAWP checks for shell/head/nozzle under the same clause routes:

- `UG-27-shell-mawp`

- `UG-32-head-mawp`

- `UG-45-nozzle-mawp`

Each MAWP record is additive in `CalculationRecords.v1` and reuses existing fields for compatibility (`required_thickness_m` stores design pressure in Pa for MAWP records, `provided_thickness_m` stores provided thickness used in the MAWP equation). MAWP-specific typed fields are included on every record:

- `design_pressure_pa` (`number | null`)

- `computed_mawp_pa` (`number | null`)

- `pressure_margin_pa` (`number | null`, computed as `computed_mawp_pa - design_pressure_pa`)

For thickness checks these fields are `null`. For MAWP checks, `pass_status` is `computed_mawp_pa >= design_pressure_pa`.

## Scope (MVP) and Deferred Items

BL-003 MVP now implements thickness + MAWP checks for shell (UG-27), head (UG-32), and nozzle (UG-45) under internal pressure. The following Workflow D items remain deferred and tracked as follow-up backlog entries BL-003b..BL-003e:

- BL-003b External-pressure / buckling check (UG-28)

- BL-003c Reinforcement-area replacement (UG-37 / UG-45 full)

- BL-003d Margin / utilization near-limit reporting

- BL-003e Model-domain / validity-envelope gating

## BL-004 Handoff Contract

BL-004 (compliance report) may proceed only when:

- `CalculationRecordsArtifact` and `NonConformanceListArtifact` are both produced from the same `run_calculation_pipeline` invocation (matching `generated_at_utc` and matching `source_calculation_records_hash`).

- Every `CalculationRecord.clause_id` is present in the referenced `ApplicabilityMatrix`.

- `applied_defaults.applied_mvp_defaults == false`, **or** the downstream dossier explicitly renders the `applied_defaults` block alongside the compliance matrix.
