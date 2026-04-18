"""Deterministic change-impact and selective re-verification pipeline for BL-008."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from .calculation_pipeline import CALCULATION_RECORDS_VERSION, CalculationRecord, CalculationRecordsArtifact
from .traceability_pipeline import TraceabilityGraphRevision, TraceabilityLink

IMPACT_REPORT_VERSION = "ImpactReport.v1"
BASELINE_UPDATE_STATUS_VERSION = "BaselineUpdateStatus.v1"
_REVISION_SNAPSHOT_VERSION = "RevisionTraceSnapshot.v1"


@dataclass(frozen=True)
class RevisionTraceSnapshot:
    schema_version: str
    revision_id: str
    previous_revision_id: str | None
    requirement_set_hash: str
    calculation_records_hash: str
    traceability_graph_hash: str
    code_fingerprint: str
    model_fingerprint: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RevisionDelta:
    schema_version: str
    from_revision_id: str
    to_revision_id: str
    changed_domains: list[str]
    changed_hashes: dict[str, dict[str, str]]

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReverificationResult:
    check_id: str
    clause_id: str
    status: str
    evidence_refs: list[str]

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BaselineUpdateStatus:
    schema_version: str
    from_revision_id: str
    to_revision_id: str
    decision: str
    rationale: str
    reverification_check_ids: list[str]

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ImpactReport:
    schema_version: str
    generated_at_utc: str
    from_revision_id: str
    to_revision_id: str
    revision_delta: RevisionDelta
    impacted_clause_ids: list[str]
    minimal_reverification_check_ids: list[str]
    reverification_results: list[ReverificationResult]
    baseline_update_status: BaselineUpdateStatus
    evidence_links: list[str]
    signing: dict[str, str]
    deterministic_hash: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at_utc": self.generated_at_utc,
            "from_revision_id": self.from_revision_id,
            "to_revision_id": self.to_revision_id,
            "revision_delta": self.revision_delta.to_json_dict(),
            "impacted_clause_ids": self.impacted_clause_ids,
            "minimal_reverification_check_ids": self.minimal_reverification_check_ids,
            "reverification_results": [result.to_json_dict() for result in self.reverification_results],
            "baseline_update_status": self.baseline_update_status.to_json_dict(),
            "evidence_links": self.evidence_links,
            "signing": self.signing,
            "deterministic_hash": self.deterministic_hash,
        }


def build_revision_trace_snapshot(
    *,
    revision_id: str,
    previous_revision_id: str | None,
    requirement_set_hash: str,
    calculation_records_hash: str,
    traceability_graph_hash: str,
    code_fingerprint: str,
    model_fingerprint: str,
) -> RevisionTraceSnapshot:
    """Build deterministic snapshot metadata used for BL-008 delta detection."""
    if not revision_id.strip():
        raise ValueError("BL-008 snapshot build failed: revision_id must be non-empty.")
    if not code_fingerprint.strip() or not model_fingerprint.strip():
        raise ValueError("BL-008 snapshot build failed: code/model fingerprint must be non-empty.")
    return RevisionTraceSnapshot(
        schema_version=_REVISION_SNAPSHOT_VERSION,
        revision_id=revision_id,
        previous_revision_id=previous_revision_id,
        requirement_set_hash=requirement_set_hash,
        calculation_records_hash=calculation_records_hash,
        traceability_graph_hash=traceability_graph_hash,
        code_fingerprint=code_fingerprint,
        model_fingerprint=model_fingerprint,
    )


def detect_revision_delta(previous: RevisionTraceSnapshot, current: RevisionTraceSnapshot) -> RevisionDelta:
    """Detect requirement/code/model deltas between two deterministic revision snapshots."""
    changed_domains: list[str] = []
    changed_hashes: dict[str, dict[str, str]] = {}

    _append_domain_change(
        changed_domains,
        changed_hashes,
        "requirement",
        previous.requirement_set_hash,
        current.requirement_set_hash,
    )
    _append_domain_change(changed_domains, changed_hashes, "code", previous.code_fingerprint, current.code_fingerprint)
    _append_domain_change(
        changed_domains,
        changed_hashes,
        "model",
        previous.model_fingerprint,
        current.model_fingerprint,
    )

    return RevisionDelta(
        schema_version="RevisionDelta.v1",
        from_revision_id=previous.revision_id,
        to_revision_id=current.revision_id,
        changed_domains=changed_domains,
        changed_hashes=changed_hashes,
    )


def generate_change_impact_report(
    previous_snapshot: RevisionTraceSnapshot,
    current_snapshot: RevisionTraceSnapshot,
    previous_graph: TraceabilityGraphRevision,
    current_graph: TraceabilityGraphRevision,
    current_calculation_records: CalculationRecordsArtifact,
    *,
    signing_key_ref: str,
    now_utc: datetime | None = None,
) -> ImpactReport:
    """Generate a signed BL-008 impact report with selective re-verification and baseline decision."""
    if not signing_key_ref.strip():
        raise ValueError("BL-008 impact report failed: signing_key_ref must be non-empty.")

    delta = detect_revision_delta(previous_snapshot, current_snapshot)
    selected_checks, impacted_clause_ids = compute_minimal_reverification_set(
        delta,
        previous_graph,
        current_graph,
        current_calculation_records,
    )
    reverification_results = execute_selective_reverification(selected_checks, current_graph)

    baseline_decision = "accepted"
    rationale = "No impacted checks were identified."
    if reverification_results:
        all_pass = all(result.status == "pass" for result in reverification_results)
        baseline_decision = "accepted" if all_pass else "rejected"
        rationale = (
            "All impacted checks passed deterministic re-verification."
            if all_pass
            else "At least one impacted check failed deterministic re-verification."
        )

    baseline_status = BaselineUpdateStatus(
        schema_version=BASELINE_UPDATE_STATUS_VERSION,
        from_revision_id=previous_snapshot.revision_id,
        to_revision_id=current_snapshot.revision_id,
        decision=baseline_decision,
        rationale=rationale,
        reverification_check_ids=[check.check_id for check in selected_checks],
    )

    generated_at = (now_utc or datetime.now(tz=timezone.utc)).replace(microsecond=0).isoformat()
    evidence_links = _build_evidence_links(
        previous_snapshot,
        current_snapshot,
        current_graph,
        current_calculation_records,
        reverification_results,
    )

    unsigned_payload = {
        "schema_version": IMPACT_REPORT_VERSION,
        "generated_at_utc": generated_at,
        "from_revision_id": previous_snapshot.revision_id,
        "to_revision_id": current_snapshot.revision_id,
        "revision_delta": delta.to_json_dict(),
        "impacted_clause_ids": impacted_clause_ids,
        "minimal_reverification_check_ids": [check.check_id for check in selected_checks],
        "reverification_results": [result.to_json_dict() for result in reverification_results],
        "baseline_update_status": baseline_status.to_json_dict(),
        "evidence_links": evidence_links,
        "signing": {
            "algorithm": "sha256",
            "signing_key_ref": signing_key_ref,
            "signature": _sign_payload(signing_key_ref, {
                "to_revision_id": current_snapshot.revision_id,
                "revision_delta": delta.to_json_dict(),
                "minimal_reverification_check_ids": [check.check_id for check in selected_checks],
                "evidence_links": evidence_links,
            }),
        },
    }

    deterministic_hash = _sha256_payload(unsigned_payload)
    return ImpactReport(
        schema_version=IMPACT_REPORT_VERSION,
        generated_at_utc=generated_at,
        from_revision_id=previous_snapshot.revision_id,
        to_revision_id=current_snapshot.revision_id,
        revision_delta=delta,
        impacted_clause_ids=impacted_clause_ids,
        minimal_reverification_check_ids=[check.check_id for check in selected_checks],
        reverification_results=reverification_results,
        baseline_update_status=baseline_status,
        evidence_links=evidence_links,
        signing=unsigned_payload["signing"],
        deterministic_hash=deterministic_hash,
    )


def compute_minimal_reverification_set(
    delta: RevisionDelta,
    previous_graph: TraceabilityGraphRevision,
    current_graph: TraceabilityGraphRevision,
    current_calculation_records: CalculationRecordsArtifact,
) -> tuple[list[CalculationRecord], list[str]]:
    """Compute the minimal set of checks that need re-verification for the revision delta."""
    checks_by_id = {check.check_id: check for check in current_calculation_records.checks}

    if "code" in delta.changed_domains:
        selected = sorted(current_calculation_records.checks, key=lambda check: check.check_id)
        impacted = sorted({check.clause_id for check in selected})
        return selected, impacted

    impacted_clauses = _collect_impacted_clauses(delta, previous_graph, current_graph)
    impacted_check_ids = {
        check.check_id for check in current_calculation_records.checks if check.clause_id in impacted_clauses
    }

    if "model" in delta.changed_domains:
        impacted_model_refs = _collect_impacted_model_refs(previous_graph, current_graph)
        model_to_results = _map_model_to_result_ids(current_graph.links)
        for model_ref in impacted_model_refs:
            for result_id in model_to_results.get(model_ref, []):
                check_id = _parse_check_id_from_result_ref(result_id)
                if check_id in checks_by_id:
                    impacted_check_ids.add(check_id)

    selected_checks = sorted((checks_by_id[check_id] for check_id in impacted_check_ids), key=lambda check: check.check_id)
    impacted_clause_ids = sorted({check.clause_id for check in selected_checks})
    return selected_checks, impacted_clause_ids


def execute_selective_reverification(
    selected_checks: list[CalculationRecord],
    current_graph: TraceabilityGraphRevision,
) -> list[ReverificationResult]:
    """Execute deterministic selective re-verification using already-generated check results."""
    artifact_refs_by_result = _map_result_to_artifact_refs(current_graph.links)
    results: list[ReverificationResult] = []

    for check in sorted(selected_checks, key=lambda item: item.check_id):
        result_ref = f"{check.check_id}:pass={str(check.pass_status).lower()}"
        evidence_refs = artifact_refs_by_result.get(result_ref, [])
        if not evidence_refs:
            evidence_refs = [f"{CALCULATION_RECORDS_VERSION}#missing:{check.check_id}"]

        results.append(
            ReverificationResult(
                check_id=check.check_id,
                clause_id=check.clause_id,
                status="pass" if check.pass_status else "fail",
                evidence_refs=evidence_refs,
            )
        )

    return results


def write_impact_report(
    impact_report: ImpactReport,
    directory: str | Path,
    *,
    filename_prefix: str = "",
) -> Path:
    """Persist a deterministic BL-008 ImpactReport artifact."""
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    output_path = target / f"{filename_prefix}{IMPACT_REPORT_VERSION}.json"
    output_path.write_text(json.dumps(impact_report.to_json_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def _collect_impacted_clauses(
    delta: RevisionDelta,
    previous_graph: TraceabilityGraphRevision,
    current_graph: TraceabilityGraphRevision,
) -> set[str]:
    impacted_clauses: set[str] = set()

    if "requirement" in delta.changed_domains:
        before_pairs = _collect_requirement_clause_pairs(previous_graph.links)
        after_pairs = _collect_requirement_clause_pairs(current_graph.links)
        for _, clause_id in before_pairs.symmetric_difference(after_pairs):
            impacted_clauses.add(clause_id)

    if "model" in delta.changed_domains:
        before_pairs = _collect_clause_model_pairs(previous_graph.links)
        after_pairs = _collect_clause_model_pairs(current_graph.links)
        for clause_id, _ in before_pairs.symmetric_difference(after_pairs):
            impacted_clauses.add(clause_id)

    return impacted_clauses


def _collect_impacted_model_refs(
    previous_graph: TraceabilityGraphRevision,
    current_graph: TraceabilityGraphRevision,
) -> set[str]:
    before_pairs = _collect_clause_model_pairs(previous_graph.links)
    after_pairs = _collect_clause_model_pairs(current_graph.links)
    return {model_ref for _, model_ref in before_pairs.symmetric_difference(after_pairs)}


def _collect_requirement_clause_pairs(links: list[TraceabilityLink]) -> set[tuple[str, str]]:
    return {
        (link.source_ref, link.target_ref)
        for link in links
        if link.source_kind == "requirement" and link.target_kind == "clause"
    }


def _collect_clause_model_pairs(links: list[TraceabilityLink]) -> set[tuple[str, str]]:
    return {
        (link.source_ref, link.target_ref)
        for link in links
        if link.source_kind == "clause" and link.target_kind == "model"
    }


def _map_model_to_result_ids(links: list[TraceabilityLink]) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for link in links:
        if link.source_kind != "model" or link.target_kind != "calculation":
            continue
        mapping.setdefault(link.source_ref, []).append(link.target_ref)

    return {key: sorted(values) for key, values in mapping.items()}


def _map_result_to_artifact_refs(links: list[TraceabilityLink]) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for link in links:
        if link.source_kind != "calculation" or link.target_kind != "artifact":
            continue
        mapping.setdefault(link.source_ref, []).append(link.target_ref)

    return {key: sorted(values) for key, values in mapping.items()}


def _parse_check_id_from_result_ref(result_ref: str) -> str:
    return result_ref.split(":pass=", maxsplit=1)[0]


def _build_evidence_links(
    previous_snapshot: RevisionTraceSnapshot,
    current_snapshot: RevisionTraceSnapshot,
    current_graph: TraceabilityGraphRevision,
    current_calculation_records: CalculationRecordsArtifact,
    reverification_results: list[ReverificationResult],
) -> list[str]:
    refs = {
        f"{_REVISION_SNAPSHOT_VERSION}#{previous_snapshot.revision_id}",
        f"{_REVISION_SNAPSHOT_VERSION}#{current_snapshot.revision_id}",
        f"TraceabilityGraphRevision.v1#{current_graph.deterministic_hash}",
        f"{CALCULATION_RECORDS_VERSION}#{current_calculation_records.deterministic_hash}",
    }
    for result in reverification_results:
        refs.update(result.evidence_refs)
    return sorted(refs)


def _append_domain_change(
    changed_domains: list[str],
    changed_hashes: dict[str, dict[str, str]],
    domain: str,
    previous_value: str,
    current_value: str,
) -> None:
    if previous_value == current_value:
        return
    changed_domains.append(domain)
    changed_hashes[domain] = {"from": previous_value, "to": current_value}


def _sha256_payload(payload: Any) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _sign_payload(signing_key_ref: str, payload: dict[str, Any]) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    raw = f"{signing_key_ref}:{normalized}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
