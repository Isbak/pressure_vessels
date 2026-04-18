# Certification Dossier Export Contract (BL-007)

This document defines the deterministic contract for the BL-007 certification dossier export package.

## Entry Point

- Python API: `pressure_vessels.dossier_export_pipeline.generate_certification_dossier_export(requirement_set, design_basis, applicability_matrix, calculation_records, non_conformance_list, compliance_dossier_human, compliance_dossier_machine, traceability_graph_revision, revision_id, previous_revision_id=None, now_utc=None)`
- Persistence helper: `pressure_vessels.dossier_export_pipeline.write_certification_dossier_export(export_package, directory, filename_prefix="")`

## BL-007 Handoff Gate (Required)

BL-007 proceeds only if all are true:

- BL-001..BL-006 artifact schema versions match their current `*.v1` versions.
- All upstream source-hash links are consistent (`RequirementSet`, `DesignBasis`, `ApplicabilityMatrix`, `CalculationRecords`, `NonConformanceList`, compliance dossiers, traceability graph).
- `revision_id` is non-empty.
- Traceability graph references the exact machine dossier hash (`source_compliance_dossier_hash == ComplianceDossierMachine.deterministic_hash`).

If any condition fails, BL-007 raises a deterministic `ValueError` (fail closed).

## Output Artifact

`generate_certification_dossier_export` returns:

- `CertificationDossierExportPackage.v1`

The package includes:

1. **Machine-readable JSON package payload**.
2. **PDF-oriented payload route** (`CertificationDossierPDFPayload.v1`) to support deterministic rendering.
3. **Signed calculation snapshot references** (`SignedCalculationSnapshotSet.v1`) derived from calculation check reproducibility hashes.
4. **Change impact placeholder report** (`ChangeImpactReport.v1.placeholder`) reserved for BL-008 delta logic.
5. **Inspector/regulator workflow scaffold** (`InspectorRegulatorWorkflow.v1`).
6. **Template catalog** (`CertificationDossierTemplateCatalog.v1`) for report section composition.

### Key JSON Fields

- `template_catalog[]`: deterministic section catalog used by PDF rendering and package review.
- `signed_calculation_snapshots[]`: one record per `CalculationRecords.checks[]` with `artifact_ref`, `canonical_payload_sha256`, and `signature_ref`.
- `change_impact_report`: placeholder section containing impacted clauses and BL-008 integration note.
- `inspector_regulator_workflow[]`: deterministic review sequence (`design_authority` -> `authorized_inspector` -> `regulator`).
- `pdf_payload`: canonical payload for future PDF renderer.
- `package_artifact_refs[]`: evidence references tying package, PDF payload, compliance, traceability, signed snapshots, and change impact sections.

## Deterministic Controls

- `generated_at_utc` supports injection via `now_utc` for reproducible tests.
- Signed snapshots are sorted by `check_id`.
- Section templates and workflow steps are fixed deterministic catalogs.
- Package hash is SHA-256 of canonical unsigned payload (`json.dumps(..., sort_keys=True, separators=(",", ":"))`).

## Acceptance-Criteria Mapping

- **PDF + machine-readable JSON included**: `pdf_payload` and root package JSON.
- **Signed snapshots + change impact report included**: `signed_calculation_snapshots` and `change_impact_report`.
- **Inspector/regulator review workflow supported**: `inspector_regulator_workflow` + `template_catalog` sectioning.
