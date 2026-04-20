import pytest

from pressure_vessels.workflow_orchestrator import (
    APPROVAL_GATE_EVENT_VERSION,
    WORKFLOW_EXECUTION_REPORT_VERSION,
    WorkflowStageSpec,
    build_approval_gate_event,
    orchestrate_workflow,
)


def test_orchestrator_runs_deterministic_approved_path():
    approval = build_approval_gate_event(
        event_id="APR-0001",
        workflow_id="wf-release-001",
        stage_id="compliance_review",
        gate_id="human_approval",
        decision="approved",
        approver_role="authorized_inspector",
        approver_id="insp-007",
        decided_at_utc="2026-04-18T10:00:00+00:00",
        rationale="Compliance dossier reviewed and accepted.",
    )

    report = orchestrate_workflow(
        workflow_id="wf-release-001",
        stage_specs=[
            WorkflowStageSpec(stage_id="prepare_inputs", requires_approval=False),
            WorkflowStageSpec(stage_id="compliance_review", requires_approval=True),
            WorkflowStageSpec(stage_id="publish_release", requires_approval=False),
        ],
        approval_events=[approval],
    )

    assert report.schema_version == WORKFLOW_EXECUTION_REPORT_VERSION
    assert report.completed_stages == ["prepare_inputs", "compliance_review", "publish_release"]
    assert report.failed_stage is None
    assert report.blocked_stage is None
    assert report.stage_states == {
        "prepare_inputs": "completed",
        "compliance_review": "completed",
        "publish_release": "completed",
    }
    assert [event.sequence for event in report.execution_trace] == list(
        range(1, len(report.execution_trace) + 1)
    )


def test_approval_events_are_immutable_and_include_role_and_timestamp_metadata():
    event_a = build_approval_gate_event(
        event_id="APR-0001",
        workflow_id="wf-release-002",
        stage_id="compliance_review",
        gate_id="human_approval",
        decision="approved",
        approver_role="quality_lead",
        approver_id="qa-21",
        decided_at_utc="2026-04-18T11:00:00+00:00",
        rationale="Quality criteria met.",
    )
    assert event_a.schema_version == APPROVAL_GATE_EVENT_VERSION

    event_b = build_approval_gate_event(
        event_id="APR-0002",
        workflow_id="wf-release-002",
        stage_id="compliance_review",
        gate_id="human_approval",
        decision="rejected",
        approver_role="quality_lead",
        approver_id="qa-21",
        decided_at_utc="2026-04-18T12:00:00+00:00",
        rationale="Second decision should be rejected as duplicate gate event.",
    )

    try:
        orchestrate_workflow(
            workflow_id="wf-release-002",
            stage_specs=[WorkflowStageSpec(stage_id="compliance_review", requires_approval=True)],
            approval_events=[event_a, event_b],
        )
        raise AssertionError("Expected immutable duplicate approval event validation to fail.")
    except ValueError as error:
        assert "immutable" in str(error)


def test_retry_trace_is_observable_before_terminal_success():
    report = orchestrate_workflow(
        workflow_id="wf-release-003",
        stage_specs=[
            WorkflowStageSpec(
                stage_id="sync_enterprise_systems",
                requires_approval=False,
                max_retries=2,
                fail_first_attempts=2,
                escalation_role="operations_manager",
            )
        ],
        approval_events=[],
    )

    assert report.failed_stage is None
    assert report.escalation_target is None
    assert report.stage_states["sync_enterprise_systems"] == "completed"

    statuses = [
        (event.event_type, event.status)
        for event in report.execution_trace
        if event.event_type == "execution_attempt"
    ]
    assert statuses == [
        ("execution_attempt", "retrying"),
        ("execution_attempt", "retrying"),
        ("execution_attempt", "success"),
    ]


def test_workflow_stage_spec_rejects_negative_max_retries():
    with pytest.raises(
        ValueError, match="BL-016 orchestration failed: max_retries cannot be negative."
    ):
        WorkflowStageSpec(stage_id="prepare", requires_approval=False, max_retries=-1)


def test_workflow_stage_spec_rejects_negative_fail_first_attempts():
    with pytest.raises(
        ValueError,
        match="BL-016 orchestration failed: fail_first_attempts cannot be negative.",
    ):
        WorkflowStageSpec(stage_id="prepare", requires_approval=False, fail_first_attempts=-1)


def test_workflow_stage_spec_rejects_max_retries_above_upper_bound():
    with pytest.raises(
        ValueError, match="BL-016 orchestration failed: max_retries cannot exceed 10."
    ):
        WorkflowStageSpec(stage_id="prepare", requires_approval=False, max_retries=11)


def test_workflow_stage_spec_rejects_fail_first_attempts_above_max_retries():
    with pytest.raises(
        ValueError,
        match="BL-016 orchestration failed: fail_first_attempts cannot exceed max_retries.",
    ):
        WorkflowStageSpec(
            stage_id="prepare",
            requires_approval=False,
            max_retries=2,
            fail_first_attempts=3,
        )


def test_workflow_stage_spec_accepts_upper_bounds():
    stage = WorkflowStageSpec(
        stage_id="prepare",
        requires_approval=False,
        max_retries=10,
        fail_first_attempts=10,
    )

    assert stage.max_retries == 10
    assert stage.fail_first_attempts == 10
