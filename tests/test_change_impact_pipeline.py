from datetime import datetime, timezone

from pressure_vessels.calculation_pipeline import run_calculation_pipeline
from pressure_vessels.change_impact_pipeline import (
    BASELINE_UPDATE_STATUS_VERSION,
    IMPACT_REPORT_VERSION,
    build_revision_trace_snapshot,
    compute_minimal_reverification_set,
    detect_revision_delta,
    generate_change_impact_report,
)
from pressure_vessels.compliance_pipeline import generate_compliance_dossier
from pressure_vessels.design_basis_pipeline import build_design_basis
from pressure_vessels.requirements_pipeline import parse_prompt_to_requirement_set
from pressure_vessels.traceability_pipeline import TraceabilityLink, build_traceability_graph_revision, with_additional_links

FIXED_NOW = datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc)


def _prompt() -> str:
    return (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )


def _build_revision(revision_id: str):
    requirement_set = parse_prompt_to_requirement_set(_prompt(), now_utc=FIXED_NOW)
    design_basis, matrix = build_design_basis(requirement_set, now_utc=FIXED_NOW)
    calculation_records, non_conformance = run_calculation_pipeline(
        requirement_set,
        design_basis,
        matrix,
        now_utc=FIXED_NOW,
    )
    _, machine = generate_compliance_dossier(
        requirement_set,
        design_basis,
        matrix,
        calculation_records,
        non_conformance,
        now_utc=FIXED_NOW,
    )
    graph = build_traceability_graph_revision(
        requirement_set,
        design_basis,
        matrix,
        machine,
        revision_id=revision_id,
        now_utc=FIXED_NOW,
    )
    return requirement_set, calculation_records, graph


def test_detect_revision_delta_for_requirement_code_and_model_domains():
    previous = build_revision_trace_snapshot(
        revision_id="REV-0001",
        previous_revision_id=None,
        requirement_set_hash="req-hash-a",
        calculation_records_hash="calc-hash-a",
        traceability_graph_hash="graph-hash-a",
        code_fingerprint="code-a",
        model_fingerprint="model-a",
    )
    current = build_revision_trace_snapshot(
        revision_id="REV-0002",
        previous_revision_id="REV-0001",
        requirement_set_hash="req-hash-b",
        calculation_records_hash="calc-hash-b",
        traceability_graph_hash="graph-hash-b",
        code_fingerprint="code-b",
        model_fingerprint="model-b",
    )

    delta = detect_revision_delta(previous, current)

    assert delta.changed_domains == ["requirement", "code", "model"]
    assert delta.changed_hashes["requirement"] == {"from": "req-hash-a", "to": "req-hash-b"}
    assert delta.changed_hashes["code"] == {"from": "code-a", "to": "code-b"}
    assert delta.changed_hashes["model"] == {"from": "model-a", "to": "model-b"}


def test_compute_minimal_reverification_set_scopes_to_impacted_clause_for_model_delta():
    requirement_set, calculation_records, previous_graph = _build_revision("REV-0100")
    current_graph = with_additional_links(
        previous_graph,
        [
            TraceabilityLink(
                link_id="UG-27:ug27_shell_thickness_v2:bl008-model",
                source_kind="clause",
                source_ref="UG-27",
                target_kind="model",
                target_ref="ug27_shell_thickness_v2",
                relation="implemented_by",
                clause_id="UG-27",
            ),
            TraceabilityLink(
                link_id="ug27_shell_thickness_v2:UG-27-shell:pass=true:bl008-model-calc",
                source_kind="model",
                source_ref="ug27_shell_thickness_v2",
                target_kind="calculation",
                target_ref="UG-27-shell:pass=true",
                relation="produces",
                clause_id="UG-27",
            ),
        ],
        allow_mutation=True,
    )

    previous_snapshot = build_revision_trace_snapshot(
        revision_id="REV-0100",
        previous_revision_id=None,
        requirement_set_hash=requirement_set.deterministic_hash,
        calculation_records_hash=calculation_records.deterministic_hash,
        traceability_graph_hash=previous_graph.deterministic_hash,
        code_fingerprint="git:abc123",
        model_fingerprint="models:v1",
    )
    current_snapshot = build_revision_trace_snapshot(
        revision_id="REV-0101",
        previous_revision_id="REV-0100",
        requirement_set_hash=requirement_set.deterministic_hash,
        calculation_records_hash=calculation_records.deterministic_hash,
        traceability_graph_hash=current_graph.deterministic_hash,
        code_fingerprint="git:abc123",
        model_fingerprint="models:v2",
    )

    delta = detect_revision_delta(previous_snapshot, current_snapshot)
    checks, impacted_clauses = compute_minimal_reverification_set(
        delta,
        previous_graph,
        current_graph,
        calculation_records,
    )

    assert impacted_clauses == ["UG-27"]
    assert [check.check_id for check in checks] == ["UG-27-shell", "UG-27-shell-mawp"]


def test_generate_change_impact_report_is_signed_with_evidence_and_baseline_status():
    requirement_set, calculation_records, previous_graph = _build_revision("REV-0200")
    current_graph = with_additional_links(
        previous_graph,
        [
            TraceabilityLink(
                link_id="UG-27:ug27_shell_thickness_v2:bl008-model",
                source_kind="clause",
                source_ref="UG-27",
                target_kind="model",
                target_ref="ug27_shell_thickness_v2",
                relation="implemented_by",
                clause_id="UG-27",
            ),
            TraceabilityLink(
                link_id="ug27_shell_thickness_v2:UG-27-shell:pass=true:bl008-model-calc",
                source_kind="model",
                source_ref="ug27_shell_thickness_v2",
                target_kind="calculation",
                target_ref="UG-27-shell:pass=true",
                relation="produces",
                clause_id="UG-27",
            ),
        ],
        allow_mutation=True,
    )

    previous_snapshot = build_revision_trace_snapshot(
        revision_id="REV-0200",
        previous_revision_id=None,
        requirement_set_hash=requirement_set.deterministic_hash,
        calculation_records_hash=calculation_records.deterministic_hash,
        traceability_graph_hash=previous_graph.deterministic_hash,
        code_fingerprint="git:abc123",
        model_fingerprint="models:v1",
    )
    current_snapshot = build_revision_trace_snapshot(
        revision_id="REV-0201",
        previous_revision_id="REV-0200",
        requirement_set_hash=requirement_set.deterministic_hash,
        calculation_records_hash=calculation_records.deterministic_hash,
        traceability_graph_hash=current_graph.deterministic_hash,
        code_fingerprint="git:abc123",
        model_fingerprint="models:v2",
    )

    report = generate_change_impact_report(
        previous_snapshot,
        current_snapshot,
        previous_graph,
        current_graph,
        calculation_records,
        signing_key_ref="kms://pressure-vessels/bl-008",
        now_utc=FIXED_NOW,
    )

    assert report.schema_version == IMPACT_REPORT_VERSION
    assert report.baseline_update_status.schema_version == BASELINE_UPDATE_STATUS_VERSION
    assert report.baseline_update_status.decision == "accepted"
    assert report.minimal_reverification_check_ids == ["UG-27-shell", "UG-27-shell-mawp"]
    assert report.signing["signing_key_ref"] == "kms://pressure-vessels/bl-008"
    assert len(report.signing["signature"]) == 64
    assert any(
        ref.startswith(f"CalculationRecords.v1#{calculation_records.deterministic_hash}:UG-27-shell")
        for ref in report.evidence_links
    )
