# ADR-0006: Safety-Critical Rounding Policy for BL-003 Calculations

- Status: accepted
- Date: 2026-04-20
- Related findings: AF-003
- Related interface contract: `docs/interfaces/calculation_pipeline_contract.md`

## Context

`pressure_vessels.calculation_pipeline` performs deterministic sizing checks for
required thickness, provided thickness, utilization ratio, MAWP margins, and SI
normalization. Prior to this ADR, the implementation used inline `round(..., 9)`
operations without a documented rationale. Audit finding AF-003 flagged this as
non-auditable for safety-critical pass/fail behavior.

## Decision

BL-003 standardizes safety-critical rounding through a single helper:
`_round_safety_critical(value: float) -> float`.

The helper uses **9 decimal places** in canonical SI units (`m`, `Pa`) for all
safety-critical calculations and normalization paths.

Rationale:

1. `1e-9 m` resolution corresponds to nanometer-scale granularity, far smaller
   than pressure-vessel fabrication and inspection tolerances.
2. `1e-9 Pa` resolution is similarly far below engineering uncertainty in input
   pressure/stress data.
3. Quantizing at this level eliminates non-deterministic floating-point noise
   in pass/fail thresholds, utilization, and reproducibility hashes.
4. The precision is conservative for determinism while remaining operationally
   irrelevant to manufacturing decisions.

## Consequences

- Safety-critical rounding behavior is now centrally named and testable.
- Inline precision drift risk is reduced because call sites no longer hardcode
  decimal counts.
- Auditors can trace precision intent from implementation to ADR and interface
  contract.

## Change Control

Future changes to safety-critical rounding precision (decimal count, method, or
scope) require all of the following:

1. New/updated ADR with engineering rationale and impact assessment.
2. Contract update in `docs/interfaces/calculation_pipeline_contract.md`.
3. Regression-test updates that pin expected boundary behavior.
4. Explicit code-review approval from calculation and quality owners.
