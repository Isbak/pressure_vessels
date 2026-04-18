# Calculation Pipeline Contract (BL-003)

This document defines the deterministic contract for the **Calculation Engine** vertical slice.

## Entry Point

- Python API: `pressure_vessels.calculation_pipeline.run_calculation_pipeline(requirement_set, design_basis, applicability_matrix, sizing_input=None, now_utc=None, near_limit_threshold=0.9)`

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

## Model-Domain / Validity-Envelope Gate (BL-003e)

BL-003 fails closed when caller inputs are outside deterministic engineering-model envelopes.

- Every check route declares a model-specific envelope (`min`/`max` bounds in canonical SI units).
- Before any records are emitted, BL-003 validates planned checks against their envelopes.
- If any bound is violated, BL-003 raises deterministic `ValueError`:
  - `"BL-003 model-domain gate failed: <check_id> input <name>=<value> is outside validity envelope [<min>, <max>]."`
- Envelope coverage is deterministic for conditional checks (UG-28 checks are validated only when `external_pressure` is declared).

## Materials + Corrosion Integration (BL-013)

When `sizing_input=None`, the pipeline now resolves allowable stress, joint efficiency, and corrosion policy from the deterministic materials module and only applies MVP placeholders for geometry. Material allowables are versioned and include standards-package trace fields. Corrosion allowance policy is explicit and persisted in both `material_basis` and `applied_defaults`.

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
  "material_basis": {
    "schema_version": "MaterialBasis.v1",
    "standards_package_ref": "ASME Section VIII Division 1:ASME_BPVC_2023",
    "allowables_version": "ASME_BPVC_2023.materials.2026-04",
    "material_spec": "SA-516 Gr.70",
    "allowable_stress_pa": 138000000.0,
    "joint_efficiency": 0.85,
    "corrosion_allowance_m": 0.003,
    "corrosion_allowance_policy": {
      "policy_id": "CA-INPUT-REQUIREMENT",
      "source": "requirement_set.corrosion_allowance",
      "value_mm": 3.0
    }
  },
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
      "near_limit_threshold": 0.9,
      "is_near_limit": true,
      "parent_component": null,
      "parent_check_id": null,
      "design_pressure_pa": null,
      "computed_mawp_pa": null,
      "pressure_margin_pa": null,
      "validity_envelope": {
        "model_id": "ug27_shell_thickness_v1",
        "status": "in_envelope",
        "bounds": {
          "internal_pressure_pa": {"min": 1.0, "max": 20000000.0},
          "allowable_stress_pa": {"min": 50000000.0, "max": 500000000.0},
          "joint_efficiency": {"min": 0.5, "max": 1.0},
          "shell_inside_diameter_m": {"min": 0.25, "max": 8.0},
          "corrosion_allowance_m": {"min": 0.0, "max": 0.02}
        },
        "evaluated_inputs": {
          "internal_pressure_pa": 1800000.0,
          "allowable_stress_pa": 138000000.0,
          "joint_efficiency": 0.85,
          "shell_inside_diameter_m": 2.0,
          "corrosion_allowance_m": 0.003
        }
      },
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
  - `near_limit_threshold` (default `0.9`, configurable per pipeline invocation)
  - `is_near_limit` (`true` only when `pass_status == true` and `utilization_ratio >= near_limit_threshold`)
  - `parent_component`, `parent_check_id` (set for routed checks such as nozzle reinforcement linked to shell/head parent checks)

  - `design_pressure_pa`, `computed_mawp_pa`, `pressure_margin_pa` (populated for pressure-capacity checks such as MAWP and UG-28 external-pressure)
  - `validity_envelope` metadata:
    - `model_id` (deterministic model route identifier)
    - `status` (`"in_envelope"` for emitted checks)
    - `bounds` (declared domain limits used for fail-closed gating)
    - `evaluated_inputs` (normalized values checked against bounds)

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

## External-Pressure Buckling Check (BL-003b / UG-28)

When `RequirementSet.requirements["external_pressure"]` is present (canonical unit `Pa`), BL-003b adds deterministic UG-28 external-pressure records:

- `UG-28-shell-external`
- `UG-28-head-external`

These checks are **conditional** and are omitted when external pressure is not declared.

Deterministic route:

- Compute `A = (t - CA) / D` with floor at zero for `t-CA`.
- Deterministically map to a pseudo-chart factor `B = clip(0.35 + 12*A, 0.2, 0.95)`.
- Compute elastic critical pressure surrogate `P_elastic = 2E*A^3/(1-ν^2)` with fixed constants `E=200 GPa`, `ν=0.3`.
- Compute allowable external pressure `P_allow = (B * P_elastic) / SF` with fixed safety factor `SF=3`.
- Pass criterion: `P_allow >= external_pressure`.

Each UG-28 record includes:

- `clause_id: "UG-28"` and per-check reproducibility hash metadata
- `design_pressure_pa = external_pressure`
- `computed_mawp_pa = P_allow` (field retained for schema compatibility)
- `pressure_margin_pa = computed_mawp_pa - design_pressure_pa`

Clause-coverage gate impact:

- If an external-pressure check is produced, `UG-28` **must** be marked applicable in `ApplicabilityMatrix`; otherwise BL-003 raises deterministic `ValueError`.

## Reinforcement-Area Replacement (BL-003c / UG-37 + UG-45 linkage)

BL-003c adds deterministic nozzle reinforcement-area replacement checks:

- `UG-37-nozzle-shell-reinforcement`
- `UG-37-nozzle-head-reinforcement`

Deterministic route (UG-37 area replacement with UG-45 nozzle-thickness linkage):

- Uses required nozzle thickness from `UG-45-nozzle` (`t_r_nozzle`) and required parent thickness from the linked parent route (`UG-27-shell` or `UG-32-head`) as `t_r_parent`.
- Computes required reinforcement area `A_req = d_opening * t_r_parent`.
- Computes available reinforcement area `A_avail = d_opening*max(t_parent-t_r_parent,0) + 2*w*max(t_nozzle-t_r_nozzle,0)`.

- Uses deterministic effective half-width `w = min(d_opening/2, sqrt(d_opening*D_parent))`.
- Pass criterion: `A_avail >= A_req`.

Each reinforcement record includes:

- `clause_id: "UG-37"`
- `component: "nozzle"`
- `parent_component: "shell" | "head"`
- `parent_check_id: "UG-27-shell" | "UG-32-head"`
- per-check reproducibility metadata (`sha256`)

Clause-coverage gate impact:

- If reinforcement checks are produced, `UG-37` **must** be marked applicable in `ApplicabilityMatrix`; otherwise BL-003 raises deterministic `ValueError`.

## Scope (MVP) and Deferred Items

BL-003 MVP now implements thickness + MAWP checks for shell (UG-27), head (UG-32), and nozzle (UG-45) under internal pressure, conditional UG-28 external-pressure checks for shell/head, UG-37 nozzle reinforcement-area replacement with parent-route linkage, and BL-003e model-domain/validity-envelope fail-closed gating.

## BL-004 Handoff Contract

BL-004 (compliance report) may proceed only when:

- `CalculationRecordsArtifact` and `NonConformanceListArtifact` are both produced from the same `run_calculation_pipeline` invocation (matching `generated_at_utc` and matching `source_calculation_records_hash`).

- Every `CalculationRecord.clause_id` is present in the referenced `ApplicabilityMatrix`.

- `applied_defaults.applied_mvp_defaults == false`, **or** the downstream dossier explicitly renders the `applied_defaults` block alongside the compliance matrix.
