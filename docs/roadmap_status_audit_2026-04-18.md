# Roadmap and Documentation Cross-Check Audit — 2026-04-18

## Scope

This audit cross-checks roadmap status in `docs/development_backlog.yaml` against:

- implemented pipelines under `src/pressure_vessels/`,
- behavioral coverage in `tests/`,
- contracts in `docs/interfaces/`,
- sample artifacts in `artifacts/`, and
- roadmap narrative in `README.md` and `docs/architecture.md`.

## Method

1. Ran full test suite to verify functional baseline (`pytest -q`).
2. Ran markdown lint across repository docs (`./markdownlint-cli2 "**/*.md" "#node_modules"`).
3. Reviewed BL-tagged modules, tests, interface contracts, runbooks, and artifacts.
4. Compared each backlog item marked `todo` with direct implementation evidence.

## Executive Assessment

As of **2026-04-18**, the repository implementation is ahead of the previously recorded roadmap status. The backlog had stale `todo` states for multiple delivered items.

### Status corrections applied

The following backlog items were changed from `todo` to `done` based on implemented code + tests + contracts:

- **BL-003a** MAWP checks
- **BL-003b** external pressure / buckling checks
- **BL-003c** reinforcement-area replacement checks
- **BL-003d** margin/utilization reporting
- **BL-003e** model-domain/validity-envelope gate
- **BL-004** compliance report generation
- **BL-005** standards ingestion pipeline
- **BL-007** certification dossier export
- **BL-009** multi-standard design routes

After this correction, all baseline BL-001..BL-012 entries are in `done` state.

### New roadmap items added after cross-check

To keep roadmap-driven planning active, the backlog now includes a new hardening tranche:

- **BL-013** materials and corrosion module integration
- **BL-014** geometry/CAD interface + strict sizing-input gate
- **BL-015** dossier placeholder replacement with signed BL-008 report + deterministic PDF rendering
- **BL-016** workflow orchestrator with human-in-the-loop approval gates
- **BL-017** QA benchmark and cross-verification harness

## Evidence Summary by Corrected Item

- **BL-003a..BL-003e:** calculation pipeline includes MAWP, UG-28 external checks, UG-37 reinforcement checks, utilization/near-limit fields, and model-domain gating; test coverage validates each behavior.
- **BL-004:** deterministic compliance dossier generator exists with contract and tests.
- **BL-005:** ingestion pipeline covers source intake, parsing, normalization, semantic links, regression gate, immutable release write path, with dedicated runbook and tests.
- **BL-007:** dossier export package generator includes machine JSON + PDF payload route, signed snapshot references, inspector workflow, and deterministic write path with tests.
- **BL-009:** design basis supports deterministic multi-route selection (ASME / PED), route-specific applicability with `standard_route_id`, and tests validating both routes.

## Documentation Consistency Notes

- Fixed one markdown lint issue (`MD012`) in `docs/architecture.md`.
- Roadmap narrative in `README.md` remains phase-oriented (MVP/Production/Advanced) and is consistent at a capability level.
- Machine-readable roadmap status now matches delivered implementation and interface documentation.

## Commands Executed

- `pytest -q`
- `./markdownlint-cli2 "**/*.md" "#node_modules"`
- `rg -n "MAWP|external-pressure|UG-28|reinforcement|utilization|near_limit|validity envelope" src/pressure_vessels tests`
- `rg -n "multi-standard|standard_route_id|PED|ASME" src/pressure_vessels/design_basis_pipeline.py tests/test_design_basis_pipeline.py docs/interfaces/design_basis_pipeline_contract.md`
- `sed -n ...` and `nl -ba ...` inspections for roadmap/docs/status verification

## Conclusion

Roadmap status and documentation are synchronized with current implementation, and a new `todo` queue (BL-013..BL-017) has been added for the next development wave as of **April 18, 2026**.

## Reconciliation Audit Addendum — F1 (2026-04-18)

| id | title | current status | evidence (file/line or PR) | corrected status | rationale |
|---|---|---|---|---|---|
| BL-001 | Implement prompt parsing and requirement normalization pipeline | done | `src/pressure_vessels/requirements_pipeline.py:1-270`; `tests/test_requirements_pipeline.py:1-86` | done | Implemented and covered by dedicated pipeline tests. |
| BL-002 | Build design basis and code applicability matrix | done | `src/pressure_vessels/design_basis_pipeline.py:1-434`; `tests/test_design_basis_pipeline.py:1-170` | done | Deterministic design-basis + applicability matrix are implemented and tested. |
| BL-003 | Implement core ASME Div 1 sizing checks | done | `src/pressure_vessels/calculation_pipeline.py:1-1130`; `tests/test_calculation_pipeline.py:1-673` | done | Core calculation checks and records are implemented with extensive coverage. |
| BL-003a | Implement MAWP check | done | `src/pressure_vessels/calculation_pipeline.py:629-671`; `tests/test_calculation_pipeline.py:493-518` | done | MAWP route is present and validated by tests. |
| BL-003b | Implement external-pressure / buckling check | done | `src/pressure_vessels/calculation_pipeline.py:843-885`; `tests/test_calculation_pipeline.py:535-553` | done | UG-28 external-pressure logic exists and is tested. |
| BL-003c | Implement reinforcement-area replacement (UG-37/UG-45 full) | done | `src/pressure_vessels/calculation_pipeline.py:795-841`; `tests/test_calculation_pipeline.py:472-491` | done | Reinforcement-area replacement check implemented and verified. |
| BL-003d | Report margins and utilization ratios | done | `src/pressure_vessels/calculation_pipeline.py:730-779`; `tests/test_calculation_pipeline.py:105-135` | done | Margin/utilization fields are emitted and asserted. |
| BL-003e | Enforce model-domain / validity-envelope gate | done | `src/pressure_vessels/calculation_pipeline.py:1028-1088`; `tests/test_calculation_pipeline.py:554-618` | done | Fail-closed validity gate is implemented and tested for error/metadata paths. |
| BL-004 | Generate basic compliance report | done | `src/pressure_vessels/compliance_pipeline.py:1-330`; `tests/test_compliance_pipeline.py:1-200` | done | Compliance dossier generation and evidence mapping are implemented and tested. |
| BL-005 | Standards ingestion pipeline | done | `src/pressure_vessels/standards_ingestion_pipeline.py:1-219`; `tests/test_standards_ingestion_pipeline.py:1-135` | done | End-to-end deterministic ingestion workflow is implemented and covered. |
| BL-006 | Implement full traceability graph | done | `src/pressure_vessels/traceability_pipeline.py:1-339`; `tests/test_traceability_pipeline.py:1-145` | done | Revisioned traceability graph artifact and audit query paths are implemented. |
| BL-007 | Certification dossier export | done | `src/pressure_vessels/dossier_export_pipeline.py:1-542`; `tests/test_dossier_export_pipeline.py:1-234` | done | Export package path (JSON + PDF payload) and gates are implemented and tested. |
| BL-008 | Add change impact and selective re-verification | done | `src/pressure_vessels/change_impact_pipeline.py:1-376`; `tests/test_change_impact_pipeline.py:1-226` | done | Delta detection, selective re-verification, and signed impact report are implemented. |
| BL-009 | Support multi-standard design routes | done | `src/pressure_vessels/design_basis_pipeline.py:236-434`; `tests/test_design_basis_pipeline.py:68-118` | done | Deterministic ASME/PED routing is implemented and validated. |
| BL-010 | Add optimization for cost and manufacturability | done | `src/pressure_vessels/optimization_pipeline.py:1-284`; `tests/test_optimization_pipeline.py:1-129` | done | Optimization workflow and report generation are implemented with tests. |
| BL-011 | Integrate enterprise systems (PLM/ERP/QMS) | done | `src/pressure_vessels/enterprise_integration_pipeline.py:1-277`; `tests/test_enterprise_integration_pipeline.py:1-126` | done | Integration adapter and observability behavior are implemented and tested. |
| BL-012 | Enforce governance gates in CI | done | `src/pressure_vessels/governance_pipeline.py:1-219`; `tests/test_governance_pipeline.py:1-143` | done | Governance policy checks and exception behavior are implemented and tested. |
| BL-013 | Implement materials and corrosion module integration | done | `src/pressure_vessels/materials_module.py:1-79`; `src/pressure_vessels/calculation_pipeline.py:471-582`; `tests/test_calculation_pipeline.py:137-262`; `docs/interfaces/calculation_pipeline_contract.md:36-79` | done | Materials basis, corrosion policy, and calculation integration are implemented with contract + tests. |
| BL-014 | Add geometry/CAD interface and strict sizing-input gate | done | `src/pressure_vessels/geometry_module.py:1-100`; `src/pressure_vessels/calculation_pipeline.py:471-543`; `tests/test_calculation_pipeline.py:180-230`; `docs/interfaces/calculation_pipeline_contract.md:40-53` | done | Geometry adapter, strict gate, and CAD-ready export wiring are present and tested. |
| BL-015 | Replace dossier placeholders with signed change-impact and PDF rendering | done | `src/pressure_vessels/dossier_export_pipeline.py:162-537`; `tests/test_dossier_export_pipeline.py:118-221`; `docs/interfaces/dossier_export_pipeline_contract.md:1-63`; `docs/runbooks/dossier_export_pipeline_runbook.md:1-65` | done | Signed impact embedding and deterministic canonical PDF rendering paths are implemented with docs/tests. |
| BL-016 | Implement workflow orchestrator with human-in-the-loop approval gates | todo | `docs/development_backlog.yaml` item definition; no `orchestrator` module/test/contract currently present in repository | todo | First not-yet-implemented item whose declared dependencies are all `done`; should remain the next coding target. |
| BL-017 | Build QA benchmark and cross-verification harness | todo | `docs/development_backlog.yaml` depends_on includes `BL-016`, which is not done | blocked | Dependency not yet satisfied; status corrected to `blocked` to prevent out-of-order execution. |
