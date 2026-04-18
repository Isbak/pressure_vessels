# BL-003 Delivery Audit — 2026-04-18

## Scope

Audit of the BL-003 delivery (commit `cc23b81` "Implement BL-003 deterministic calculation pipeline") against the project documentation:

- `docs/development_backlog.yaml` (BL-003 entry, lines 60–80)

- `README.md` §3 "Calculation Engine", §12 "Roadmap — Phase 1: MVP"

- `docs/semantic_layer_workflows_for_requirements_verification.md` Workflow D, §7 Automation Quality Gates, §8 Minimum Deliverables

- `docs/interfaces/requirements_pipeline_contract.md`, `docs/interfaces/design_basis_pipeline_contract.md`

- `docs/next_code_generation_prompt.md`

- `AGENT_GOVERNANCE.md`, `docs/decision-log/`

## Method

1. Re-read the BL-003 acceptance criteria, deliverables, and referenced workflow/README sections.

2. Reviewed the delivered code (`src/pressure_vessels/calculation_pipeline.py`, `src/pressure_vessels/__init__.py`), the tests (`tests/test_calculation_pipeline.py`), and the persisted sample artifacts under `artifacts/bl-003/`.

3. Ran the full test suite (`pytest -q`) — 12/12 green.

4. Re-executed the pipeline on the canonical propane prompt and compared `deterministic_hash`/payloads against the checked-in sample artifacts — both the `CalculationRecords.v1` and `NonConformanceList.v1` samples reproduce byte-for-byte.

## Executive Summary

BL-003 delivers the three acceptance criteria for an MVP slice: deterministic shell/head/nozzle thickness checks, unit-safe inputs with per-check reproducibility hashes, and a pass/fail + non-conformance artifact pair. The implementation is clean, deterministic, and consistent with the BL-001/BL-002 style.

However, several **documentation, governance, and scope** items from the project docs were not updated alongside the delivery. The implemented slice is narrower than the README "Calculation Engine" and Workflow D descriptions, and supporting artifacts (interface contract, backlog status, next-code prompt, ADR) are stale.

Overall assessment: **delivery meets backlog-level acceptance criteria; documentation trail and forward scope need follow-up work.**

## What the Delivery Satisfies

| BL-003 acceptance criterion | Evidence |
| --- | --- |
| Deterministic sizing checks for shell/head/nozzle | `calculation_pipeline.py:239-296` — UG-27-shell, UG-32-head, UG-45-nozzle records |
| Unit-safe with reproducibility hashes | `_to_si_pressure`/`_to_si_length` at `calculation_pipeline.py:352-374`; per-check `ReproducibilityMetadata` (sha256) at `calculation_pipeline.py:312-335`; per-artifact `deterministic_hash` at `calculation_pipeline.py:155,173` |
| Pass/fail records + non-conformance list stored | `_build_non_conformances` at `calculation_pipeline.py:338-349`; sample artifacts under `artifacts/bl-003/` |
| Deliverable: `CalculationRecords` | `artifacts/bl-003/CalculationRecords.v1.sample.json` |
| Deliverable: Non-conformance list | `artifacts/bl-003/NonConformanceList.v1.sample.json` |
| BL-001/BL-002 handoff gate enforced | `_validate_handoff_gate` at `calculation_pipeline.py:186-199` (rejects blocked/gapped requirement sets and non-ASME Div 1 design basis) |
| Determinism gate (Quality Gate #5) | Test `test_calculation_pipeline_is_deterministic_with_fixed_timestamp` and independent re-run of the canonical prompt both reproduce the checked-in artifact hashes `0b5d0c04…` and `1023db5f…` |

## Detailed Findings

### F1 — Backlog status not updated after delivery (Medium)

`docs/development_backlog.yaml:65` still records `status: todo` for BL-003, yet the feature branch was merged (commit `cc23b81`), code is present under `src/pressure_vessels/calculation_pipeline.py`, tests pass, and the sample artifacts are committed.

**Impact:** the machine-readable roadmap reports BL-003 as not started, which breaks the traceability the backlog is meant to provide and will mislead downstream planning (BL-004 depends on BL-003).

**Recommended fix:** set `status: done`, mirroring the update pattern used for BL-001/BL-002.

### F2 — "Next-code" prompt is stale (Medium)

`docs/next_code_generation_prompt.md:10-22` still reads `Current completed items: BL-001, BL-002` and `Next item to implement: BL-003`.

**Impact:** the document is intended to drive the next roadmap iteration. As written, it will re-generate an already-delivered slice. It should advance to BL-004 (Generate basic compliance report — the only Phase 1 item with its dependencies now satisfied).

**Recommended fix:** update the prompt so "completed" lists BL-001..BL-003 and "next" points at BL-004 with its acceptance criteria and `ComplianceDossier` deliverable names.

### F3 — No interface contract document for BL-003 (Medium)

BL-001 and BL-002 each ship with an interface contract under `docs/interfaces/` (`requirements_pipeline_contract.md`, `design_basis_pipeline_contract.md`). No equivalent `docs/interfaces/calculation_pipeline_contract.md` exists.

**Impact:** breaks the established pattern; downstream consumers (BL-004 compliance report, BL-006 traceability graph) lack a canonical, reviewable description of the `CalculationRecords.v1` and `NonConformanceList.v1` schemas, the handoff gate, the canonical-unit policy, and the deterministic hashing scheme. The schema is currently discoverable only by reading the implementation.

**Recommended fix:** add `docs/interfaces/calculation_pipeline_contract.md` documenting entry point, BL-002 handoff gate, both artifact schemas, and determinism/unit controls; link it from `README.md`'s "Related repository docs" list alongside the existing BL-001/BL-002 contracts.

### F4 — Scope narrower than README §3 and Workflow D (Medium)

Documented scope for the Calculation Engine (`README.md:103` — "shell/head/nozzle/thickness/MAWP checks") and Workflow D step 1 (`semantic_layer_workflows_for_requirements_verification.md:125` — "thickness, MAWP, external pressure, reinforcement, and related checks") covers five check families. The delivery implements one: **thickness for shell/head/nozzle under internal pressure**.

Not implemented and not tracked anywhere as deferred:

- MAWP check

- External-pressure / buckling check

- Reinforcement-area replacement (UG-37 / UG-45 full)

- Margin / utilization ratio reporting (Workflow D step 3 — "Compute margins and utilization ratios")

- Model-domain / validity-envelope check (Workflow D step 4; Quality Gate #2)

The BL-003 acceptance criterion only requires "shell/head/nozzle **and related checks**" so the delivery is defensible as an MVP slice, but the narrower scope is not recorded. Code comments label the formulas as "Placeholder extension point" (`calculation_pipeline.py:247, 267, 287`) but that is not visible from the roadmap.

**Recommended fix:** either (a) add follow-up backlog items for MAWP, external pressure, reinforcement, utilization, and domain gating; or (b) add explicit "deferred from BL-003" notes in `docs/development_backlog.yaml` and/or a new ADR, so the coverage gap is auditable rather than implicit.

### F5 — Calculation records lack clause traceability (Medium)

`CalculationRecord` (`calculation_pipeline.py:56-76`) carries `check_id` (`"UG-27-shell"`), `component`, and `formula` string, but **no explicit `clause_id` field linking back to the `ApplicabilityMatrix` produced by BL-002**. Automation Quality Gate #4 (`semantic_layer_workflows_for_requirements_verification.md:309` — "fail if any pass/fail result lacks source clause + input snapshot") cannot be enforced on the current schema without a trailing string parse of `check_id`.

Similarly, `CalculationRecordsArtifact` references the design basis via `source_design_basis_signature` but **does not reference the `ApplicabilityMatrix.deterministic_hash`**, which is the artifact that actually declares which clauses apply.

**Impact:** downstream BL-004/BL-006 (compliance matrix, traceability graph) will either need to reverse-engineer clause ids from check ids or be extended with a clause-link field.

**Recommended fix:** add explicit `clause_id` and `source_applicability_matrix_hash` fields to the records/artifact schema (and, once F3 is addressed, document them there).

### F6 — Hardcoded defaults bypass DesignBasis (Medium)

When `sizing_input=None`, `_normalize_and_resolve_inputs` (`calculation_pipeline.py:220-236`) silently injects:

- `allowable_stress = 138 MPa`

- `joint_efficiency = 0.85`

- `shell_inside_diameter = 2.0 m`, `shell_provided_thickness = 0.020 m`

- `head_inside_diameter = 2.0 m`, `head_provided_thickness = 0.018 m`

- `nozzle_inside_diameter = 0.35 m`, `nozzle_provided_thickness = 0.004 m`

These values are load-bearing — they determine pass/fail — but are not recorded in `DesignBasis.assumptions` (the BL-002 slot for exactly this), not surfaced as `unresolved_gaps` on the RequirementSet, and not mentioned in an ADR or the sample artifact commentary.

This conflicts with:

- Workflow C step 4: "Register assumptions and conservative defaults" (`semantic_layer_workflows_for_requirements_verification.md`).

- README §9 "Explainability: Every result includes formula and clause provenance" (`README.md:273`).

- `AGENT_GOVERNANCE.md` expectation that engineering assumptions are explicit and reviewable.

**Impact:** the sample `CalculationRecords` artifact looks authoritative (signed hash, deterministic), but the pass/fail outcome depends on hidden assumptions that would never survive a certification review. A reader of `DesignBasis.v1.sample.json` cannot see why allowable stress is 138 MPa.

**Recommended fix:** either require `sizing_input` explicitly (fail-closed if absent), or, if defaults must remain for test fixtures, mirror them into `DesignBasis.assumptions` via an extension to `build_design_basis` and emit an `unresolved_gaps`-style warning when they are applied.

### F7 — Handoff-gate unit check is incomplete (Low)

`_EXPECTED_REQUIREMENT_UNITS` (`calculation_pipeline.py:17-20`) validates only `design_pressure` (Pa) and `corrosion_allowance` (mm). The canonical unit policy in `docs/interfaces/requirements_pipeline_contract.md` §"Canonical Unit Policy" mandates canonical units for **all** five requirement fields, and Quality Gate #1 ("Unit-consistency gate: no implicit unit conversions") applies uniformly.

**Impact:** low today because `design_temperature` and `capacity` are not consumed by the current checks, but the gate will silently accept non-canonical inputs for those fields, so a future check that does consume them would silently operate on wrong units.

**Recommended fix:** extend `_EXPECTED_REQUIREMENT_UNITS` to cover every field listed in the canonical unit policy, or import the canonical map from `requirements_pipeline.CANONICAL_UNITS` to keep them in lock-step.

### F8 — "Stored" in AC3 is only satisfied by committed samples (Low)

Acceptance criterion 3 says the records are "stored". The pipeline returns dataclasses — there is **no serialization/persistence helper** in `calculation_pipeline.py` that writes `*.v1.json` to `artifacts/bl-003/`. The checked-in samples were produced manually as part of the commit.

**Impact:** low for an MVP. But an agent executing the pipeline at runtime has no standard path to emit a signed artifact, which BL-004 (compliance report) and BL-007 (dossier export) will need.

**Recommended fix:** add a small `write_calculation_artifacts(path)` helper (mirroring whatever pattern BL-001/BL-002 will eventually use), or specify in the interface contract (F3) that persistence is the caller's responsibility.

### F9 — No ADR captures BL-003 engineering/modeling choices (Low)

`docs/decision-log/` holds ADR-0001..ADR-0004 covering governance, LLM serving, graph store, and vector retrieval. BL-003 makes several engineering-significant choices that are not captured in an ADR:

- Using placeholder thickness formulas rather than the full UG-27(c)(1), UG-32(d)/(e), and UG-45 equations.

- Hardcoded defaults for allowable stress / joint efficiency / geometry (see F6).

- Using SHA-256 over canonicalized JSON for both per-check and per-artifact reproducibility hashes, with the specific canonicalization rule `sort_keys=True, separators=(",",":")`.

**Impact:** medium-term auditability — future reviewers (or an agent doing BL-008 change-impact analysis) have no single place to understand why the numeric outputs are what they are.

**Recommended fix:** add `ADR-0005-bl-003-sizing-check-scope-and-defaults.md` documenting the MVP placeholder scope, the chosen canonical hashing scheme, and the default material/geometry assumptions (until the Materials Module replaces them).

## Prioritized Remediation Plan

1. **P1 — Fix documentation trail (F1, F2, F3).** Mark BL-003 `done` in the backlog, point `next_code_generation_prompt.md` at BL-004, and add the `calculation_pipeline_contract.md` interface document. Unblocks BL-004.

2. **P1 — Surface hidden assumptions (F6).** Either fail-closed when `sizing_input` is absent or propagate the defaults into `DesignBasis.assumptions` so the evidence graph is complete.

3. **P2 — Add clause-level traceability to records (F5).** Required for BL-004/BL-006 to meet Quality Gate #4.

4. **P2 — Track scope deferrals (F4).** Either new backlog items for MAWP / external pressure / reinforcement / utilization / domain gating, or explicit "deferred from BL-003" notes.

5. **P3 — Strengthen handoff unit gate (F7), add persistence helper (F8), and capture BL-003 decisions in an ADR (F9).**

## Commands Run

- `pytest -q` (12 passed)

- Independent re-execution of `run_calculation_pipeline` on the canonical propane prompt and comparison against `artifacts/bl-003/*.v1.sample.json`

- Review of `git log` around BL-003 merge (`cc23b81`, `818f057`)

## Audit Conclusion

BL-003's code, tests, and sample artifacts cleanly satisfy the backlog's three acceptance criteria and reproduce deterministically. The gaps are around documentation freshness, governance trail, and scope visibility — none of which block the delivery standing as a valid MVP slice, but all of which should be addressed before BL-004 starts, to preserve the documentation-first posture the repository advertises.
