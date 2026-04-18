# Requirements Pipeline Contract (BL-001)

This document defines the minimal deterministic contract for the **Prompt Intake & Requirement Parser** vertical slice.

## Entry Point

- Python API: `pressure_vessels.requirements_pipeline.parse_prompt_to_requirement_set(prompt: str, now_utc: datetime | None = None)`

## Output Artifact

The parser returns a `RequirementSet.v1` structure suitable for JSON serialization.

### Schema: `RequirementSet.v1`

```json
{
  "schema_version": "RequirementSet.v1",
  "generated_at_utc": "2026-04-18T00:00:00+00:00",
  "input_prompt": "<original prompt>",
  "requirements": {
    "design_pressure": {
      "value": 1800000.0,
      "unit": "Pa",
      "source_text": "18 bar design pressure"
    }
  },
  "unresolved_gaps": [
    {
      "field": "code_standard",
      "reason": "Mandatory field missing or not parseable from prompt."
    }
  ],
  "downstream_blocked": true,
  "deterministic_hash": "<sha256 over canonical normalized requirements>"
}
```

## Mandatory Field Policy

The following fields are mandatory for downstream design-basis processing:

- `fluid`

- `design_pressure`

- `design_temperature`

- `capacity`

- `code_standard`

If any mandatory field is absent/unparseable:

- it is listed in `unresolved_gaps`

- `downstream_blocked` is set to `true`

## Canonical Unit Policy

Normalized canonical units in `RequirementSet.v1`:

- `design_pressure` → `Pa`

- `design_temperature` → `C`

- `capacity` → `m3`

- `corrosion_allowance` → `mm`

## Determinism/Traceability Controls

- Deterministic regex-based extraction only (no non-deterministic model calls).

- `deterministic_hash` is SHA-256 over canonical normalized requirement values/units with stable key ordering.

- `source_text` stores matched prompt substring for traceability.

- `generated_at_utc` can be injected (`now_utc`) to support reproducible tests.

## BL-002 Handoff Contract

BL-002 may proceed **only when**:

See also: `docs/interfaces/design_basis_pipeline_contract.md` for BL-002 output contract.

- `downstream_blocked == false`

- `unresolved_gaps` is empty

- Required normalized fields listed above are present in `requirements`
