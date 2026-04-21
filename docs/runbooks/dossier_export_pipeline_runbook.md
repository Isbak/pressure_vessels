# Dossier Export Pipeline Runbook (BL-015)

Operational runbook for producing deterministic certification dossier exports with embedded signed BL-008 impact reports and canonical PDF rendering.

## Scope

- BL-007 dossier export package generation.
- BL-015 hardening integrations:
  - signed `ImpactReport.v1` embedding,
  - deterministic canonical PDF render,
  - inspector/regulator sign-off transition artifacts.

## Preconditions

1. Upstream artifacts (BL-001..BL-008) are generated for a target revision.
2. `ImpactReport.v1` exists and `to_revision_id` matches the dossier `revision_id`.
3. Deterministic timestamp is supplied (`now_utc`) when reproducibility tests or artifact comparison is required.

## Execution

```python
from pressure_vessels.dossier_export_pipeline import (
    generate_certification_dossier_export,
    verify_dossier_export_signatures,
    write_certification_dossier_export,
)

export = generate_certification_dossier_export(
    requirement_set,
    design_basis,
    applicability_matrix,
    calculation_records,
    non_conformance_list,
    compliance_dossier_human,
    compliance_dossier_machine,
    traceability_graph_revision,
    impact_report,
    revision_id="REV-0007",
    previous_revision_id="REV-0006",
    now_utc=fixed_now,
)

package_path, payload_path, canonical_pdf_path = write_certification_dossier_export(export, "artifacts/")
verify_dossier_export_signatures(export)  # fail-closed: raises ValueError on tamper/unsigned payloads
```

## Expected Outputs

- `CertificationDossierExportPackage.v1.json`
- `CertificationDossierPDFPayload.v1.json`
- `CanonicalDossierPDF.v1.pdf`

The package must include:

- `change_impact_report` populated from signed BL-008 `ImpactReport.v1`.
- `workflow_signoff_transitions` with deterministic transition states and evidence refs.
- `canonical_pdf_render.content_sha256` and matching `CanonicalDossierPDF.v1#...` entry in `package_artifact_refs`.
- `signing.signature` populated and verifiable against package deterministic fields.

## Failure Modes

- `ValueError: ... impact report revision mismatch.`
  - Cause: BL-008 `to_revision_id` and BL-015 `revision_id` do not match.
- `ValueError: ... unsupported ImpactReport schema version.`
  - Cause: report payload is not `ImpactReport.v1`.
- `ValueError: ... traceability graph compliance hash mismatch.`
  - Cause: BL-007 handoff evidence chain is inconsistent.
- `ValueError: BL-037 signature verification failed: ...`
  - Cause: unsigned payload, tampered signature fields, or canonical PDF hash/content mismatch.

## Audit Checklist

1. Verify `package_artifact_refs` includes `ImpactReport.v1#<hash>` and `CanonicalDossierPDF.v1#<hash>`.
2. Verify `workflow_signoff_transitions` contains `WF-T001`, `WF-T002`, and `WF-T003`.
3. Re-run export with the same fixed inputs and timestamp; confirm identical `deterministic_hash`.
4. Run `verify_dossier_export_signatures(export)` and confirm no exception is raised.
