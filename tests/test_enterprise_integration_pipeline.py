import json
from datetime import datetime, timezone

import pytest

from pressure_vessels.enterprise_integration_pipeline import (
    ENTERPRISE_INTEGRATION_BATCH_VERSION,
    ApprovalSyncRecord,
    ArtifactSyncRecord,
    EnterpriseSystemTarget,
    run_enterprise_integration_batch,
    write_enterprise_integration_batch,
)
from pressure_vessels.traceability_pipeline import TraceabilityLink

FIXED_NOW = datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc)


def _traceability_links() -> list[TraceabilityLink]:
    return [
        TraceabilityLink(
            link_id="calc-001:dossier-001:calc-artifact",
            source_kind="calculation",
            source_ref="calc-001",
            target_kind="artifact",
            target_ref="dossier-001",
            relation="recorded_in",
            clause_id="UG-27",
        ),
        TraceabilityLink(
            link_id="dossier-001:approval-001:artifact-approval",
            source_kind="artifact",
            source_ref="dossier-001",
            target_kind="approval",
            target_ref="approval-001",
            relation="approved_by:design_authority:approved",
            clause_id=None,
        ),
    ]


def test_syncs_artifacts_and_approvals_across_configured_enterprise_targets():
    batch = run_enterprise_integration_batch(
        batch_id="batch-001",
        targets=[
            EnterpriseSystemTarget(system_code="PLM-A", system_kind="plm", endpoint="plm://system-a"),
            EnterpriseSystemTarget(system_code="QMS-A", system_kind="qms", endpoint="qms://system-a"),
        ],
        artifacts=[
            ArtifactSyncRecord(
                artifact_ref="dossier-001",
                artifact_type="certification_dossier",
                content_hash="hash-dossier-001",
            )
        ],
        approvals=[
            ApprovalSyncRecord(
                approval_id="approval-001",
                artifact_ref="dossier-001",
                status="approved",
                approver_role="design_authority",
            )
        ],
        traceability_links=_traceability_links(),
        now_utc=FIXED_NOW,
    )

    assert batch.schema_version == ENTERPRISE_INTEGRATION_BATCH_VERSION
    assert len(batch.mappings) == 4
    assert all(mapping.external_ref.startswith(mapping.system_code) for mapping in batch.mappings)
    assert not batch.failures


def test_traceability_links_preserved_in_boundary_mappings():
    batch = run_enterprise_integration_batch(
        batch_id="batch-002",
        targets=[EnterpriseSystemTarget(system_code="ERP-A", system_kind="erp", endpoint="erp://system-a")],
        artifacts=[
            ArtifactSyncRecord(
                artifact_ref="dossier-001",
                artifact_type="certification_dossier",
                content_hash="hash-dossier-001",
            )
        ],
        approvals=[
            ApprovalSyncRecord(
                approval_id="approval-001",
                artifact_ref="dossier-001",
                status="approved",
                approver_role="design_authority",
            )
        ],
        traceability_links=_traceability_links(),
        now_utc=FIXED_NOW,
    )

    mapping_index = {(row.entity_kind, row.internal_ref): row for row in batch.mappings}

    artifact_mapping = mapping_index[("artifact", "dossier-001")]
    approval_mapping = mapping_index[("approval", "approval-001")]

    assert artifact_mapping.traceability_link_ids == [
        "calc-001:dossier-001:calc-artifact",
        "dossier-001:approval-001:artifact-approval",
    ]
    assert approval_mapping.traceability_link_ids == ["dossier-001:approval-001:artifact-approval"]


def test_retry_and_failure_handling_are_observable_and_deterministic(tmp_path):
    batch = run_enterprise_integration_batch(
        batch_id="batch-003",
        targets=[
            EnterpriseSystemTarget(
                system_code="PLM-RETRY",
                system_kind="plm",
                endpoint="plm://retry",
                max_retries=2,
                fail_first_attempts=1,
            ),
            EnterpriseSystemTarget(
                system_code="QMS-FAIL",
                system_kind="qms",
                endpoint="qms://fail",
                max_retries=1,
                fail_first_attempts=5,
            ),
        ],
        artifacts=[
            ArtifactSyncRecord(
                artifact_ref="dossier-001",
                artifact_type="certification_dossier",
                content_hash="hash-dossier-001",
            )
        ],
        approvals=[
            ApprovalSyncRecord(
                approval_id="approval-001",
                artifact_ref="dossier-001",
                status="approved",
                approver_role="design_authority",
            )
        ],
        traceability_links=_traceability_links(),
        now_utc=FIXED_NOW,
    )

    success_attempts = [
        row for row in batch.attempt_logs if row.system_code == "PLM-RETRY" and row.status == "success"
    ]
    qms_failures = [row for row in batch.failures if row.system_code == "QMS-FAIL"]

    assert len(success_attempts) == 2
    assert all(row.attempt == 2 for row in success_attempts)
    assert len(qms_failures) == 2
    assert all(row.attempts == 2 for row in qms_failures)

    output_path = write_enterprise_integration_batch(batch, tmp_path, filename_prefix="batch-003")
    with output_path.open(encoding="utf-8") as handle:
        on_disk = json.load(handle)

    assert on_disk == batch.to_json_dict()


def test_rejects_invalid_target_configuration():
    with pytest.raises(ValueError, match="unsupported system_kind"):
        run_enterprise_integration_batch(
            batch_id="batch-004",
            targets=[EnterpriseSystemTarget(system_code="MES-A", system_kind="mes", endpoint="mes://system-a")],
            artifacts=[],
            approvals=[],
            traceability_links=[],
            now_utc=FIXED_NOW,
        )
