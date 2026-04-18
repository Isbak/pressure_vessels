# ADR-0005: BL-003 Sizing-Check Scope, Default Assumptions, and Canonical Hashing

- Status: accepted

- Date: 2026-04-18

- Related backlog items: BL-003, BL-003a..BL-003e

- Related interface contract: `docs/interfaces/calculation_pipeline_contract.md`

## Context

BL-003 delivers the first executable slice of the Calculation Engine described in `README.md` §3 and Workflow D of `docs/semantic_layer_workflows_for_requirements_verification.md`. The slice must be deterministic, unit-safe, traceable, and reproducible. Three engineering-significant choices were not captured in a decision record as part of the initial delivery (flagged by the BL-003 audit as F4, F6, F9). This ADR documents them so that downstream items (BL-004 compliance report, BL-008 change-impact analysis) have a single source of truth for their inputs.

## Decision

### 1. MVP check scope

BL-003 implements thickness checks for:

- UG-27 cylindrical shell under internal pressure

- UG-32 head under internal pressure (simplified formula, pending head-type selection)

- UG-45 nozzle neck minimum thickness (simplified, pending reinforcement-area logic)

The following items from Workflow D are deferred and tracked as follow-up backlog entries, not silent gaps:

- BL-003a MAWP check

- BL-003b External-pressure / buckling check (UG-28 route)

- BL-003c Reinforcement-area replacement (UG-37 / UG-45 full)

- BL-003d Margin / utilization near-limit reporting (basic margin and utilization ratio are now emitted; threshold-based near-limit reporting remains)

- BL-003e Model-domain / validity-envelope gating

### 2. Placeholder defaults when `sizing_input` is absent

When a caller does not supply a `SizingCheckInput`, the pipeline injects the following deterministic defaults so that the canonical propane prompt remains runnable end-to-end:

| Field | Value | Unit | Rationale |
| --- | --- | --- | --- |
| Allowable stress (S) | 138 000 000 | Pa | Representative SA-516 Gr.70 at moderate temperature; to be replaced by Materials Module lookup. |
| Joint efficiency (E) | 0.85 | — | Common spot-RT value; placeholder until weld/NDE basis is captured. |
| Shell ID | 2.0 | m | Demo geometry. |
| Shell provided thickness | 0.020 | m | Demo geometry. |
| Head ID | 2.0 | m | Demo geometry. |
| Head provided thickness | 0.018 | m | Demo geometry. |
| Nozzle ID | 0.35 | m | Demo geometry. |
| Nozzle provided thickness | 0.004 | m | Demo geometry; intentionally below required so the non-conformance path is exercised. |
| Corrosion-allowance fallback | 1.5 | mm | Used only if RequirementSet has no `corrosion_allowance`. |

These defaults are **explicitly surfaced** in `CalculationRecordsArtifact.applied_defaults`; the artifact hash covers them. Callers who want fail-closed behavior should pass a fully populated `SizingCheckInput` built from the Materials and Geometry modules.

### 3. Canonical hashing scheme

Every deterministic hash in BL-003 is `sha256` over canonical JSON produced with `json.dumps(payload, sort_keys=True, separators=(",", ":"))`. This matches the scheme used by BL-001 and BL-002. The per-check reproducibility hash covers the fully normalized SI inputs plus outputs but excludes the hash field itself; artifact-level hashes cover every field of the unsigned payload.

### 4. Clause traceability

Each `CalculationRecord` carries a `clause_id` that must appear in the `ApplicabilityMatrix.records` with `applicable: true`. The pipeline raises `ValueError` if this invariant is violated. This closes Workflow D Quality Gates #3 (Clause coverage) and #4 (Traceability).

### 5. Canonical-unit enforcement

The BL-003 handoff gate iterates over `requirements_pipeline.CANONICAL_UNITS` and rejects any RequirementSet whose stored unit for a canonical field disagrees with the policy. This closes Workflow D Quality Gate #1 (Unit consistency).

## Consequences

- BL-003 outputs are fully reproducible and auditable without reading the source of `calculation_pipeline.py`.

- Downstream items (BL-004 compliance report, BL-006 traceability graph) can rely on `clause_id`, `source_applicability_matrix_hash`, and `applied_defaults` being present in every artifact.

- The placeholder allowable stress and joint efficiency **must** be replaced before any output is used for a real certification; this ADR makes that dependency explicit.

- The BL-002 `ApplicabilityMatrix` is extended with UG-27, UG-32, UG-45 clauses (applicable under internal pressure), so BL-003's clause-coverage gate is satisfiable with the BL-002 MVP output.

## Alternatives Considered

- **Fail-closed when `sizing_input` is absent.** Rejected because it would force every caller (including smoke tests and the repository's canonical-prompt example) to wire a full geometry before the Materials/Geometry modules exist. Deferred to a future hardening pass once those modules ship.

- **Store defaults in `DesignBasis.assumptions` only.** Rejected because the defaults are numeric and BL-003-specific; putting them in the DesignBasis would couple BL-002 to BL-003 and still leave the values invisible to consumers of the CalculationRecords artifact. Placing them in `applied_defaults` keeps the concern inside BL-003.

- **Use Decimal for pass/fail arithmetic.** Rejected for MVP; the sha256 canonicalization plus explicit `round(..., 9)` is sufficient for determinism at current precision.
