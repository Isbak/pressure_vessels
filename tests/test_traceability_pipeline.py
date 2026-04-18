import json
from datetime import datetime, timezone

import pytest

from pressure_vessels.calculation_pipeline import run_calculation_pipeline
from pressure_vessels.compliance_pipeline import generate_compliance_dossier
from pressure_vessels.design_basis_pipeline import build_design_basis
from pressure_vessels.requirements_pipeline import parse_prompt_to_requirement_set
from pressure_vessels.traceability_pipeline import (
    ApprovalRecord,
    TraceabilityLink,
    build_audit_report_template,
    build_traceability_graph_revision,
    query_clause_evidence,
    query_graph_by_revision,
    with_additional_links,
    write_traceability_graph_revision,
)

FIXED_NOW = datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc)


def _default_prompt() -> str:
    return (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )


def _build_graph_inputs(prompt: str):
    requirement_set = parse_prompt_to_requirement_set(prompt, now_utc=FIXED_NOW)
    design_basis, matrix = build_design_basis(requirement_set, now_utc=FIXED_NOW)
    calculation_records, non_conformance = run_calculation_pipeline(
        requirement_set,
        design_basis,
        matrix,
        now_utc=FIXED_NOW,
        use_mvp_defaults=True,
    )
    _, machine = generate_compliance_dossier(
        requirement_set,
        design_basis,
        matrix,
        calculation_records,
        non_conformance,
        now_utc=FIXED_NOW,
    )
    return requirement_set, design_basis, matrix, machine


def test_graph_schema_stores_requirement_clause_model_calculation_artifact_and_approval_links():
    req, design_basis, matrix, machine = _build_graph_inputs(_default_prompt())
    approvals = [
        ApprovalRecord(
            approval_id="APR-001",
            approver_role="authorized_inspector",
            status="approved",
            artifact_ref=f"ComplianceDossierMachine.v1#{machine.deterministic_hash}",
        )
    ]

    graph = build_traceability_graph_revision(
        req,
        design_basis,
        matrix,
        machine,
        revision_id="REV-0001",
        approvals=approvals,
        now_utc=FIXED_NOW,
    )

    endpoint_kinds = {link.source_kind for link in graph.links} | {link.target_kind for link in graph.links}
    assert endpoint_kinds == {"requirement", "clause", "model", "calculation", "artifact", "approval"}
    assert graph.immutable is True
    assert graph.revision_id == "REV-0001"


def test_revision_and_clause_queries_return_scoped_links():
    req, design_basis, matrix, machine = _build_graph_inputs(_default_prompt())
    rev1 = build_traceability_graph_revision(
        req,
        design_basis,
        matrix,
        machine,
        revision_id="REV-0001",
        now_utc=FIXED_NOW,
    )
    rev2 = build_traceability_graph_revision(
        req,
        design_basis,
        matrix,
        machine,
        revision_id="REV-0002",
        previous_revision_id="REV-0001",
        now_utc=FIXED_NOW,
    )

    fetched = query_graph_by_revision([rev1, rev2], "REV-0002")
    assert fetched.revision_id == "REV-0002"

    ug27_links = query_clause_evidence([rev1, rev2], "UG-27", revision_id="REV-0002")
    assert ug27_links
    assert all(link.clause_id == "UG-27" or link.source_ref == "UG-27" or link.target_ref == "UG-27" for link in ug27_links)


def test_writes_are_revisioned_and_immutable_by_default(tmp_path):
    req, design_basis, matrix, machine = _build_graph_inputs(_default_prompt())
    graph = build_traceability_graph_revision(
        req,
        design_basis,
        matrix,
        machine,
        revision_id="REV-0001",
        now_utc=FIXED_NOW,
    )

    path = write_traceability_graph_revision(graph, tmp_path)
    assert path.name == "REV-0001.traceability_graph.json"

    with path.open() as handle:
        on_disk = json.load(handle)
    assert on_disk == graph.to_json_dict()

    with pytest.raises(FileExistsError):
        write_traceability_graph_revision(graph, tmp_path)

    with pytest.raises(ValueError, match="immutable"):
        with_additional_links(
            graph,
            [
                TraceabilityLink(
                    link_id="custom",
                    source_kind="artifact",
                    source_ref="A",
                    target_kind="approval",
                    target_ref="B",
                    relation="approved_by",
                )
            ],
        )


def test_audit_report_template_is_deterministic_and_clause_scoped():
    req, design_basis, matrix, machine = _build_graph_inputs(_default_prompt())
    graph = build_traceability_graph_revision(
        req,
        design_basis,
        matrix,
        machine,
        revision_id="REV-0003",
        now_utc=FIXED_NOW,
    )

    report = build_audit_report_template(graph, clause_id="UG-45")

    assert report["schema_version"] == "TraceabilityAuditReportTemplate.v1"
    assert report["revision_id"] == "REV-0003"
    assert report["clause_scope"] == "UG-45"
    assert report["summary_lines"][1] == "Immutable: true"
    assert all(row["clause_id"] in {"UG-45", "-"} for row in report["evidence_rows"])
