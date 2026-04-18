"""Deterministic enterprise integration adapters and sync orchestration for BL-011."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from .traceability_pipeline import TraceabilityLink

ENTERPRISE_INTEGRATION_BATCH_VERSION = "EnterpriseIntegrationBatch.v1"

_SUPPORTED_SYSTEM_KINDS = {"plm", "erp", "qms"}


@dataclass(frozen=True)
class EnterpriseSystemTarget:
    system_code: str
    system_kind: str
    endpoint: str
    max_retries: int = 2
    fail_first_attempts: int = 0

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ArtifactSyncRecord:
    artifact_ref: str
    artifact_type: str
    content_hash: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovalSyncRecord:
    approval_id: str
    artifact_ref: str
    status: str
    approver_role: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IntegrationAttemptLog:
    system_code: str
    entity_kind: str
    entity_ref: str
    attempt: int
    status: str
    detail: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IntegrationBoundaryMapping:
    system_code: str
    entity_kind: str
    internal_ref: str
    external_ref: str
    traceability_link_ids: list[str]

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IntegrationFailureRecord:
    system_code: str
    entity_kind: str
    entity_ref: str
    attempts: int
    reason: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EnterpriseIntegrationBatch:
    schema_version: str
    batch_id: str
    generated_at_utc: str
    targets: list[EnterpriseSystemTarget]
    mappings: list[IntegrationBoundaryMapping]
    attempt_logs: list[IntegrationAttemptLog]
    failures: list[IntegrationFailureRecord]
    deterministic_hash: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "batch_id": self.batch_id,
            "generated_at_utc": self.generated_at_utc,
            "targets": [target.to_json_dict() for target in self.targets],
            "mappings": [mapping.to_json_dict() for mapping in self.mappings],
            "attempt_logs": [attempt.to_json_dict() for attempt in self.attempt_logs],
            "failures": [failure.to_json_dict() for failure in self.failures],
            "deterministic_hash": self.deterministic_hash,
        }


def run_enterprise_integration_batch(
    *,
    batch_id: str,
    targets: list[EnterpriseSystemTarget],
    artifacts: list[ArtifactSyncRecord],
    approvals: list[ApprovalSyncRecord],
    traceability_links: list[TraceabilityLink],
    now_utc: datetime | None = None,
) -> EnterpriseIntegrationBatch:
    """Sync artifacts and approvals to configured enterprise systems with retry observability."""
    if not batch_id.strip():
        raise ValueError("BL-011 sync failed: batch_id must be non-empty.")
    if not targets:
        raise ValueError("BL-011 sync failed: at least one enterprise target is required.")

    _validate_targets(targets)
    link_index = _index_traceability_links(traceability_links)

    mappings: list[IntegrationBoundaryMapping] = []
    attempt_logs: list[IntegrationAttemptLog] = []
    failures: list[IntegrationFailureRecord] = []

    for target in sorted(targets, key=lambda item: (item.system_kind, item.system_code)):
        for artifact in sorted(artifacts, key=lambda item: item.artifact_ref):
            success, logs, failure = _sync_entity_with_retry(
                target=target,
                entity_kind="artifact",
                entity_ref=artifact.artifact_ref,
            )
            attempt_logs.extend(logs)
            if success:
                mappings.append(
                    IntegrationBoundaryMapping(
                        system_code=target.system_code,
                        entity_kind="artifact",
                        internal_ref=artifact.artifact_ref,
                        external_ref=_build_external_ref(target, "artifact", artifact.artifact_ref),
                        traceability_link_ids=sorted(link_index.get(artifact.artifact_ref, set())),
                    )
                )
            elif failure is not None:
                failures.append(failure)

        for approval in sorted(approvals, key=lambda item: item.approval_id):
            success, logs, failure = _sync_entity_with_retry(
                target=target,
                entity_kind="approval",
                entity_ref=approval.approval_id,
            )
            attempt_logs.extend(logs)
            if success:
                mappings.append(
                    IntegrationBoundaryMapping(
                        system_code=target.system_code,
                        entity_kind="approval",
                        internal_ref=approval.approval_id,
                        external_ref=_build_external_ref(target, "approval", approval.approval_id),
                        traceability_link_ids=sorted(link_index.get(approval.approval_id, set())),
                    )
                )
            elif failure is not None:
                failures.append(failure)

    _validate_traceability_preservation(mappings, link_index)

    generated_at = (now_utc or datetime.now(tz=timezone.utc)).replace(microsecond=0).isoformat()
    payload = {
        "schema_version": ENTERPRISE_INTEGRATION_BATCH_VERSION,
        "batch_id": batch_id,
        "generated_at_utc": generated_at,
        "targets": [target.to_json_dict() for target in sorted(targets, key=lambda item: (item.system_kind, item.system_code))],
        "mappings": [mapping.to_json_dict() for mapping in sorted(mappings, key=lambda item: (item.system_code, item.entity_kind, item.internal_ref))],
        "attempt_logs": [attempt.to_json_dict() for attempt in sorted(attempt_logs, key=lambda item: (item.system_code, item.entity_kind, item.entity_ref, item.attempt))],
        "failures": [failure.to_json_dict() for failure in sorted(failures, key=lambda item: (item.system_code, item.entity_kind, item.entity_ref))],
    }

    return EnterpriseIntegrationBatch(
        schema_version=ENTERPRISE_INTEGRATION_BATCH_VERSION,
        batch_id=batch_id,
        generated_at_utc=generated_at,
        targets=sorted(targets, key=lambda item: (item.system_kind, item.system_code)),
        mappings=sorted(mappings, key=lambda item: (item.system_code, item.entity_kind, item.internal_ref)),
        attempt_logs=sorted(attempt_logs, key=lambda item: (item.system_code, item.entity_kind, item.entity_ref, item.attempt)),
        failures=sorted(failures, key=lambda item: (item.system_code, item.entity_kind, item.entity_ref)),
        deterministic_hash=_sha256_payload(payload),
    )


def write_enterprise_integration_batch(
    integration_batch: EnterpriseIntegrationBatch,
    directory: str | Path,
    *,
    filename_prefix: str = "enterprise_integration",
) -> Path:
    """Persist deterministic enterprise integration payload."""
    output_dir = Path(directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{filename_prefix}.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(integration_batch.to_json_dict(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return output_path


def _validate_targets(targets: list[EnterpriseSystemTarget]) -> None:
    seen_codes: set[str] = set()
    for target in targets:
        if not target.system_code.strip():
            raise ValueError("BL-011 sync failed: system_code must be non-empty.")
        if target.system_code in seen_codes:
            raise ValueError(f"BL-011 sync failed: duplicate system_code '{target.system_code}'.")
        seen_codes.add(target.system_code)

        if target.system_kind not in _SUPPORTED_SYSTEM_KINDS:
            raise ValueError(
                f"BL-011 sync failed: unsupported system_kind '{target.system_kind}'."
            )
        if not target.endpoint.strip():
            raise ValueError("BL-011 sync failed: endpoint must be non-empty.")
        if target.max_retries < 0:
            raise ValueError("BL-011 sync failed: max_retries cannot be negative.")
        if target.fail_first_attempts < 0:
            raise ValueError("BL-011 sync failed: fail_first_attempts cannot be negative.")


def _sync_entity_with_retry(
    *,
    target: EnterpriseSystemTarget,
    entity_kind: str,
    entity_ref: str,
) -> tuple[bool, list[IntegrationAttemptLog], IntegrationFailureRecord | None]:
    logs: list[IntegrationAttemptLog] = []
    max_attempts = target.max_retries + 1

    for attempt in range(1, max_attempts + 1):
        if attempt <= target.fail_first_attempts:
            logs.append(
                IntegrationAttemptLog(
                    system_code=target.system_code,
                    entity_kind=entity_kind,
                    entity_ref=entity_ref,
                    attempt=attempt,
                    status="retryable_failure",
                    detail=f"Deterministic adapter failure on attempt {attempt}.",
                )
            )
            continue

        logs.append(
            IntegrationAttemptLog(
                system_code=target.system_code,
                entity_kind=entity_kind,
                entity_ref=entity_ref,
                attempt=attempt,
                status="success",
                detail=f"Synchronized to {target.endpoint}.",
            )
        )
        return True, logs, None

    return (
        False,
        logs,
        IntegrationFailureRecord(
            system_code=target.system_code,
            entity_kind=entity_kind,
            entity_ref=entity_ref,
            attempts=max_attempts,
            reason="Exhausted retry budget after deterministic adapter failures.",
        ),
    )


def _index_traceability_links(traceability_links: list[TraceabilityLink]) -> dict[str, set[str]]:
    link_index: dict[str, set[str]] = {}
    for link in traceability_links:
        link_index.setdefault(link.source_ref, set()).add(link.link_id)
        link_index.setdefault(link.target_ref, set()).add(link.link_id)
    return link_index


def _validate_traceability_preservation(
    mappings: list[IntegrationBoundaryMapping],
    link_index: dict[str, set[str]],
) -> None:
    for mapping in mappings:
        expected_link_ids = sorted(link_index.get(mapping.internal_ref, set()))
        if mapping.traceability_link_ids != expected_link_ids:
            raise ValueError(
                "BL-011 sync failed: traceability links changed across integration boundary "
                f"for {mapping.entity_kind}:{mapping.internal_ref}."
            )


def _build_external_ref(target: EnterpriseSystemTarget, entity_kind: str, entity_ref: str) -> str:
    return f"{target.system_code}:{entity_kind}:{entity_ref}"


def _sha256_payload(payload: dict[str, Any]) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
