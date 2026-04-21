"""Deterministic traceability graph schema and audit helpers for BL-006."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from .compliance_pipeline import ComplianceDossierMachine
from .design_basis_pipeline import ApplicabilityMatrix, DesignBasis
from .requirements_pipeline import RequirementSet

TRACEABILITY_GRAPH_REVISION_VERSION = "TraceabilityGraphRevision.v1"
AUDIT_REPORT_TEMPLATE_VERSION = "TraceabilityAuditReportTemplate.v1"
_LINK_ENDPOINT_KINDS = {"requirement", "clause", "model", "calculation", "artifact", "approval"}


@dataclass(frozen=True)
class ApprovalRecord:
    approval_id: str
    approver_role: str
    status: str
    artifact_ref: str
    note: str = ""

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TraceabilityLink:
    link_id: str
    source_kind: str
    source_ref: str
    target_kind: str
    target_ref: str
    relation: str
    clause_id: str | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TraceabilityGraphRevision:
    schema_version: str
    generated_at_utc: str
    revision_id: str
    previous_revision_id: str | None
    immutable: bool
    source_requirement_set_hash: str
    source_design_basis_signature: str
    source_applicability_matrix_hash: str
    source_compliance_dossier_hash: str
    links: list[TraceabilityLink]
    deterministic_hash: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at_utc": self.generated_at_utc,
            "revision_id": self.revision_id,
            "previous_revision_id": self.previous_revision_id,
            "immutable": self.immutable,
            "source_requirement_set_hash": self.source_requirement_set_hash,
            "source_design_basis_signature": self.source_design_basis_signature,
            "source_applicability_matrix_hash": self.source_applicability_matrix_hash,
            "source_compliance_dossier_hash": self.source_compliance_dossier_hash,
            "links": [link.to_json_dict() for link in self.links],
            "deterministic_hash": self.deterministic_hash,
        }


class Neo4jTraceabilityStoreBackend:
    """Deterministic in-memory stand-in for Neo4j revisioned graph writes."""

    def __init__(self) -> None:
        self._revisions: dict[str, TraceabilityGraphRevision] = {}

    def write_revision(self, revision: TraceabilityGraphRevision) -> None:
        if revision.revision_id in self._revisions:
            raise ValueError(
                f"BL-035 neo4j write failed: immutable revision '{revision.revision_id}' already exists."
            )
        self._revisions[revision.revision_id] = revision

    def read_revision(self, revision_id: str) -> TraceabilityGraphRevision:
        try:
            return self._revisions[revision_id]
        except KeyError as error:
            raise ValueError(
                f"BL-035 neo4j read failed: revision '{revision_id}' not found."
            ) from error

    def read_all(self) -> list[TraceabilityGraphRevision]:
        return [self._revisions[key] for key in sorted(self._revisions.keys())]


class Neo4jTraceabilityStore:
    """Neo4j-facing repository wrapper with deterministic read/query helpers."""

    def __init__(self, backend: Neo4jTraceabilityStoreBackend) -> None:
        self._backend = backend

    def persist_revision(self, graph_revision: TraceabilityGraphRevision) -> None:
        self._backend.write_revision(graph_revision)

    def get_revision(self, revision_id: str) -> TraceabilityGraphRevision:
        return self._backend.read_revision(revision_id)

    def query_clause_links(
        self,
        *,
        clause_id: str,
        revision_id: str | None = None,
    ) -> list[TraceabilityLink]:
        return query_clause_evidence(self._backend.read_all(), clause_id, revision_id=revision_id)


def build_traceability_graph_revision(
    requirement_set: RequirementSet,
    design_basis: DesignBasis,
    applicability_matrix: ApplicabilityMatrix,
    compliance_dossier: ComplianceDossierMachine,
    *,
    revision_id: str,
    approvals: list[ApprovalRecord] | None = None,
    previous_revision_id: str | None = None,
    now_utc: datetime | None = None,
) -> TraceabilityGraphRevision:
    """Build a deterministic traceability graph snapshot for a project revision."""
    if not revision_id.strip():
        raise ValueError("BL-006 graph build failed: revision_id must be non-empty.")
    if compliance_dossier.source_requirement_set_hash != requirement_set.deterministic_hash:
        raise ValueError("BL-006 graph build failed: requirement hash mismatch.")
    if compliance_dossier.source_design_basis_signature != design_basis.deterministic_signature:
        raise ValueError("BL-006 graph build failed: design basis signature mismatch.")
    if compliance_dossier.source_applicability_matrix_hash != applicability_matrix.deterministic_hash:
        raise ValueError("BL-006 graph build failed: applicability matrix hash mismatch.")

    generated_at = (now_utc or datetime.now(tz=timezone.utc)).replace(microsecond=0).isoformat()
    links = _build_links(compliance_dossier, approvals or [])

    payload = {
        "schema_version": TRACEABILITY_GRAPH_REVISION_VERSION,
        "generated_at_utc": generated_at,
        "revision_id": revision_id,
        "previous_revision_id": previous_revision_id,
        "immutable": True,
        "source_requirement_set_hash": requirement_set.deterministic_hash,
        "source_design_basis_signature": design_basis.deterministic_signature,
        "source_applicability_matrix_hash": applicability_matrix.deterministic_hash,
        "source_compliance_dossier_hash": compliance_dossier.deterministic_hash,
        "links": [link.to_json_dict() for link in links],
    }

    return TraceabilityGraphRevision(
        schema_version=TRACEABILITY_GRAPH_REVISION_VERSION,
        generated_at_utc=generated_at,
        revision_id=revision_id,
        previous_revision_id=previous_revision_id,
        immutable=True,
        source_requirement_set_hash=requirement_set.deterministic_hash,
        source_design_basis_signature=design_basis.deterministic_signature,
        source_applicability_matrix_hash=applicability_matrix.deterministic_hash,
        source_compliance_dossier_hash=compliance_dossier.deterministic_hash,
        links=links,
        deterministic_hash=_sha256_payload(payload),
    )


def with_additional_links(
    graph_revision: TraceabilityGraphRevision,
    additional_links: list[TraceabilityLink],
    *,
    allow_mutation: bool = False,
) -> TraceabilityGraphRevision:
    """Return a graph revision with extra links; immutable revisions reject mutation by default."""
    if graph_revision.immutable and not allow_mutation:
        raise ValueError("BL-006 graph mutation blocked: revision is immutable.")
    merged = sorted(
        [*graph_revision.links, *additional_links],
        key=lambda link: (
            link.link_id,
            link.source_kind,
            link.source_ref,
            link.target_kind,
            link.target_ref,
            link.relation,
            link.clause_id or "",
        ),
    )
    payload = graph_revision.to_json_dict()
    payload["links"] = [link.to_json_dict() for link in merged]
    payload.pop("deterministic_hash", None)
    deterministic_hash = _sha256_payload(payload)
    return TraceabilityGraphRevision(
        schema_version=graph_revision.schema_version,
        generated_at_utc=graph_revision.generated_at_utc,
        revision_id=graph_revision.revision_id,
        previous_revision_id=graph_revision.previous_revision_id,
        immutable=graph_revision.immutable,
        source_requirement_set_hash=graph_revision.source_requirement_set_hash,
        source_design_basis_signature=graph_revision.source_design_basis_signature,
        source_applicability_matrix_hash=graph_revision.source_applicability_matrix_hash,
        source_compliance_dossier_hash=graph_revision.source_compliance_dossier_hash,
        links=merged,
        deterministic_hash=deterministic_hash,
    )


def query_graph_by_revision(
    graph_revisions: Iterable[TraceabilityGraphRevision],
    revision_id: str,
) -> TraceabilityGraphRevision:
    """Return the graph snapshot for a specific revision."""
    for revision in graph_revisions:
        if revision.revision_id == revision_id:
            return revision
    raise ValueError(f"BL-006 revision query failed: revision '{revision_id}' not found.")


def query_clause_evidence(
    graph_revisions: Iterable[TraceabilityGraphRevision],
    clause_id: str,
    *,
    revision_id: str | None = None,
) -> list[TraceabilityLink]:
    """Return links bound to a clause, optionally scoped to one revision."""
    if not clause_id.strip():
        raise ValueError("BL-006 clause query failed: clause_id must be non-empty.")

    revisions = list(graph_revisions)
    if revision_id is not None:
        revisions = [query_graph_by_revision(revisions, revision_id)]

    result: list[TraceabilityLink] = []
    for revision in revisions:
        for link in revision.links:
            if link.clause_id == clause_id or (
                link.source_kind == "clause" and link.source_ref == clause_id
            ) or (
                link.target_kind == "clause" and link.target_ref == clause_id
            ):
                result.append(link)
    return sorted(
        result,
        key=lambda link: (
            link.link_id,
            link.source_kind,
            link.source_ref,
            link.target_kind,
            link.target_ref,
            link.relation,
        ),
    )


def build_audit_report_template(
    graph_revision: TraceabilityGraphRevision,
    *,
    clause_id: str | None = None,
) -> dict[str, Any]:
    """Build deterministic audit report template payload for a revision and optional clause focus."""
    scoped_links = graph_revision.links
    if clause_id is not None:
        scoped_links = query_clause_evidence([graph_revision], clause_id, revision_id=graph_revision.revision_id)

    return {
        "schema_version": AUDIT_REPORT_TEMPLATE_VERSION,
        "revision_id": graph_revision.revision_id,
        "clause_scope": clause_id,
        "summary_lines": [
            f"Revision: {graph_revision.revision_id}",
            f"Immutable: {str(graph_revision.immutable).lower()}",
            f"Traceability links: {len(scoped_links)}",
        ],
        "evidence_rows": [
            {
                "link_id": link.link_id,
                "source": f"{link.source_kind}:{link.source_ref}",
                "relation": link.relation,
                "target": f"{link.target_kind}:{link.target_ref}",
                "clause_id": link.clause_id or "-",
            }
            for link in scoped_links
        ],
    }


def write_traceability_graph_revision(graph_revision: TraceabilityGraphRevision, directory: str | Path) -> Path:
    """Persist immutable, revisioned graph snapshot; fail if revision path already exists."""
    output_dir = Path(directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{graph_revision.revision_id}.traceability_graph.json"
    payload = json.dumps(graph_revision.to_json_dict(), indent=2, sort_keys=True)
    with output_path.open("x", encoding="utf-8") as handle:
        handle.write(payload)
        handle.write("\n")
    return output_path


def _build_links(compliance_dossier: ComplianceDossierMachine, approvals: list[ApprovalRecord]) -> list[TraceabilityLink]:
    links: list[TraceabilityLink] = []
    for evidence in compliance_dossier.evidence_links:
        if evidence.clause_id:
            links.append(
                TraceabilityLink(
                    link_id=f"{evidence.requirement_field}:{evidence.clause_id}:req-clause",
                    source_kind="requirement",
                    source_ref=evidence.requirement_field,
                    target_kind="clause",
                    target_ref=evidence.clause_id,
                    relation="satisfies",
                    clause_id=evidence.clause_id,
                )
            )
            links.append(
                TraceabilityLink(
                    link_id=f"{evidence.clause_id}:{evidence.model_id}:clause-model",
                    source_kind="clause",
                    source_ref=evidence.clause_id,
                    target_kind="model",
                    target_ref=evidence.model_id,
                    relation="implemented_by",
                    clause_id=evidence.clause_id,
                )
            )

        links.append(
            TraceabilityLink(
                link_id=f"{evidence.model_id}:{evidence.result_id}:model-calc",
                source_kind="model",
                source_ref=evidence.model_id,
                target_kind="calculation",
                target_ref=evidence.result_id,
                relation="produces",
                clause_id=evidence.clause_id,
            )
        )
        links.append(
            TraceabilityLink(
                link_id=f"{evidence.result_id}:{evidence.artifact_ref}:calc-artifact",
                source_kind="calculation",
                source_ref=evidence.result_id,
                target_kind="artifact",
                target_ref=evidence.artifact_ref,
                relation="recorded_in",
                clause_id=evidence.clause_id,
            )
        )

    for approval in approvals:
        links.append(
            TraceabilityLink(
                link_id=f"{approval.artifact_ref}:{approval.approval_id}:artifact-approval",
                source_kind="artifact",
                source_ref=approval.artifact_ref,
                target_kind="approval",
                target_ref=approval.approval_id,
                relation=f"approved_by:{approval.approver_role}:{approval.status}",
                clause_id=None,
            )
        )

    _validate_link_endpoints(links)

    unique_links: dict[tuple[str, str, str, str, str, str, str | None], TraceabilityLink] = {}
    for link in links:
        key = (
            link.link_id,
            link.source_kind,
            link.source_ref,
            link.target_kind,
            link.target_ref,
            link.relation,
            link.clause_id,
        )
        unique_links[key] = link

    return sorted(
        unique_links.values(),
        key=lambda link: (
            link.link_id,
            link.source_kind,
            link.source_ref,
            link.target_kind,
            link.target_ref,
            link.relation,
            link.clause_id or "",
        ),
    )


def _validate_link_endpoints(links: list[TraceabilityLink]) -> None:
    for link in links:
        if link.source_kind not in _LINK_ENDPOINT_KINDS:
            raise ValueError(f"BL-006 graph build failed: unsupported source kind '{link.source_kind}'.")
        if link.target_kind not in _LINK_ENDPOINT_KINDS:
            raise ValueError(f"BL-006 graph build failed: unsupported target kind '{link.target_kind}'.")
        if not link.source_ref.strip() or not link.target_ref.strip() or not link.relation.strip() or not link.link_id.strip():
            raise ValueError("BL-006 graph build failed: links must have non-empty IDs, endpoints, and relation.")


def _sha256_payload(payload: dict[str, Any]) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
