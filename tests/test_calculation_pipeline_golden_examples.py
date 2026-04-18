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
