# Certification Dossier Export Contract (BL-007 + BL-015)

This document defines the deterministic contract for the BL-007 certification dossier export package and the BL-015 hardening extensions.

## Entry Point

- Python API: `pressure_vessels.dossier_export_pipeline.generate_certification_dossier_export(requirement_set, design_basis, applicability_matrix, calculation_records, non_conformance_list, compliance_dossier_human, compliance_dossier_machine, traceability_graph_revision, change_impact_report, revision_id, previous_revision_id=None, now_utc=None)`
- Persistence helper: `pressure_vessels.dossier_export_pipeline.write_certification_dossier_export(export_package, directory, filename_prefix="")`
- Deterministic renderer: `pressure_vessels.dossier_export_pipeline.render_canonical_dossier_pdf(pdf_payload, template_catalog, impact_report, signoff_transitions)`
- Verification harness: `pressure_vessels.dossier_export_pipeline.verify_dossier_export_signatures(export_package)`

## BL-007 Handoff Gate (Required)

BL-007 proceeds only if all are true:

- BL-001..BL-006 artifact schema versions match their current `*.v1` versions.
- BL-008 impact report schema and revision alignment are valid (`schema_version == ImpactReport.v1`, `to_revision_id == revision_id`).
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
4. **Embedded signed BL-008 impact report** (`ImpactReport.v1`).
5. **Inspector/regulator workflow scaffold** (`InspectorRegulatorWorkflow.v1`).
6. **Workflow sign-off transitions with evidence refs** (deterministic state transitions).
7. **Template catalog** (`CertificationDossierTemplateCatalog.v1`) for report section composition.
8. **Canonical deterministic PDF render artifact** (`CanonicalDossierPDF.v1`) produced from payload templates.
9. **Dossier signature envelope** (`signing`) that binds revision metadata, canonical PDF hash, and embedded `ImpactReport.v1` signature.

### Key JSON Fields

- `template_catalog[]`: deterministic section catalog used by PDF rendering and package review.
- `signed_calculation_snapshots[]`: one record per `CalculationRecords.checks[]` with `artifact_ref`, `canonical_payload_sha256`, and `signature_ref`.
- `change_impact_report`: embedded signed BL-008 payload (no placeholder rows).
- `inspector_regulator_workflow[]`: deterministic review sequence (`design_authority` -> `authorized_inspector` -> `regulator`).
- `workflow_signoff_transitions[]`: deterministic sign-off transitions with trigger + required evidence refs.
- `pdf_payload`: canonical payload for future PDF renderer.
- `canonical_pdf_render`: deterministic rendered content with `content_sha256` and immutable renderer metadata.
- `package_artifact_refs[]`: evidence references tying package, PDF payload, canonical PDF render, compliance, traceability, signed snapshots, and change impact sections.
- `signing`: deterministic signature metadata (`algorithm`, `signing_key_ref`, `signature`) for fail-closed integrity verification.

## Deterministic Controls

- `generated_at_utc` supports injection via `now_utc` for reproducible tests.
- Signed snapshots are sorted by `check_id`.
- Section templates and workflow steps are fixed deterministic catalogs.
- Canonical PDF render content is assembled deterministically from required section templates + workflow transitions + impact report hash.
- Package hash is SHA-256 of canonical unsigned payload (`json.dumps(..., sort_keys=True, separators=(",", ":"))`).
- Verification harness fail-closed checks:
  - canonical PDF `content_sha256` equals hash(content) and content is reproducible from package payload;
  - embedded BL-008 impact signature is valid for its signed fields;
  - dossier signature is valid and chained to embedded impact signature + canonical PDF hash.

## Acceptance-Criteria Mapping

- **BL-015.1 signed impact integration**: `change_impact_report.schema_version == ImpactReport.v1` and artifact refs include `ImpactReport.v1#<hash>`.
- **BL-015.2 deterministic canonical PDF rendering**: package includes `canonical_pdf_render` and `CanonicalDossierPDF.v1#<content_sha256>`.
- **BL-015.3 sign-off transitions and evidence refs**: `workflow_signoff_transitions[]` carries deterministic transitions and required evidence references.
- **BL-037.1 deterministic PDF verification**: `verify_dossier_export_signatures()` rejects tampered canonical PDF content or non-reproducible render content.
- **BL-037.2 signature verification checks**: harness validates both embedded `ImpactReport.v1` signature and dossier-level signature.
- **BL-037.3 CI gate coverage**: unsigned/tampered dossier payload tests fail in CI `python-tests`.
