# Architecture Overview

This repository documents an agent-driven, modular pressure vessel design platform.

Primary concerns:

- Requirements capture and normalization

- Standards-aware calculation services

- Compliance traceability and report generation

- Human-in-the-loop governance and approvals

## BL-006 Traceability Graph

- Schema: `TraceabilityGraphRevision.v1` with immutable, revision-scoped link snapshots.
- Link endpoints: requirement, clause, model, calculation, artifact, approval.
- Audit helpers support revision-scoped and clause-scoped evidence retrieval and report templating.

## BL-007 Certification Dossier Export

- Schema: `CertificationDossierExportPackage.v1` with embedded `CertificationDossierPDFPayload.v1` route for deterministic PDF rendering.
- Includes `CertificationDossierTemplateCatalog.v1`, signed calculation snapshot references, and `ChangeImpactReport.v1.placeholder` section for BL-008 integration.
- Adds an `InspectorRegulatorWorkflow.v1` scaffold so design authority, inspector, and regulator review steps can be tracked against artifact refs.

## BL-008 Change Impact and Selective Re-Verification

- Schema set: `RevisionTraceSnapshot.v1`, `RevisionDelta.v1`, `ImpactReport.v1`, and `BaselineUpdateStatus.v1`.
- Revision deltas are detected automatically for requirement, code, and model fingerprints.
- Impact analysis validates snapshot alignment to revisioned traceability artifacts (`revision_id`, requirement hash, and graph hash) plus current calculation hash integrity before delta computation.
- Minimal re-verification scope is computed from traceability graph link deltas and executed deterministically against current calculation records.
- Every revision delta emits a signed `ImpactReport.v1` artifact with evidence links and an explicit baseline update decision.
- Baseline decisions can also be persisted as standalone `BaselineUpdateStatus.v1` artifacts for release-gate consumption.

## BL-009 Multi-Standard Design Routes

- Design-basis routing now supports deterministic route configuration for ASME and PED defaults.
- Route resolution is auditable through `route_selection_audit` with explicit match/selection reasons.
- Applicability records remain clause-level and now include `standard_route_id` for cross-standard traceability integrity.
- Additional standards can be added by injecting deterministic `StandardRouteConfig` entries.

