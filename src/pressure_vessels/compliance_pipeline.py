"""Deterministic compliance dossier generation for BL-004."""

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
from .design_basis_pipeline import (
    APPLICABILITY_MATRIX_VERSION,
    DESIGN_BASIS_VERSION,
    ApplicabilityMatrix,
    DesignBasis,
)
from .requirements_pipeline import REQUIREMENT_SET_VERSION, RequirementSet

COMPLIANCE_MATRIX_VERSION = "ComplianceMatrix.v1"
EVIDENCE_LINK_SET_VERSION = "EvidenceLinkSet.v1"
REVIEW_CHECKLIST_VERSION = "ReviewChecklist.v1"
COMPLIANCE_DOSSIER_HUMAN_VERSION = "ComplianceDossierHuman.v1"
COMPLIANCE_DOSSIER_MACHINE_VERSION = "ComplianceDossierMachine.v1"


@dataclass(frozen=True)
class ClauseComplianceRecord:
    clause_id: str
    applicable: bool
    check_ids: list[str]
    status: str
    justification: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceLink:
    requirement_field: str
    clause_id: str
    model_id: str
    result_id: str
    artifact_ref: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewChecklistItem:
    item_id: str
    prompt: str
    required: bool
    evidence_refs: list[str]

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ComplianceDossierMachine:
    schema_version: str
    generated_at_utc: str
    source_requirement_set_hash: str
    source_design_basis_signature: str
    source_applicability_matrix_hash: str
    source_calculation_records_hash: str
    source_non_conformance_hash: str
    compliance_matrix_schema_version: str
    evidence_link_set_schema_version: str
    review_checklist_schema_version: str
    reproducibility: dict[str, str]
    compliance_matrix: list[ClauseComplianceRecord]
    evidence_links: list[EvidenceLink]
    review_checklist: list[ReviewChecklistItem]
    material_basis: dict[str, Any]
    geometry_basis: dict[str, Any]
    applied_defaults: dict[str, Any]
    cad_ready_parameter_export: dict[str, Any] | None
    deterministic_hash: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at_utc": self.generated_at_utc,
            "source_requirement_set_hash": self.source_requirement_set_hash,
            "source_design_basis_signature": self.source_design_basis_signature,
            "source_applicability_matrix_hash": self.source_applicability_matrix_hash,
            "source_calculation_records_hash": self.source_calculation_records_hash,
            "source_non_conformance_hash": self.source_non_conformance_hash,
            "compliance_matrix_schema_version": self.compliance_matrix_schema_version,
            "evidence_link_set_schema_version": self.evidence_link_set_schema_version,
            "review_checklist_schema_version": self.review_checklist_schema_version,
            "reproducibility": self.reproducibility,
            "compliance_matrix": [record.to_json_dict() for record in self.compliance_matrix],
            "evidence_links": [record.to_json_dict() for record in self.evidence_links],
            "review_checklist": [record.to_json_dict() for record in self.review_checklist],
            "material_basis": self.material_basis,
            "geometry_basis": self.geometry_basis,
            "applied_defaults": self.applied_defaults,
            "cad_ready_parameter_export": self.cad_ready_parameter_export,
            "deterministic_hash": self.deterministic_hash,
        }


@dataclass(frozen=True)
class ComplianceDossierHuman:
    schema_version: str
    generated_at_utc: str
    title: str
    source_requirement_set_hash: str
    source_design_basis_signature: str
    source_applicability_matrix_hash: str
    source_calculation_records_hash: str
    source_non_conformance_hash: str
    material_basis_ref: str
    geometry_basis_ref: str
    reproducibility: dict[str, str]
    summary_lines: list[str]
    clause_matrix_rows: list[dict[str, str]]
    evidence_trace_lines: list[str]
    review_checklist_lines: list[str]
    deterministic_hash: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at_utc": self.generated_at_utc,
            "title": self.title,
            "source_requirement_set_hash": self.source_requirement_set_hash,
            "source_design_basis_signature": self.source_design_basis_signature,
            "source_applicability_matrix_hash": self.source_applicability_matrix_hash,
            "source_calculation_records_hash": self.source_calculation_records_hash,
            "source_non_conformance_hash": self.source_non_conformance_hash,
            "material_basis_ref": self.material_basis_ref,
            "geometry_basis_ref": self.geometry_basis_ref,
            "reproducibility": self.reproducibility,
            "summary_lines": self.summary_lines,
            "clause_matrix_rows": self.clause_matrix_rows,
            "evidence_trace_lines": self.evidence_trace_lines,
            "review_checklist_lines": self.review_checklist_lines,
            "deterministic_hash": self.deterministic_hash,
        }


def generate_compliance_dossier(
    requirement_set: RequirementSet,
    design_basis: DesignBasis,
    applicability_matrix: ApplicabilityMatrix,
    calculation_records: CalculationRecordsArtifact,
    non_conformance_list: NonConformanceListArtifact,
    *,
    now_utc: datetime | None = None,
) -> tuple[ComplianceDossierHuman, ComplianceDossierMachine]:
    """Generate deterministic human and machine compliance dossier artifacts."""
    _validate_handoff_gate(
        requirement_set=requirement_set,
        design_basis=design_basis,
        applicability_matrix=applicability_matrix,
        calculation_records=calculation_records,
        non_conformance_list=non_conformance_list,
    )

    generated_at = (now_utc or datetime.now(tz=timezone.utc)).replace(microsecond=0).isoformat()

    clause_matrix = _build_clause_matrix(applicability_matrix, calculation_records)
    evidence_links = _build_evidence_links(requirement_set, applicability_matrix, calculation_records)
    checklist = _build_review_checklist(calculation_records)

    _validate_evidence_coverage(requirement_set, applicability_matrix, evidence_links)

    machine_payload = {
        "schema_version": COMPLIANCE_DOSSIER_MACHINE_VERSION,
        "generated_at_utc": generated_at,
        "source_requirement_set_hash": requirement_set.deterministic_hash,
        "source_design_basis_signature": design_basis.deterministic_signature,
        "source_applicability_matrix_hash": applicability_matrix.deterministic_hash,
        "source_calculation_records_hash": calculation_records.deterministic_hash,
        "source_non_conformance_hash": non_conformance_list.deterministic_hash,
        "compliance_matrix_schema_version": COMPLIANCE_MATRIX_VERSION,
        "evidence_link_set_schema_version": EVIDENCE_LINK_SET_VERSION,
        "review_checklist_schema_version": REVIEW_CHECKLIST_VERSION,
        "reproducibility": {"canonicalization": "json.sort_keys+compact", "hash_algorithm": "sha256"},
        "compliance_matrix": [record.to_json_dict() for record in clause_matrix],
        "evidence_links": [record.to_json_dict() for record in evidence_links],
        "review_checklist": [record.to_json_dict() for record in checklist],
        "material_basis": calculation_records.material_basis,
        "geometry_basis": calculation_records.geometry_basis,
        "applied_defaults": calculation_records.applied_defaults,
        "cad_ready_parameter_export": calculation_records.cad_ready_parameter_export,
    }
    machine_hash = _sha256_payload(machine_payload)

    machine_dossier = ComplianceDossierMachine(
        schema_version=COMPLIANCE_DOSSIER_MACHINE_VERSION,
        generated_at_utc=generated_at,
        source_requirement_set_hash=requirement_set.deterministic_hash,
        source_design_basis_signature=design_basis.deterministic_signature,
        source_applicability_matrix_hash=applicability_matrix.deterministic_hash,
        source_calculation_records_hash=calculation_records.deterministic_hash,
        source_non_conformance_hash=non_conformance_list.deterministic_hash,
        compliance_matrix_schema_version=COMPLIANCE_MATRIX_VERSION,
        evidence_link_set_schema_version=EVIDENCE_LINK_SET_VERSION,
        review_checklist_schema_version=REVIEW_CHECKLIST_VERSION,
        reproducibility=machine_payload["reproducibility"],
        compliance_matrix=clause_matrix,
        evidence_links=evidence_links,
        review_checklist=checklist,
        material_basis=calculation_records.material_basis,
        geometry_basis=calculation_records.geometry_basis,
        applied_defaults=calculation_records.applied_defaults,
        cad_ready_parameter_export=calculation_records.cad_ready_parameter_export,
        deterministic_hash=machine_hash,
    )

    passed = sum(1 for record in clause_matrix if record.status == "pass")
    failed = sum(1 for record in clause_matrix if record.status == "fail")
    not_applicable = sum(1 for record in clause_matrix if record.status == "not_applicable")
    not_evaluated = sum(1 for record in clause_matrix if record.status == "not_evaluated")

    human_payload = {
        "schema_version": COMPLIANCE_DOSSIER_HUMAN_VERSION,
        "generated_at_utc": generated_at,
        "title": "BL-004 Compliance Dossier",
        "source_requirement_set_hash": requirement_set.deterministic_hash,
        "source_design_basis_signature": design_basis.deterministic_signature,
        "source_applicability_matrix_hash": applicability_matrix.deterministic_hash,
        "source_calculation_records_hash": calculation_records.deterministic_hash,
        "source_non_conformance_hash": non_conformance_list.deterministic_hash,
        "material_basis_ref": (
            f"{calculation_records.material_basis['schema_version']}:"
            f"{calculation_records.material_basis['standards_package_ref']}:"
            f"{calculation_records.material_basis['standards_package_id']}:"
            f"{calculation_records.material_basis['effective_date']}:"
            f"{calculation_records.material_basis['allowables_version']}"
        ),
        "geometry_basis_ref": (
            f"{calculation_records.geometry_basis['source']}:"
            f"{calculation_records.geometry_basis.get('geometry_revision_id')}"
        ),
        "reproducibility": {"canonicalization": "json.sort_keys+compact", "hash_algorithm": "sha256"},
        "summary_lines": [
            f"Primary standard: {design_basis.primary_standard} ({design_basis.primary_standard_version})",
            (
                "Material basis: "
                f"{calculation_records.material_basis['material_spec']} "
                f"[{calculation_records.material_basis['allowables_version']}; "
                f"package={calculation_records.material_basis['standards_package_id']}; "
                f"effective={calculation_records.material_basis['effective_date']}]"
            ),
            (
                "Clause outcomes: "
                f"pass={passed}, fail={failed}, not_applicable={not_applicable}, not_evaluated={not_evaluated}"
            ),
        ],
        "clause_matrix_rows": [
            {
                "clause_id": row.clause_id,
                "status": row.status,
                "check_ids": ", ".join(row.check_ids) if row.check_ids else "-",
                "justification": row.justification,
            }
            for row in clause_matrix
        ],
        "evidence_trace_lines": [
            (
                f"{link.requirement_field} -> {link.clause_id} -> {link.model_id} -> "
                f"{link.result_id} -> {link.artifact_ref}"
            )
            for link in evidence_links
        ],
        "review_checklist_lines": [f"[{item.item_id}] {item.prompt}" for item in checklist],
    }
    human_hash = _sha256_payload(human_payload)

    human_dossier = ComplianceDossierHuman(
        schema_version=COMPLIANCE_DOSSIER_HUMAN_VERSION,
        generated_at_utc=generated_at,
        title="BL-004 Compliance Dossier",
        source_requirement_set_hash=requirement_set.deterministic_hash,
        source_design_basis_signature=design_basis.deterministic_signature,
        source_applicability_matrix_hash=applicability_matrix.deterministic_hash,
        source_calculation_records_hash=calculation_records.deterministic_hash,
        source_non_conformance_hash=non_conformance_list.deterministic_hash,
        material_basis_ref=human_payload["material_basis_ref"],
        geometry_basis_ref=human_payload["geometry_basis_ref"],
        reproducibility=human_payload["reproducibility"],
        summary_lines=human_payload["summary_lines"],
        clause_matrix_rows=human_payload["clause_matrix_rows"],
        evidence_trace_lines=human_payload["evidence_trace_lines"],
        review_checklist_lines=human_payload["review_checklist_lines"],
        deterministic_hash=human_hash,
    )

    return human_dossier, machine_dossier


def write_compliance_artifacts(
    human_dossier: ComplianceDossierHuman,
    machine_dossier: ComplianceDossierMachine,
    directory: str | Path,
    *,
    filename_prefix: str = "",
) -> tuple[Path, Path]:
    """Persist BL-004 artifacts to disk in canonical JSON form."""
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)

    human_path = target / f"{filename_prefix}{COMPLIANCE_DOSSIER_HUMAN_VERSION}.json"
    machine_path = target / f"{filename_prefix}{COMPLIANCE_DOSSIER_MACHINE_VERSION}.json"

    human_path.write_text(
        json.dumps(human_dossier.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    machine_path.write_text(
        json.dumps(machine_dossier.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return human_path, machine_path


def _validate_handoff_gate(
    requirement_set: RequirementSet,
    design_basis: DesignBasis,
    applicability_matrix: ApplicabilityMatrix,
    calculation_records: CalculationRecordsArtifact,
    non_conformance_list: NonConformanceListArtifact,
) -> None:
    if requirement_set.schema_version != REQUIREMENT_SET_VERSION:
        raise ValueError("BL-004 handoff gate failed: unsupported RequirementSet schema version.")
    if design_basis.schema_version != DESIGN_BASIS_VERSION:
        raise ValueError("BL-004 handoff gate failed: unsupported DesignBasis schema version.")
    if applicability_matrix.schema_version != APPLICABILITY_MATRIX_VERSION:
        raise ValueError("BL-004 handoff gate failed: unsupported ApplicabilityMatrix schema version.")
    if calculation_records.schema_version != CALCULATION_RECORDS_VERSION:
        raise ValueError("BL-004 handoff gate failed: unsupported CalculationRecords schema version.")
    if non_conformance_list.schema_version != NON_CONFORMANCE_LIST_VERSION:
        raise ValueError("BL-004 handoff gate failed: unsupported NonConformanceList schema version.")

    if requirement_set.downstream_blocked:
        raise ValueError("BL-004 handoff gate failed: requirement_set.downstream_blocked must be false.")
    if requirement_set.unresolved_gaps:
        raise ValueError("BL-004 handoff gate failed: requirement_set.unresolved_gaps must be empty.")

    if design_basis.source_requirement_set_hash != requirement_set.deterministic_hash:
        raise ValueError("BL-004 handoff gate failed: design_basis hash link mismatch.")
    if applicability_matrix.source_requirement_set_hash != requirement_set.deterministic_hash:
        raise ValueError("BL-004 handoff gate failed: applicability_matrix hash link mismatch.")
    if calculation_records.source_requirement_set_hash != requirement_set.deterministic_hash:
        raise ValueError("BL-004 handoff gate failed: calculation_records hash link mismatch.")
    if calculation_records.source_design_basis_signature != design_basis.deterministic_signature:
        raise ValueError("BL-004 handoff gate failed: calculation_records design_basis link mismatch.")
    if calculation_records.source_applicability_matrix_hash != applicability_matrix.deterministic_hash:
        raise ValueError(
            "BL-004 handoff gate failed: calculation_records applicability_matrix link mismatch."
        )
    if non_conformance_list.source_calculation_records_hash != calculation_records.deterministic_hash:
        raise ValueError("BL-004 handoff gate failed: non_conformance_list hash link mismatch.")

    known_clauses = {record.clause_id for record in applicability_matrix.records}
    for check in calculation_records.checks:
        if check.clause_id not in known_clauses:
            raise ValueError(
                f"BL-004 handoff gate failed: calculation check clause '{check.clause_id}' is unknown."
            )

    failed_checks = {check.check_id for check in calculation_records.checks if not check.pass_status}
    for entry in non_conformance_list.entries:
        if entry.check_id not in failed_checks:
            raise ValueError(
                "BL-004 handoff gate failed: non_conformance entry references non-failed or missing check."
            )


def _build_clause_matrix(
    applicability_matrix: ApplicabilityMatrix,
    calculation_records: CalculationRecordsArtifact,
) -> list[ClauseComplianceRecord]:
    checks_by_clause: dict[str, list[Any]] = {}
    for check in calculation_records.checks:
        checks_by_clause.setdefault(check.clause_id, []).append(check)

    matrix: list[ClauseComplianceRecord] = []
    for clause in applicability_matrix.records:
        clause_checks = sorted(
            checks_by_clause.get(clause.clause_id, []),
            key=lambda check: check.check_id,
        )
        status = _resolve_status(clause.applicable, clause_checks)
        matrix.append(
            ClauseComplianceRecord(
                clause_id=clause.clause_id,
                applicable=clause.applicable,
                check_ids=[check.check_id for check in clause_checks],
                status=status,
                justification=clause.justification,
            )
        )

    return matrix


def _resolve_status(applicable: bool, checks: list[Any]) -> str:
    if not applicable:
        return "not_applicable"
    if not checks:
        return "not_evaluated"
    if all(check.pass_status for check in checks):
        return "pass"
    return "fail"


def _build_evidence_links(
    requirement_set: RequirementSet,
    applicability_matrix: ApplicabilityMatrix,
    calculation_records: CalculationRecordsArtifact,
) -> list[EvidenceLink]:
    requirement_fields = set(requirement_set.requirements.keys())
    checks_by_clause: dict[str, list[Any]] = {}
    for check in calculation_records.checks:
        checks_by_clause.setdefault(check.clause_id, []).append(check)

    links: list[EvidenceLink] = []
    for clause in applicability_matrix.records:
        for field in sorted(clause.evidence_fields):
            if field not in requirement_fields:
                continue

            clause_checks = sorted(checks_by_clause.get(clause.clause_id, []), key=lambda check: check.check_id)
            if not clause_checks:
                links.append(
                    EvidenceLink(
                        requirement_field=field,
                        clause_id=clause.clause_id,
                        model_id="ApplicabilityModel.v1",
                        result_id=f"{clause.clause_id}:applicable={str(clause.applicable).lower()}",
                        artifact_ref=(
                            f"{APPLICABILITY_MATRIX_VERSION}#{applicability_matrix.deterministic_hash}:"
                            f"{clause.clause_id}"
                        ),
                    )
                )
                continue

            for check in clause_checks:
                links.append(
                    EvidenceLink(
                        requirement_field=field,
                        clause_id=clause.clause_id,
                        model_id=check.formula,
                        result_id=f"{check.check_id}:pass={str(check.pass_status).lower()}",
                        artifact_ref=(
                            f"{CALCULATION_RECORDS_VERSION}#{calculation_records.deterministic_hash}:"
                            f"{check.check_id}"
                        ),
                    )
                )

    links.sort(
        key=lambda link: (
            link.requirement_field,
            link.clause_id,
            link.model_id,
            link.result_id,
            link.artifact_ref,
        )
    )
    return links


def _validate_evidence_coverage(
    requirement_set: RequirementSet,
    applicability_matrix: ApplicabilityMatrix,
    evidence_links: list[EvidenceLink],
) -> None:
    present_requirements = set(requirement_set.requirements.keys())
    expected_pairs: set[tuple[str, str]] = set()
    applicable_clauses: set[str] = set()

    for clause in applicability_matrix.records:
        if clause.applicable:
            applicable_clauses.add(clause.clause_id)
        for field in clause.evidence_fields:
            if field in present_requirements:
                expected_pairs.add((field, clause.clause_id))

    linked_pairs = {(link.requirement_field, link.clause_id) for link in evidence_links}
    missing_pairs = sorted(expected_pairs - linked_pairs)
    if missing_pairs:
        raise ValueError(
            "BL-004 handoff gate failed: evidence links incomplete for expected requirement/clause pairs."
        )

    linked_clauses = {link.clause_id for link in evidence_links}
    uncovered_clauses = sorted(applicable_clauses - linked_clauses)
    if uncovered_clauses:
        raise ValueError(
            "BL-004 handoff gate failed: evidence links missing for applicable clause(s) "
            f"{', '.join(uncovered_clauses)}."
        )


def _build_review_checklist(
    calculation_records: CalculationRecordsArtifact,
) -> list[ReviewChecklistItem]:
    includes_defaults = bool(calculation_records.applied_defaults.get("applied_mvp_defaults"))

    return [
        ReviewChecklistItem(
            item_id="CHK-001",
            prompt="Confirm requirement-to-clause evidence links cover all applicable clauses.",
            required=True,
            evidence_refs=["evidence_links"],
        ),
        ReviewChecklistItem(
            item_id="CHK-002",
            prompt="Review all failed clause checks and verify non-conformance severity assignments.",
            required=True,
            evidence_refs=["compliance_matrix", "non_conformance_list"],
        ),
        ReviewChecklistItem(
            item_id="CHK-003",
            prompt="Confirm applied default assumptions are acceptable for release.",
            required=includes_defaults,
            evidence_refs=["applied_defaults"],
        ),
    ]


def _sha256_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
