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
from .design_basis_pipeline import APPLICABILITY_MATRIX_VERSION, DESIGN_BASIS_VERSION, ApplicabilityMatrix, DesignBasis
from .requirements_pipeline import REQUIREMENT_SET_VERSION, RequirementSet
from .traceability_pipeline import TRACEABILITY_GRAPH_REVISION_VERSION, TraceabilityGraphRevision

CERTIFICATION_DOSSIER_EXPORT_PACKAGE_VERSION = "CertificationDossierExportPackage.v1"
CERTIFICATION_DOSSIER_PDF_PAYLOAD_VERSION = "CertificationDossierPDFPayload.v1"
TEMPLATE_CATALOG_VERSION = "CertificationDossierTemplateCatalog.v1"
SIGNED_CALCULATION_SNAPSHOT_SET_VERSION = "SignedCalculationSnapshotSet.v1"
CHANGE_IMPACT_REPORT_PLACEHOLDER_VERSION = "ChangeImpactReport.v1.placeholder"
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
    reproducibility: dict[str, str]
    template_catalog: list[ReportSectionTemplate]
    signed_calculation_snapshots: list[SignedCalculationSnapshotRef]
    change_impact_report: dict[str, Any]
    inspector_regulator_workflow: list[InspectorWorkflowStep]
    pdf_payload: dict[str, Any]
    package_artifact_refs: list[str]
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
            "reproducibility": self.reproducibility,
            "template_catalog": [template.to_json_dict() for template in self.template_catalog],
            "signed_calculation_snapshots": [snapshot.to_json_dict() for snapshot in self.signed_calculation_snapshots],
            "change_impact_report": self.change_impact_report,
            "inspector_regulator_workflow": [step.to_json_dict() for step in self.inspector_regulator_workflow],
            "pdf_payload": self.pdf_payload,
            "package_artifact_refs": self.package_artifact_refs,
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
        revision_id=revision_id,
    )

    generated_at = (now_utc or datetime.now(tz=timezone.utc)).replace(microsecond=0).isoformat()

    template_catalog = _build_template_catalog()
    signed_snapshots = _build_signed_snapshot_refs(calculation_records)
    change_impact_report = _build_change_impact_report_placeholder(
        revision_id=revision_id,
        previous_revision_id=previous_revision_id,
        calculation_records=calculation_records,
    )
    workflow = _build_inspector_workflow(
        compliance_dossier_machine_hash=compliance_dossier_machine.deterministic_hash,
        traceability_graph_hash=traceability_graph_revision.deterministic_hash,
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
            f"Signed snapshots: {len(signed_snapshots)}",
        ],
    }

    package_artifact_refs = [
        f"{CERTIFICATION_DOSSIER_EXPORT_PACKAGE_VERSION}#<package_hash>",
        f"{CERTIFICATION_DOSSIER_PDF_PAYLOAD_VERSION}#{_sha256_payload(pdf_payload)}",
        f"{COMPLIANCE_DOSSIER_MACHINE_VERSION}#{compliance_dossier_machine.deterministic_hash}",
        f"{TRACEABILITY_GRAPH_REVISION_VERSION}#{traceability_graph_revision.deterministic_hash}",
        f"{SIGNED_CALCULATION_SNAPSHOT_SET_VERSION}#{_sha256_payload([snapshot.to_json_dict() for snapshot in signed_snapshots])}",
        f"{CHANGE_IMPACT_REPORT_PLACEHOLDER_VERSION}#{_sha256_payload(change_impact_report)}",
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
        "change_impact_report_schema_version": CHANGE_IMPACT_REPORT_PLACEHOLDER_VERSION,
        "inspector_workflow_schema_version": INSPECTOR_WORKFLOW_VERSION,
        "reproducibility": {"canonicalization": "json.sort_keys+compact", "hash_algorithm": "sha256"},
        "template_catalog": [template.to_json_dict() for template in template_catalog],
        "signed_calculation_snapshots": [snapshot.to_json_dict() for snapshot in signed_snapshots],
        "change_impact_report": change_impact_report,
        "inspector_regulator_workflow": [step.to_json_dict() for step in workflow],
        "pdf_payload": pdf_payload,
        "package_artifact_refs": package_artifact_refs,
    }
    deterministic_hash = _sha256_payload(payload)

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
        change_impact_report_schema_version=CHANGE_IMPACT_REPORT_PLACEHOLDER_VERSION,
        inspector_workflow_schema_version=INSPECTOR_WORKFLOW_VERSION,
        reproducibility=payload["reproducibility"],
        template_catalog=template_catalog,
        signed_calculation_snapshots=signed_snapshots,
        change_impact_report=change_impact_report,
        inspector_regulator_workflow=workflow,
        pdf_payload=pdf_payload,
        package_artifact_refs=finalized_refs,
        deterministic_hash=deterministic_hash,
    )


def write_certification_dossier_export(
    export_package: CertificationDossierExportPackage,
    directory: str | Path,
    *,
    filename_prefix: str = "",
) -> tuple[Path, Path]:
    """Persist BL-007 package JSON and PDF payload JSON in canonical form."""
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)

    package_path = target / f"{filename_prefix}{CERTIFICATION_DOSSIER_EXPORT_PACKAGE_VERSION}.json"
    pdf_payload_path = target / f"{filename_prefix}{CERTIFICATION_DOSSIER_PDF_PAYLOAD_VERSION}.json"

    package_path.write_text(json.dumps(export_package.to_json_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pdf_payload_path.write_text(json.dumps(export_package.pdf_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return package_path, pdf_payload_path


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
            source_refs=[CHANGE_IMPACT_REPORT_PLACEHOLDER_VERSION],
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


def _build_change_impact_report_placeholder(
    *,
    revision_id: str,
    previous_revision_id: str | None,
    calculation_records: CalculationRecordsArtifact,
) -> dict[str, Any]:
    impacted_clauses = sorted({check.clause_id for check in calculation_records.checks})
    return {
        "schema_version": CHANGE_IMPACT_REPORT_PLACEHOLDER_VERSION,
        "status": "pending_bl_008_integration",
        "revision_id": revision_id,
        "previous_revision_id": previous_revision_id,
        "summary_lines": [
            "Placeholder change impact section for BL-008 selective re-verification.",
            f"Detected impacted clauses from current snapshot: {', '.join(impacted_clauses)}",
        ],
        "impact_rows": [
            {
                "clause_id": clause_id,
                "impact_level": "to_be_computed",
                "rationale": "BL-008 will compute revision deltas and impacted evidence links.",
            }
            for clause_id in impacted_clauses
        ],
    }


def _build_inspector_workflow(*, compliance_dossier_machine_hash: str, traceability_graph_hash: str) -> list[InspectorWorkflowStep]:
    return [
        InspectorWorkflowStep(
            step_id="WF-001",
            role="design_authority",
            prompt="Assemble dossier package and verify hashes before external review.",
            required_artifact_refs=[
                f"{COMPLIANCE_DOSSIER_MACHINE_VERSION}#{compliance_dossier_machine_hash}",
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


def _sha256_payload(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
