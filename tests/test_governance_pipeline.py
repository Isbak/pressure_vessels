from pressure_vessels.governance_pipeline import (
    GOVERNANCE_GATE_REPORT_SCHEMA_VERSION,
    PolicyExceptionApproval,
    build_governance_policy,
    evaluate_governance_gates,
)


def test_governance_gates_fail_when_required_gate_missing_or_failed():
    policy = build_governance_policy(
        required_gates=["lint", "tests", "security", "reporting"],
        artifact_retention_days=30,
        approved_exceptions=[],
    )

    report = evaluate_governance_gates(
        policy=policy,
        gate_results={"lint": "success", "tests": "failure", "security": "success"},
    )

    assert report.schema_version == GOVERNANCE_GATE_REPORT_SCHEMA_VERSION
    assert report.failed_gates == ["reporting", "tests"]
    assert report.gate_status["tests"] == "fail:failure"
    assert report.gate_status["reporting"] == "fail:missing"
    assert report.applied_exception_ids == []


def test_governance_gates_apply_only_explicitly_approved_policy_exception():
    policy = build_governance_policy(
        required_gates=["lint", "tests", "security"],
        artifact_retention_days=30,
        approved_exceptions=[
            PolicyExceptionApproval(
                exception_id="EX-2026-001",
                gate_id="security",
                rationale="Temporary gitleaks false positive while rule fix is reviewed.",
                approved_by="security-reviewer",
                approved_on="2026-04-18",
                approval_record_ref="https://github.com/example/pressure_vessels/pull/12#discussion_r100",
            )
        ],
    )

    report = evaluate_governance_gates(
        policy=policy,
        gate_results={"lint": "success", "tests": "success", "security": "failure"},
    )

    assert report.failed_gates == []
    assert report.gate_status["security"] == "exception-approved"
    assert report.applied_exception_ids == ["EX-2026-001"]


def test_policy_exception_requires_explicit_approval_record_fields():
    invalid_exception = PolicyExceptionApproval(
        exception_id="EX-2026-002",
        gate_id="reporting",
        rationale="CI reporting endpoint outage.",
        approved_by="",
        approved_on="2026-04-18",
        approval_record_ref="",
    )

    try:
        build_governance_policy(
            required_gates=["reporting"],
            artifact_retention_days=14,
            approved_exceptions=[invalid_exception],
        )
        raise AssertionError("Expected policy validation to fail for missing approval fields.")
    except ValueError as error:
        assert "approved_by" in str(error) or "approval_record_ref" in str(error)
