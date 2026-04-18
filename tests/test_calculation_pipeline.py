import json
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from pressure_vessels.calculation_pipeline import (
    Quantity,
    SizingCheckInput,
    run_calculation_pipeline,
    write_calculation_artifacts,
)
from pressure_vessels.design_basis_pipeline import build_design_basis
from pressure_vessels.requirements_pipeline import (
    RequirementValue,
    parse_prompt_to_requirement_set,
)

FIXED_NOW = datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc)


def _build_inputs(prompt: str):
    req = parse_prompt_to_requirement_set(prompt, now_utc=FIXED_NOW)
    design_basis, matrix = build_design_basis(req, now_utc=FIXED_NOW)
    return req, design_basis, matrix


def test_calculation_pipeline_is_deterministic_with_fixed_timestamp():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)

    calc_a, nc_a = run_calculation_pipeline(req, design_basis, matrix, now_utc=FIXED_NOW)
    calc_b, nc_b = run_calculation_pipeline(req, design_basis, matrix, now_utc=FIXED_NOW)

    assert calc_a.to_json_dict() == calc_b.to_json_dict()
    assert nc_a.to_json_dict() == nc_b.to_json_dict()
    assert calc_a.deterministic_hash == calc_b.deterministic_hash
    assert nc_a.deterministic_hash == nc_b.deterministic_hash


def test_calculation_pipeline_generates_expected_pass_fail_and_non_conformance():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)

    calc, non_conformance = run_calculation_pipeline(req, design_basis, matrix, now_utc=FIXED_NOW)

    assert [record.component for record in calc.checks] == ["shell", "head", "nozzle"]
    assert [record.clause_id for record in calc.checks] == ["UG-27", "UG-32", "UG-45"]
    assert [record.pass_status for record in calc.checks] == [True, True, False]
    for record in calc.checks:
        assert record.utilization_ratio > 0.0

    assert len(non_conformance.entries) == 1
    entry = non_conformance.entries[0]
    assert entry.check_id == "UG-45-nozzle"
    assert entry.clause_id == "UG-45"
    assert entry.component == "nozzle"
    assert "minimum=" in entry.required


def test_artifact_links_requirement_design_basis_and_applicability_matrix():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)

    calc, _ = run_calculation_pipeline(req, design_basis, matrix, now_utc=FIXED_NOW)

    assert calc.source_requirement_set_hash == req.deterministic_hash
    assert calc.source_design_basis_signature == design_basis.deterministic_signature
    assert calc.source_applicability_matrix_hash == matrix.deterministic_hash


def test_applied_defaults_are_surfaced_when_sizing_input_is_absent():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)

    calc, _ = run_calculation_pipeline(req, design_basis, matrix, now_utc=FIXED_NOW)

    assert calc.applied_defaults["applied_mvp_defaults"] is True
    values = calc.applied_defaults["values"]
    assert values["allowable_stress_Pa"] == 138_000_000.0
    assert values["joint_efficiency"] == 0.85
    assert "source" in calc.applied_defaults


def test_applied_defaults_are_not_flagged_when_caller_supplies_sizing_input():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)

    sizing_input = SizingCheckInput(
        internal_pressure=Quantity(value=1.8, unit="MPa"),
        allowable_stress=Quantity(value=138.0, unit="MPa"),
        joint_efficiency=0.85,
        corrosion_allowance=Quantity(value=3.0, unit="mm"),
        shell_inside_diameter=Quantity(value=200.0, unit="cm"),
        shell_provided_thickness=Quantity(value=20.0, unit="mm"),
        head_inside_diameter=Quantity(value=2.0, unit="m"),
        head_provided_thickness=Quantity(value=18.0, unit="mm"),
        nozzle_inside_diameter=Quantity(value=35.0, unit="cm"),
        nozzle_provided_thickness=Quantity(value=4.0, unit="mm"),
    )

    calc, _ = run_calculation_pipeline(
        req, design_basis, matrix, sizing_input=sizing_input, now_utc=FIXED_NOW
    )

    assert calc.applied_defaults["applied_mvp_defaults"] is False
    assert calc.applied_defaults["values"] == {}


def test_unit_normalization_supports_non_si_inputs():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)

    sizing_input = SizingCheckInput(
        internal_pressure=Quantity(value=1.8, unit="MPa"),
        allowable_stress=Quantity(value=138.0, unit="MPa"),
        joint_efficiency=0.85,
        corrosion_allowance=Quantity(value=3.0, unit="mm"),
        shell_inside_diameter=Quantity(value=200.0, unit="cm"),
        shell_provided_thickness=Quantity(value=20.0, unit="mm"),
        head_inside_diameter=Quantity(value=2.0, unit="m"),
        head_provided_thickness=Quantity(value=16.0, unit="mm"),
        nozzle_inside_diameter=Quantity(value=35.0, unit="cm"),
        nozzle_provided_thickness=Quantity(value=4.0, unit="mm"),
    )

    calc, _ = run_calculation_pipeline(
        req, design_basis, matrix, sizing_input=sizing_input, now_utc=FIXED_NOW
    )

    shell = next(record for record in calc.checks if record.component == "shell")
    assert shell.inputs["P_Pa"] == 1_800_000.0
    assert shell.inputs["D_m"] == 2.0


def test_check_reproducibility_hashes_are_stable_for_canonical_payload():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)

    calc, _ = run_calculation_pipeline(req, design_basis, matrix, now_utc=FIXED_NOW)

    hashes = [record.reproducibility.canonical_payload_sha256 for record in calc.checks]
    assert len(set(hashes)) == len(hashes)
    assert all(len(value) == 64 for value in hashes)


def test_handoff_gate_rejects_non_canonical_unit():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)

    corrupted_requirements = dict(req.requirements)
    corrupted_requirements["design_temperature"] = RequirementValue(
        value=65.0,
        unit="F",  # wrong canonical unit; policy mandates "C"
        source_text="65F (forced)",
    )
    corrupted = replace(req, requirements=corrupted_requirements)

    with pytest.raises(ValueError, match="design_temperature"):
        run_calculation_pipeline(corrupted, design_basis, matrix, now_utc=FIXED_NOW)


def test_handoff_gate_rejects_mismatched_applicability_matrix():
    prompt_a = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    prompt_b = (
        "Design a horizontal pressure vessel for ammonia storage, "
        "20 bar design pressure, 40°C design temperature, 25 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req_a, design_basis_a, _ = _build_inputs(prompt_a)
    _, _, matrix_b = _build_inputs(prompt_b)

    with pytest.raises(ValueError, match="applicability_matrix"):
        run_calculation_pipeline(req_a, design_basis_a, matrix_b, now_utc=FIXED_NOW)


def test_write_calculation_artifacts_persists_canonical_json(tmp_path):
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)

    calc, nc = run_calculation_pipeline(req, design_basis, matrix, now_utc=FIXED_NOW)
    calc_path, nc_path = write_calculation_artifacts(calc, nc, tmp_path)

    assert calc_path.exists()
    assert nc_path.exists()

    with calc_path.open() as fh:
        calc_on_disk = json.load(fh)
    with nc_path.open() as fh:
        nc_on_disk = json.load(fh)

    assert calc_on_disk == calc.to_json_dict()
    assert nc_on_disk == nc.to_json_dict()
