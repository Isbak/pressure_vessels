from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pressure_vessels.calculation_pipeline import Quantity, SizingCheckInput, run_calculation_pipeline
from pressure_vessels.design_basis_pipeline import build_design_basis
from pressure_vessels.requirements_pipeline import parse_prompt_to_requirement_set

FIXED_NOW = datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc)
PROMPT = (
    "Design a horizontal pressure vessel for propane storage, "
    "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
    "ASME Section VIII Div 1, corrosion allowance 3 mm."
)


def _set_dimension_value(sizing_input: SizingCheckInput, dimension: str, value: float) -> SizingCheckInput:
    if dimension == "joint_efficiency":
        return SizingCheckInput(
            internal_pressure=sizing_input.internal_pressure,
            allowable_stress=sizing_input.allowable_stress,
            joint_efficiency=value,
            corrosion_allowance=sizing_input.corrosion_allowance,
            shell_inside_diameter=sizing_input.shell_inside_diameter,
            shell_provided_thickness=sizing_input.shell_provided_thickness,
            head_inside_diameter=sizing_input.head_inside_diameter,
            head_provided_thickness=sizing_input.head_provided_thickness,
            nozzle_inside_diameter=sizing_input.nozzle_inside_diameter,
            nozzle_provided_thickness=sizing_input.nozzle_provided_thickness,
            external_pressure=sizing_input.external_pressure,
        )

    quantity_field_map = {
        "internal_pressure_pa": "internal_pressure",
        "allowable_stress_pa": "allowable_stress",
        "corrosion_allowance_m": "corrosion_allowance",
        "shell_inside_diameter_m": "shell_inside_diameter",
        "shell_provided_thickness_m": "shell_provided_thickness",
        "head_inside_diameter_m": "head_inside_diameter",
        "head_provided_thickness_m": "head_provided_thickness",
        "nozzle_inside_diameter_m": "nozzle_inside_diameter",
        "nozzle_provided_thickness_m": "nozzle_provided_thickness",
        "external_pressure_pa": "external_pressure",
    }
    field_name = quantity_field_map[dimension]
    current = getattr(sizing_input, field_name)
    if current is None:
        current = Quantity(value=1.0, unit="Pa")
    replacement = Quantity(value=value, unit=current.unit)
    return SizingCheckInput(
        internal_pressure=replacement if field_name == "internal_pressure" else sizing_input.internal_pressure,
        allowable_stress=replacement if field_name == "allowable_stress" else sizing_input.allowable_stress,
        joint_efficiency=sizing_input.joint_efficiency,
        corrosion_allowance=replacement if field_name == "corrosion_allowance" else sizing_input.corrosion_allowance,
        shell_inside_diameter=(
            replacement if field_name == "shell_inside_diameter" else sizing_input.shell_inside_diameter
        ),
        shell_provided_thickness=(
            replacement if field_name == "shell_provided_thickness" else sizing_input.shell_provided_thickness
        ),
        head_inside_diameter=replacement if field_name == "head_inside_diameter" else sizing_input.head_inside_diameter,
        head_provided_thickness=(
            replacement if field_name == "head_provided_thickness" else sizing_input.head_provided_thickness
        ),
        nozzle_inside_diameter=(
            replacement if field_name == "nozzle_inside_diameter" else sizing_input.nozzle_inside_diameter
        ),
        nozzle_provided_thickness=(
            replacement if field_name == "nozzle_provided_thickness" else sizing_input.nozzle_provided_thickness
        ),
        external_pressure=replacement if field_name == "external_pressure" else sizing_input.external_pressure,
    )


@pytest.mark.parametrize(
    "fixture_path",
    sorted(Path("tests/golden_examples").glob("example_*.json")),
    ids=lambda p: p.stem,
)
def test_golden_examples_match_reference_values(fixture_path: Path):
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    requirement_set = parse_prompt_to_requirement_set(PROMPT, now_utc=FIXED_NOW)
    design_basis, applicability_matrix = build_design_basis(requirement_set, now_utc=FIXED_NOW)

    fixture_input = fixture["input"]
    sizing_input = SizingCheckInput(
        internal_pressure=Quantity(value=fixture_input["internal_pressure_pa"], unit="Pa"),
        allowable_stress=Quantity(value=fixture_input["allowable_stress_pa"], unit="Pa"),
        joint_efficiency=fixture_input["joint_efficiency"],
        corrosion_allowance=Quantity(value=fixture_input["corrosion_allowance_m"], unit="m"),
        shell_inside_diameter=Quantity(value=fixture_input["shell_inside_diameter_m"], unit="m"),
        shell_provided_thickness=Quantity(value=fixture_input["shell_provided_thickness_m"], unit="m"),
        head_inside_diameter=Quantity(value=fixture_input["head_inside_diameter_m"], unit="m"),
        head_provided_thickness=Quantity(value=fixture_input["head_provided_thickness_m"], unit="m"),
        nozzle_inside_diameter=Quantity(value=fixture_input["nozzle_inside_diameter_m"], unit="m"),
        nozzle_provided_thickness=Quantity(value=fixture_input["nozzle_provided_thickness_m"], unit="m"),
    )

    calc_artifact, _ = run_calculation_pipeline(
        requirement_set,
        design_basis,
        applicability_matrix,
        sizing_input=sizing_input,
        now_utc=FIXED_NOW,
    )

    checks_by_id = {record.check_id: record for record in calc_artifact.checks}
    tolerance = fixture["tolerance"]

    for check_id, expected in fixture["expected"].items():
        assert check_id in checks_by_id
        actual = checks_by_id[check_id]
        assert actual.pass_status is expected["pass_status"]

        if "required_thickness_m" in expected:
            assert actual.required_thickness_m == pytest.approx(expected["required_thickness_m"], abs=tolerance)
        if "computed_mawp_pa" in expected:
            assert actual.computed_mawp_pa == pytest.approx(expected["computed_mawp_pa"], abs=tolerance)


def test_reject_examples_fail_closed_with_domain_gate_errors():
    fixture = json.loads(Path("tests/golden_examples/reject_envelope_cases.json").read_text(encoding="utf-8"))
    requirement_set = parse_prompt_to_requirement_set(PROMPT, now_utc=FIXED_NOW)
    design_basis, applicability_matrix = build_design_basis(requirement_set, now_utc=FIXED_NOW)

    base_input = SizingCheckInput(
        internal_pressure=Quantity(value=1_800_000.0, unit="Pa"),
        allowable_stress=Quantity(value=138_000_000.0, unit="Pa"),
        joint_efficiency=0.85,
        corrosion_allowance=Quantity(value=0.003, unit="m"),
        shell_inside_diameter=Quantity(value=2.0, unit="m"),
        shell_provided_thickness=Quantity(value=0.02, unit="m"),
        head_inside_diameter=Quantity(value=2.0, unit="m"),
        head_provided_thickness=Quantity(value=0.018, unit="m"),
        nozzle_inside_diameter=Quantity(value=0.35, unit="m"),
        nozzle_provided_thickness=Quantity(value=0.004, unit="m"),
    )

    for reject_case in fixture["cases"]:
        sizing_input = _set_dimension_value(base_input, reject_case["dimension"], reject_case["value"])
        with pytest.raises(ValueError, match=reject_case["expected_error_regex"]):
            run_calculation_pipeline(
                requirement_set,
                design_basis,
                applicability_matrix,
                sizing_input=sizing_input,
                now_utc=FIXED_NOW,
            )
