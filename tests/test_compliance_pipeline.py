import json
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from pressure_vessels.calculation_pipeline import run_calculation_pipeline
from pressure_vessels.compliance_pipeline import (
    generate_compliance_dossier,
    write_compliance_artifacts,
)
from pressure_vessels.design_basis_pipeline import build_design_basis
from pressure_vessels.requirements_pipeline import parse_prompt_to_requirement_set

FIXED_NOW = datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc)


def _build_inputs(prompt: str):
    requirement_set = parse_prompt_to_requirement_set(prompt, now_utc=FIXED_NOW)
    design_basis, matrix = build_design_basis(requirement_set, now_utc=FIXED_NOW)
    calculation_records, non_conformance_list = run_calculation_pipeline(
        requirement_set,
        design_basis,
        matrix,
        now_utc=FIXED_NOW,
    )
    return requirement_set, design_basis, matrix, calculation_records, non_conformance_list


def test_compliance_dossier_deterministic_with_fixed_timestamp():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix, calc, nc = _build_inputs(prompt)

    human_a, machine_a = generate_compliance_dossier(
        req,
        design_basis,
        matrix,
        calc,
        nc,
        now_utc=FIXED_NOW,
    )
    human_b, machine_b = generate_compliance_dossier(
        req,
        design_basis,
        matrix,
        calc,
        nc,
        now_utc=FIXED_NOW,
    )

    assert human_a.to_json_dict() == human_b.to_json_dict()
    assert machine_a.to_json_dict() == machine_b.to_json_dict()
    assert human_a.deterministic_hash == human_b.deterministic_hash
    assert machine_a.deterministic_hash == machine_b.deterministic_hash


def test_evidence_wiring_maps_requirement_clause_model_result_artifact():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix, calc, nc = _build_inputs(prompt)

    _, machine = generate_compliance_dossier(
        req,
        design_basis,
        matrix,
        calc,
        nc,
        now_utc=FIXED_NOW,
    )

    assert machine.evidence_links
    for link in machine.evidence_links:
        assert link.requirement_field in req.requirements
        assert link.clause_id
        assert link.model_id
        assert link.result_id
        assert link.artifact_ref

    first = machine.evidence_links[0]
    assert "->" not in first.artifact_ref


def test_review_checklist_generation_includes_required_items():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix, calc, nc = _build_inputs(prompt)

    _, machine = generate_compliance_dossier(
        req,
        design_basis,
        matrix,
        calc,
        nc,
        now_utc=FIXED_NOW,
    )

    ids = [item.item_id for item in machine.review_checklist]
    assert ids == ["CHK-001", "CHK-002", "CHK-003"]

    defaults_item = next(item for item in machine.review_checklist if item.item_id == "CHK-003")
    assert defaults_item.required is True
    assert defaults_item.evidence_refs == ["applied_defaults"]


def test_dossier_schema_shapes_include_required_sections():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix, calc, nc = _build_inputs(prompt)

    human, machine = generate_compliance_dossier(
        req,
        design_basis,
        matrix,
        calc,
        nc,
        now_utc=FIXED_NOW,
    )

    human_json = human.to_json_dict()
    machine_json = machine.to_json_dict()

    assert human_json["schema_version"] == "ComplianceDossierHuman.v1"
    assert set(["summary_lines", "clause_matrix_rows", "evidence_trace_lines", "review_checklist_lines"]).issubset(
        human_json
    )

    assert machine_json["schema_version"] == "ComplianceDossierMachine.v1"
    assert machine_json["compliance_matrix_schema_version"] == "ComplianceMatrix.v1"
    assert machine_json["evidence_link_set_schema_version"] == "EvidenceLinkSet.v1"
    assert machine_json["review_checklist_schema_version"] == "ReviewChecklist.v1"
    assert isinstance(machine_json["compliance_matrix"], list)
    assert isinstance(machine_json["evidence_links"], list)
    assert isinstance(machine_json["review_checklist"], list)


def test_handoff_gate_rejects_hash_mismatch():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix, calc, nc = _build_inputs(prompt)

    corrupted_calc = replace(calc, source_requirement_set_hash="bad-hash")

    with pytest.raises(ValueError, match="hash link mismatch"):
        generate_compliance_dossier(
            req,
            design_basis,
            matrix,
            corrupted_calc,
            nc,
            now_utc=FIXED_NOW,
        )


def test_write_compliance_artifacts_persists_canonical_json(tmp_path):
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix, calc, nc = _build_inputs(prompt)

    human, machine = generate_compliance_dossier(
        req,
        design_basis,
        matrix,
        calc,
        nc,
        now_utc=FIXED_NOW,
    )
    human_path, machine_path = write_compliance_artifacts(human, machine, tmp_path)

    assert human_path.exists()
    assert machine_path.exists()

    with human_path.open() as fh:
        human_on_disk = json.load(fh)
    with machine_path.open() as fh:
        machine_on_disk = json.load(fh)

    assert human_on_disk == human.to_json_dict()
    assert machine_on_disk == machine.to_json_dict()
