from datetime import datetime, timezone

from pressure_vessels.calculation_pipeline import Quantity, SizingCheckInput, run_calculation_pipeline
from pressure_vessels.design_basis_pipeline import build_design_basis
from pressure_vessels.requirements_pipeline import parse_prompt_to_requirement_set

FIXED_NOW = datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc)


def _build_inputs(prompt: str):
    req = parse_prompt_to_requirement_set(prompt, now_utc=FIXED_NOW)
    design_basis, _ = build_design_basis(req, now_utc=FIXED_NOW)
    return req, design_basis


def test_calculation_pipeline_is_deterministic_with_fixed_timestamp():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis = _build_inputs(prompt)

    calc_a, nc_a = run_calculation_pipeline(req, design_basis, now_utc=FIXED_NOW)
    calc_b, nc_b = run_calculation_pipeline(req, design_basis, now_utc=FIXED_NOW)

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
    req, design_basis = _build_inputs(prompt)

    calc, non_conformance = run_calculation_pipeline(req, design_basis, now_utc=FIXED_NOW)

    assert [record.component for record in calc.checks] == ["shell", "head", "nozzle"]
    assert [record.pass_status for record in calc.checks] == [True, True, False]

    assert len(non_conformance.entries) == 1
    entry = non_conformance.entries[0]
    assert entry.check_id == "UG-45-nozzle"
    assert entry.component == "nozzle"
    assert "minimum=" in entry.required


def test_unit_normalization_supports_non_si_inputs():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis = _build_inputs(prompt)

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

    calc, _ = run_calculation_pipeline(req, design_basis, sizing_input=sizing_input, now_utc=FIXED_NOW)

    shell = next(record for record in calc.checks if record.component == "shell")
    assert shell.inputs["P_Pa"] == 1_800_000.0
    assert shell.inputs["D_m"] == 2.0


def test_check_reproducibility_hashes_are_stable_for_canonical_payload():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis = _build_inputs(prompt)

    calc, _ = run_calculation_pipeline(req, design_basis, now_utc=FIXED_NOW)

    hashes = [record.reproducibility.canonical_payload_sha256 for record in calc.checks]
    assert len(set(hashes)) == len(hashes)
    assert all(len(value) == 64 for value in hashes)
