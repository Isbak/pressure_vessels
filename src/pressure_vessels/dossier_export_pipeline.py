"""Deterministic certification dossier export package generation for BL-007."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from .calculation_pipeline import (
    CALCULATION_RECORDS_VERSION,
    NON_CONFORMANCE_LIST_VERSION,
    CalculationRecordsArtifact,
    NonConformanceListArtifact,
)
from .compliance_pipeline import (
    COMPLIANCE_DOSSIER_HUMAN_VERSION,
    COMPLIANCE_DOSSIER_MACHINE_VERSION,
    ComplianceDossierHuman,
    ComplianceDossierMachine,
)
from .change_impact_pipeline import IMPACT_REPORT_VERSION, ImpactReport
from .design_basis_pipeline import APPLICABILITY_MATRIX_VERSION, DESIGN_BASIS_VERSION, ApplicabilityMatrix, DesignBasis
from .requirements_pipeline import REQUIREMENT_SET_VERSION, RequirementSet
from .traceability_pipeline import TRACEABILITY_GRAPH_REVISION_VERSION, TraceabilityGraphRevision

CERTIFICATION_DOSSIER_EXPORT_PACKAGE_VERSION = "CertificationDossierExportPackage.v1"
CERTIFICATION_DOSSIER_PDF_PAYLOAD_VERSION = "CertificationDossierPDFPayload.v1"
CANONICAL_DOSSIER_PDF_RENDER_VERSION = "CanonicalDossierPDF.v1"
TEMPLATE_CATALOG_VERSION = "CertificationDossierTemplateCatalog.v1"
SIGNED_CALCULATION_SNAPSHOT_SET_VERSION = "SignedCalculationSnapshotSet.v1"
INSPECTOR_WORKFLOW_VERSION = "InspectorRegulatorWorkflow.v1"


@dataclass(frozen=True)
class ReportSectionTemplate:
    section_id: str
    title: str
    required: bool
    source_refs: list[str]

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SignedCalculationSnapshotRef:
    check_id: str
    clause_id: str
    artifact_ref: str
    canonical_payload_sha256: str
    signature_ref: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InspectorWorkflowStep:
    step_id: str
    role: str
    prompt: str
    required_artifact_refs: list[str]
    status: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowSignoffTransition:
    transition_id: str
    from_step_id: str
    to_step_id: str
    trigger: str
    required_evidence_refs: list[str]
    state: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CertificationDossierExportPackage:
    schema_version: str
    generated_at_utc: str
    revision_id: str
    previous_revision_id: str | None
    source_requirement_set_hash: str
    source_design_basis_signature: str
    source_applicability_matrix_hash: str
    source_calculation_records_hash: str
    source_non_conformance_hash: str
    source_compliance_dossier_human_hash: str
    source_compliance_dossier_machine_hash: str
    source_traceability_graph_hash: str
    template_catalog_schema_version: str
    signed_calculation_snapshot_set_schema_version: str
    change_impact_report_schema_version: str
    inspector_workflow_schema_version: str
    canonical_pdf_render_schema_version: str
    reproducibility: dict[str, str]
    template_catalog: list[ReportSectionTemplate]
    signed_calculation_snapshots: list[SignedCalculationSnapshotRef]
    change_impact_report: dict[str, Any]
    inspector_regulator_workflow: list[InspectorWorkflowStep]
    workflow_signoff_transitions: list[WorkflowSignoffTransition]
    pdf_payload: dict[str, Any]
    canonical_pdf_render: dict[str, Any]
    package_artifact_refs: list[str]
    signing: dict[str, str]
    deterministic_hash: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at_utc": self.generated_at_utc,
            "revision_id": self.revision_id,
            "previous_revision_id": self.previous_revision_id,
            "source_requirement_set_hash": self.source_requirement_set_hash,
            "source_design_basis_signature": self.source_design_basis_signature,
            "source_applicability_matrix_hash": self.source_applicability_matrix_hash,
            "source_calculation_records_hash": self.source_calculation_records_hash,
            "source_non_conformance_hash": self.source_non_conformance_hash,
            "source_compliance_dossier_human_hash": self.source_compliance_dossier_human_hash,
            "source_compliance_dossier_machine_hash": self.source_compliance_dossier_machine_hash,
            "source_traceability_graph_hash": self.source_traceability_graph_hash,
            "template_catalog_schema_version": self.template_catalog_schema_version,
            "signed_calculation_snapshot_set_schema_version": self.signed_calculation_snapshot_set_schema_version,
            "change_impact_report_schema_version": self.change_impact_report_schema_version,
            "inspector_workflow_schema_version": self.inspector_workflow_schema_version,
            "canonical_pdf_render_schema_version": self.canonical_pdf_render_schema_version,
            "reproducibility": self.reproducibility,
            "template_catalog": [template.to_json_dict() for template in self.template_catalog],
            "signed_calculation_snapshots": [snapshot.to_json_dict() for snapshot in self.signed_calculation_snapshots],
            "change_impact_report": self.change_impact_report,
            "inspector_regulator_workflow": [step.to_json_dict() for step in self.inspector_regulator_workflow],
            "workflow_signoff_transitions": [transition.to_json_dict() for transition in self.workflow_signoff_transitions],
            "pdf_payload": self.pdf_payload,
            "canonical_pdf_render": self.canonical_pdf_render,
            "package_artifact_refs": self.package_artifact_refs,
            "signing": self.signing,
            "deterministic_hash": self.deterministic_hash,
        }


def generate_certification_dossier_export(
    requirement_set: RequirementSet,
    design_basis: DesignBasis,
    applicability_matrix: ApplicabilityMatrix,
    calculation_records: CalculationRecordsArtifact,
    non_conformance_list: NonConformanceListArtifact,
    compliance_dossier_human: ComplianceDossierHuman,
    compliance_dossier_machine: ComplianceDossierMachine,
    traceability_graph_revision: TraceabilityGraphRevision,
    change_impact_report: ImpactReport,
    *,
    revision_id: str,
    previous_revision_id: str | None = None,
    now_utc: datetime | None = None,
) -> CertificationDossierExportPackage:
    """Build deterministic BL-007 dossier package with machine JSON and PDF payload route."""
    _validate_handoff_gate(
        requirement_set=requirement_set,
        design_basis=design_basis,
        applicability_matrix=applicability_matrix,
        calculation_records=calculation_records,
        non_conformance_list=non_conformance_list,
        compliance_dossier_human=compliance_dossier_human,
        compliance_dossier_machine=compliance_dossier_machine,
        traceability_graph_revision=traceability_graph_revision,
        change_impact_report=change_impact_report,
        revision_id=revision_id,
    )

    generated_at = (now_utc or datetime.now(tz=timezone.utc)).replace(microsecond=0).isoformat()

    template_catalog = _build_template_catalog()
    signed_snapshots = _build_signed_snapshot_refs(calculation_records)
    workflow = _build_inspector_workflow(
        compliance_dossier_machine_hash=compliance_dossier_machine.deterministic_hash,
        traceability_graph_hash=traceability_graph_revision.deterministic_hash,
        impact_report_hash=change_impact_report.deterministic_hash,
    )
    signoff_transitions = _build_workflow_signoff_transitions(
        compliance_dossier_machine_hash=compliance_dossier_machine.deterministic_hash,
        traceability_graph_hash=traceability_graph_revision.deterministic_hash,
        impact_report_hash=change_impact_report.deterministic_hash,
    )

    pdf_payload = {
        "schema_version": CERTIFICATION_DOSSIER_PDF_PAYLOAD_VERSION,
        "title": "BL-007 Certification Dossier",
        "revision_id": revision_id,
        "generated_at_utc": generated_at,
        "template_sections": [
            {
                "section_id": template.section_id,
                "title": template.title,
                "render_required": template.required,
                "source_refs": template.source_refs,
            }
            for template in template_catalog
        ],
        "summary_lines": [
            f"RequirementSet hash: {requirement_set.deterministic_hash}",
            f"Compliance dossier machine hash: {compliance_dossier_machine.deterministic_hash}",
            f"Traceability graph hash: {traceability_graph_revision.deterministic_hash}",
            f"Impact report hash: {change_impact_report.deterministic_hash}",
            f"Signed snapshots: {len(signed_snapshots)}",
        ],
    }
    canonical_pdf_render = render_canonical_dossier_pdf(
        pdf_payload,
        template_catalog=template_catalog,
        impact_report=change_impact_report,
        signoff_transitions=signoff_transitions,
    )

    package_artifact_refs = [
        f"{CERTIFICATION_DOSSIER_EXPORT_PACKAGE_VERSION}#<package_hash>",
        f"{CERTIFICATION_DOSSIER_PDF_PAYLOAD_VERSION}#{_sha256_payload(pdf_payload)}",
        f"{CANONICAL_DOSSIER_PDF_RENDER_VERSION}#{canonical_pdf_render['content_sha256']}",
        f"{COMPLIANCE_DOSSIER_MACHINE_VERSION}#{compliance_dossier_machine.deterministic_hash}",
        f"{TRACEABILITY_GRAPH_REVISION_VERSION}#{traceability_graph_revision.deterministic_hash}",
        f"{SIGNED_CALCULATION_SNAPSHOT_SET_VERSION}#{_sha256_payload([snapshot.to_json_dict() for snapshot in signed_snapshots])}",
        f"{IMPACT_REPORT_VERSION}#{change_impact_report.deterministic_hash}",
    ]

    payload = {
        "schema_version": CERTIFICATION_DOSSIER_EXPORT_PACKAGE_VERSION,
        "generated_at_utc": generated_at,
        "revision_id": revision_id,
        "previous_revision_id": previous_revision_id,
        "source_requirement_set_hash": requirement_set.deterministic_hash,
        "source_design_basis_signature": design_basis.deterministic_signature,
        "source_applicability_matrix_hash": applicability_matrix.deterministic_hash,
        "source_calculation_records_hash": calculation_records.deterministic_hash,
        "source_non_conformance_hash": non_conformance_list.deterministic_hash,
        "source_compliance_dossier_human_hash": compliance_dossier_human.deterministic_hash,
        "source_compliance_dossier_machine_hash": compliance_dossier_machine.deterministic_hash,
        "source_traceability_graph_hash": traceability_graph_revision.deterministic_hash,
        "template_catalog_schema_version": TEMPLATE_CATALOG_VERSION,
        "signed_calculation_snapshot_set_schema_version": SIGNED_CALCULATION_SNAPSHOT_SET_VERSION,
        "change_impact_report_schema_version": IMPACT_REPORT_VERSION,
        "inspector_workflow_schema_version": INSPECTOR_WORKFLOW_VERSION,
        "canonical_pdf_render_schema_version": CANONICAL_DOSSIER_PDF_RENDER_VERSION,
        "reproducibility": {"canonicalization": "json.sort_keys+compact", "hash_algorithm": "sha256"},
        "template_catalog": [template.to_json_dict() for template in template_catalog],
        "signed_calculation_snapshots": [snapshot.to_json_dict() for snapshot in signed_snapshots],
        "change_impact_report": change_impact_report.to_json_dict(),
        "inspector_regulator_workflow": [step.to_json_dict() for step in workflow],
        "workflow_signoff_transitions": [transition.to_json_dict() for transition in signoff_transitions],
        "pdf_payload": pdf_payload,
        "canonical_pdf_render": canonical_pdf_render,
        "package_artifact_refs": package_artifact_refs,
    }
    deterministic_hash = _sha256_payload(payload)
    signing = {
        "algorithm": "sha256",
        "signing_key_ref": "dossier-export::bl-037",
        "signature": _sign_payload(
            "dossier-export::bl-037",
            {
                "revision_id": revision_id,
                "source_requirement_set_hash": requirement_set.deterministic_hash,
                "source_compliance_dossier_machine_hash": compliance_dossier_machine.deterministic_hash,
                "source_traceability_graph_hash": traceability_graph_revision.deterministic_hash,
                "canonical_pdf_render_sha256": canonical_pdf_render["content_sha256"],
                "change_impact_report_signature": change_impact_report.signing["signature"],
                "package_unsigned_payload_sha256": deterministic_hash,
            },
        ),
    }

    finalized_refs = [
        ref.replace("#<package_hash>", f"#{deterministic_hash}") if "<package_hash>" in ref else ref
        for ref in package_artifact_refs
    ]

    return CertificationDossierExportPackage(
        schema_version=CERTIFICATION_DOSSIER_EXPORT_PACKAGE_VERSION,
        generated_at_utc=generated_at,
        revision_id=revision_id,
        previous_revision_id=previous_revision_id,
        source_requirement_set_hash=requirement_set.deterministic_hash,
        source_design_basis_signature=design_basis.deterministic_signature,
        source_applicability_matrix_hash=applicability_matrix.deterministic_hash,
        source_calculation_records_hash=calculation_records.deterministic_hash,
        source_non_conformance_hash=non_conformance_list.deterministic_hash,
        source_compliance_dossier_human_hash=compliance_dossier_human.deterministic_hash,
        source_compliance_dossier_machine_hash=compliance_dossier_machine.deterministic_hash,
        source_traceability_graph_hash=traceability_graph_revision.deterministic_hash,
        template_catalog_schema_version=TEMPLATE_CATALOG_VERSION,
        signed_calculation_snapshot_set_schema_version=SIGNED_CALCULATION_SNAPSHOT_SET_VERSION,
        change_impact_report_schema_version=IMPACT_REPORT_VERSION,
        inspector_workflow_schema_version=INSPECTOR_WORKFLOW_VERSION,
        canonical_pdf_render_schema_version=CANONICAL_DOSSIER_PDF_RENDER_VERSION,
        reproducibility=payload["reproducibility"],
        template_catalog=template_catalog,
        signed_calculation_snapshots=signed_snapshots,
        change_impact_report=change_impact_report.to_json_dict(),
        inspector_regulator_workflow=workflow,
        workflow_signoff_transitions=signoff_transitions,
        pdf_payload=pdf_payload,
        canonical_pdf_render=canonical_pdf_render,
        package_artifact_refs=finalized_refs,
        signing=signing,
        deterministic_hash=deterministic_hash,
    )


def write_certification_dossier_export(
    export_package: CertificationDossierExportPackage,
    directory: str | Path,
    *,
    filename_prefix: str = "",
) -> tuple[Path, Path, Path]:
    """Persist BL-007 package JSON and PDF payload JSON in canonical form."""
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)

    package_path = target / f"{filename_prefix}{CERTIFICATION_DOSSIER_EXPORT_PACKAGE_VERSION}.json"
    pdf_payload_path = target / f"{filename_prefix}{CERTIFICATION_DOSSIER_PDF_PAYLOAD_VERSION}.json"
    canonical_pdf_render_path = target / f"{filename_prefix}{CANONICAL_DOSSIER_PDF_RENDER_VERSION}.pdf"

    package_path.write_text(json.dumps(export_package.to_json_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pdf_payload_path.write_text(json.dumps(export_package.pdf_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    canonical_pdf_render_path.write_text(export_package.canonical_pdf_render["content"], encoding="utf-8")

    return package_path, pdf_payload_path, canonical_pdf_render_path


def _build_template_catalog() -> list[ReportSectionTemplate]:
    return [
        ReportSectionTemplate(
            section_id="SEC-001",
            title="Compliance summary",
            required=True,
            source_refs=[COMPLIANCE_DOSSIER_HUMAN_VERSION, COMPLIANCE_DOSSIER_MACHINE_VERSION],
        ),
        ReportSectionTemplate(
            section_id="SEC-002",
            title="Clause matrix and evidence trace",
            required=True,
            source_refs=[COMPLIANCE_DOSSIER_MACHINE_VERSION],
        ),
        ReportSectionTemplate(
            section_id="SEC-003",
            title="Signed calculation snapshots",
            required=True,
            source_refs=[CALCULATION_RECORDS_VERSION, SIGNED_CALCULATION_SNAPSHOT_SET_VERSION],
        ),
        ReportSectionTemplate(
            section_id="SEC-004",
            title="Change impact report",
            required=True,
            source_refs=[IMPACT_REPORT_VERSION],
        ),
        ReportSectionTemplate(
            section_id="SEC-005",
            title="Inspector/regulator workflow",
            required=True,
            source_refs=[INSPECTOR_WORKFLOW_VERSION, TRACEABILITY_GRAPH_REVISION_VERSION],
        ),
    ]


def _build_signed_snapshot_refs(
    calculation_records: CalculationRecordsArtifact,
) -> list[SignedCalculationSnapshotRef]:
    snapshots = [
        SignedCalculationSnapshotRef(
            check_id=check.check_id,
            clause_id=check.clause_id,
            artifact_ref=f"{CALCULATION_RECORDS_VERSION}#{calculation_records.deterministic_hash}:{check.check_id}",
            canonical_payload_sha256=check.reproducibility.canonical_payload_sha256,
            signature_ref=f"sha256:{check.reproducibility.canonical_payload_sha256}",
        )
        for check in sorted(calculation_records.checks, key=lambda item: item.check_id)
    ]
    return snapshots


def _build_inspector_workflow(
    *,
    compliance_dossier_machine_hash: str,
    traceability_graph_hash: str,
    impact_report_hash: str,
) -> list[InspectorWorkflowStep]:
    return [
        InspectorWorkflowStep(
            step_id="WF-001",
            role="design_authority",
            prompt="Assemble dossier package and verify hashes before external review.",
            required_artifact_refs=[
                f"{COMPLIANCE_DOSSIER_MACHINE_VERSION}#{compliance_dossier_machine_hash}",
                f"{IMPACT_REPORT_VERSION}#{impact_report_hash}",
            ],
            status="pending",
        ),
        InspectorWorkflowStep(
            step_id="WF-002",
            role="authorized_inspector",
            prompt="Review signed calculation snapshots and clause-level evidence coverage.",
            required_artifact_refs=[
                SIGNED_CALCULATION_SNAPSHOT_SET_VERSION,
                f"{TRACEABILITY_GRAPH_REVISION_VERSION}#{traceability_graph_hash}",
                f"{IMPACT_REPORT_VERSION}#{impact_report_hash}",
            ],
            status="pending",
        ),
        InspectorWorkflowStep(
            step_id="WF-003",
            role="regulator",
            prompt="Approve or reject dossier package for certification release.",
            required_artifact_refs=[
                CERTIFICATION_DOSSIER_EXPORT_PACKAGE_VERSION,
                CERTIFICATION_DOSSIER_PDF_PAYLOAD_VERSION,
            ],
            status="pending",
        ),
    ]


def _build_workflow_signoff_transitions(
    *,
    compliance_dossier_machine_hash: str,
    traceability_graph_hash: str,
    impact_report_hash: str,
) -> list[WorkflowSignoffTransition]:
    return [
        WorkflowSignoffTransition(
            transition_id="WF-T001",
            from_step_id="WF-001",
            to_step_id="WF-002",
            trigger="design_authority_submit",
            required_evidence_refs=[
                f"{COMPLIANCE_DOSSIER_MACHINE_VERSION}#{compliance_dossier_machine_hash}",
                f"{IMPACT_REPORT_VERSION}#{impact_report_hash}",
            ],
            state="pending",
        ),
        WorkflowSignoffTransition(
            transition_id="WF-T002",
            from_step_id="WF-002",
            to_step_id="WF-003",
            trigger="inspector_signoff",
            required_evidence_refs=[
                f"{TRACEABILITY_GRAPH_REVISION_VERSION}#{traceability_graph_hash}",
                SIGNED_CALCULATION_SNAPSHOT_SET_VERSION,
            ],
            state="pending",
        ),
        WorkflowSignoffTransition(
            transition_id="WF-T003",
            from_step_id="WF-003",
            to_step_id="WF-003",
            trigger="regulator_disposition",
            required_evidence_refs=[
                CERTIFICATION_DOSSIER_EXPORT_PACKAGE_VERSION,
                CERTIFICATION_DOSSIER_PDF_PAYLOAD_VERSION,
                CANONICAL_DOSSIER_PDF_RENDER_VERSION,
            ],
            state="awaiting_decision",
        ),
    ]


def render_canonical_dossier_pdf(
    pdf_payload: dict[str, Any],
    *,
    template_catalog: list[ReportSectionTemplate],
    impact_report: ImpactReport,
    signoff_transitions: list[WorkflowSignoffTransition],
) -> dict[str, Any]:
    """Render deterministic canonical dossier PDF content from template-driven payloads."""
    content = _render_canonical_dossier_pdf_content(
        pdf_payload=pdf_payload,
        template_catalog=template_catalog,
        impact_report_hash=impact_report.deterministic_hash,
        signoff_transitions=signoff_transitions,
    )
    return {
        "schema_version": CANONICAL_DOSSIER_PDF_RENDER_VERSION,
        "renderer": "deterministic-template-renderer",
        "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "content": content,
    }


def verify_deterministic_pdf_render(export_package: CertificationDossierExportPackage) -> None:
    """Fail closed if canonical PDF render cannot be deterministically regenerated."""
    canonical_pdf_render = export_package.canonical_pdf_render
    actual_sha = hashlib.sha256(canonical_pdf_render["content"].encode("utf-8")).hexdigest()
    if canonical_pdf_render["content_sha256"] != actual_sha:
        raise ValueError("BL-037 PDF verification failed: canonical PDF content hash mismatch.")
    if canonical_pdf_render.get("schema_version") != CANONICAL_DOSSIER_PDF_RENDER_VERSION:
        raise ValueError("BL-037 PDF verification failed: unsupported canonical PDF schema version.")

    regenerated = _render_canonical_dossier_pdf_content(
        pdf_payload=export_package.pdf_payload,
        template_catalog=[
            ReportSectionTemplate(
                section_id=entry["section_id"],
                title=entry["title"],
                required=entry["required"],
                source_refs=entry["source_refs"],
            )
            for entry in export_package.to_json_dict()["template_catalog"]
        ],
        impact_report_hash=export_package.change_impact_report["deterministic_hash"],
        signoff_transitions=[
            WorkflowSignoffTransition(
                transition_id=transition["transition_id"],
                from_step_id=transition["from_step_id"],
                to_step_id=transition["to_step_id"],
                trigger=transition["trigger"],
                required_evidence_refs=transition["required_evidence_refs"],
                state=transition["state"],
            )
            for transition in export_package.to_json_dict()["workflow_signoff_transitions"]
        ],
    )
    if canonical_pdf_render["content"] != regenerated:
        raise ValueError("BL-037 PDF verification failed: canonical PDF render is not deterministic.")


def verify_dossier_export_signatures(export_package: CertificationDossierExportPackage) -> None:
    """Validate dossier and embedded change-impact signatures (BL-037 fail-closed gate)."""
    verify_deterministic_pdf_render(export_package)
    _verify_change_impact_signature(export_package.change_impact_report)
    _verify_dossier_signature(export_package)


def _render_canonical_dossier_pdf_content(
    *,
    pdf_payload: dict[str, Any],
    template_catalog: list[ReportSectionTemplate],
    impact_report_hash: str,
    signoff_transitions: list[WorkflowSignoffTransition],
) -> str:
    section_lines = [f"{section.section_id}|{section.title}" for section in template_catalog if section.required]
    transition_lines = [
        f"{transition.transition_id}|{transition.from_step_id}>{transition.to_step_id}|{transition.trigger}"
        for transition in signoff_transitions
    ]
    lines = [
        "%PDF-1.4",
        f"schema={CANONICAL_DOSSIER_PDF_RENDER_VERSION}",
        f"title={pdf_payload['title']}",
        f"revision_id={pdf_payload['revision_id']}",
        f"generated_at_utc={pdf_payload['generated_at_utc']}",
        f"impact_report_hash={impact_report_hash}",
        "sections=" + ";".join(section_lines),
        "workflow_transitions=" + ";".join(transition_lines),
        "%%EOF",
    ]
    return "\n".join(lines) + "\n"


def _validate_handoff_gate(
    *,
    requirement_set: RequirementSet,
    design_basis: DesignBasis,
    applicability_matrix: ApplicabilityMatrix,
    calculation_records: CalculationRecordsArtifact,
    non_conformance_list: NonConformanceListArtifact,
    compliance_dossier_human: ComplianceDossierHuman,
    compliance_dossier_machine: ComplianceDossierMachine,
    traceability_graph_revision: TraceabilityGraphRevision,
    change_impact_report: ImpactReport,
    revision_id: str,
) -> None:
    if not revision_id.strip():
        raise ValueError("BL-007 export gate failed: revision_id must be non-empty.")
    if requirement_set.schema_version != REQUIREMENT_SET_VERSION:
        raise ValueError("BL-007 export gate failed: unsupported RequirementSet schema version.")
    if design_basis.schema_version != DESIGN_BASIS_VERSION:
        raise ValueError("BL-007 export gate failed: unsupported DesignBasis schema version.")
    if applicability_matrix.schema_version != APPLICABILITY_MATRIX_VERSION:
        raise ValueError("BL-007 export gate failed: unsupported ApplicabilityMatrix schema version.")
    if calculation_records.schema_version != CALCULATION_RECORDS_VERSION:
        raise ValueError("BL-007 export gate failed: unsupported CalculationRecords schema version.")
    if non_conformance_list.schema_version != NON_CONFORMANCE_LIST_VERSION:
        raise ValueError("BL-007 export gate failed: unsupported NonConformanceList schema version.")
    if compliance_dossier_human.schema_version != COMPLIANCE_DOSSIER_HUMAN_VERSION:
        raise ValueError("BL-007 export gate failed: unsupported ComplianceDossierHuman schema version.")
    if compliance_dossier_machine.schema_version != COMPLIANCE_DOSSIER_MACHINE_VERSION:
        raise ValueError("BL-007 export gate failed: unsupported ComplianceDossierMachine schema version.")
    if traceability_graph_revision.schema_version != TRACEABILITY_GRAPH_REVISION_VERSION:
        raise ValueError("BL-007 export gate failed: unsupported TraceabilityGraphRevision schema version.")

    if design_basis.source_requirement_set_hash != requirement_set.deterministic_hash:
        raise ValueError("BL-007 export gate failed: design basis hash mismatch.")
    if applicability_matrix.source_requirement_set_hash != requirement_set.deterministic_hash:
        raise ValueError("BL-007 export gate failed: applicability matrix hash mismatch.")
    if calculation_records.source_requirement_set_hash != requirement_set.deterministic_hash:
        raise ValueError("BL-007 export gate failed: calculation records requirement hash mismatch.")
    if non_conformance_list.source_calculation_records_hash != calculation_records.deterministic_hash:
        raise ValueError("BL-007 export gate failed: non-conformance list hash mismatch.")
    if compliance_dossier_human.source_requirement_set_hash != requirement_set.deterministic_hash:
        raise ValueError("BL-007 export gate failed: human dossier requirement hash mismatch.")
    if compliance_dossier_machine.source_requirement_set_hash != requirement_set.deterministic_hash:
        raise ValueError("BL-007 export gate failed: machine dossier requirement hash mismatch.")
    if compliance_dossier_machine.source_calculation_records_hash != calculation_records.deterministic_hash:
        raise ValueError("BL-007 export gate failed: machine dossier calculation hash mismatch.")
    if traceability_graph_revision.source_compliance_dossier_hash != compliance_dossier_machine.deterministic_hash:
        raise ValueError("BL-007 export gate failed: traceability graph compliance hash mismatch.")
    if change_impact_report.schema_version != IMPACT_REPORT_VERSION:
        raise ValueError("BL-007 export gate failed: unsupported ImpactReport schema version.")
    if change_impact_report.to_revision_id != revision_id:
        raise ValueError("BL-007 export gate failed: impact report revision mismatch.")


def _sha256_payload(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _sign_payload(signing_key_ref: str, payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    raw = f"{signing_key_ref}:{canonical}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _verify_change_impact_signature(change_impact_report: dict[str, Any]) -> None:
    signing = change_impact_report.get("signing", {})
    signing_key_ref = signing.get("signing_key_ref")
    signature = signing.get("signature")
    if not signing_key_ref or not signature:
        raise ValueError("BL-037 signature verification failed: change-impact signature is missing.")
    expected_signature = _sign_payload(
        signing_key_ref,
        {
            "to_revision_id": change_impact_report["to_revision_id"],
            "revision_delta": change_impact_report["revision_delta"],
            "minimal_reverification_check_ids": change_impact_report["minimal_reverification_check_ids"],
            "evidence_links": change_impact_report["evidence_links"],
        },
    )
    if signature != expected_signature:
        raise ValueError("BL-037 signature verification failed: change-impact signature mismatch.")


def _verify_dossier_signature(export_package: CertificationDossierExportPackage) -> None:
    signing = export_package.signing
    signing_key_ref = signing.get("signing_key_ref")
    signature = signing.get("signature")
    if not signing_key_ref or not signature:
        raise ValueError("BL-037 signature verification failed: dossier signature is missing.")
    expected_signature = _sign_payload(
        signing_key_ref,
        {
            "revision_id": export_package.revision_id,
            "source_requirement_set_hash": export_package.source_requirement_set_hash,
            "source_compliance_dossier_machine_hash": export_package.source_compliance_dossier_machine_hash,
            "source_traceability_graph_hash": export_package.source_traceability_graph_hash,
            "canonical_pdf_render_sha256": export_package.canonical_pdf_render["content_sha256"],
            "change_impact_report_signature": export_package.change_impact_report["signing"]["signature"],
            "package_unsigned_payload_sha256": export_package.deterministic_hash,
        },
    )
    if signature != expected_signature:
        raise ValueError("BL-037 signature verification failed: dossier signature mismatch.")
