from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from pressure_vessels.calculation_pipeline import Quantity, SizingCheckInput, run_calculation_pipeline
from pressure_vessels.design_basis_pipeline import build_design_basis
from pressure_vessels.requirements_pipeline import RequirementValue, parse_prompt_to_requirement_set

FIXED_NOW = datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc)
PROMPT = (
    "Design a horizontal pressure vessel for propane storage, "
    "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
    "ASME Section VIII Div 1, corrosion allowance 3 mm."
)


def _build_handoff_inputs(include_external_pressure: bool = False):
    requirement_set = parse_prompt_to_requirement_set(PROMPT, now_utc=FIXED_NOW)
    if include_external_pressure:
        requirements = dict(requirement_set.requirements)
        requirements["external_pressure"] = RequirementValue(
            value=100_000.0,
            unit="Pa",
            source_text="external pressure 100000 Pa",
        )
        requirement_set = replace(requirement_set, requirements=requirements)
    design_basis, applicability_matrix = build_design_basis(requirement_set, now_utc=FIXED_NOW)
    return requirement_set, design_basis, applicability_matrix


def _baseline_sizing_input() -> SizingCheckInput:
    return SizingCheckInput(
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
        external_pressure=Quantity(value=100_000.0, unit="Pa"),
    )


def _set_dimension_value(sizing_input: SizingCheckInput, dimension: str, value: float) -> SizingCheckInput:
    if dimension == "joint_efficiency":
        return replace(sizing_input, joint_efficiency=value)

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
    return replace(sizing_input, **{field_name: Quantity(value=value, unit=current.unit)})


BOUNDED_DIMENSIONS = [
    ("internal_pressure_pa", 1.0, 20_000_000.0, 0.001),
    ("allowable_stress_pa", 50_000_000.0, 500_000_000.0, 1.0),
    ("joint_efficiency", 0.5, 1.0, 0.0001),
    ("corrosion_allowance_m", 0.0, 0.02, 0.0001),
    ("shell_inside_diameter_m", 0.25, 8.0, 0.0001),
    ("shell_provided_thickness_m", 0.002, 0.25, 0.0001),
    ("head_inside_diameter_m", 0.25, 8.0, 0.0001),
    ("head_provided_thickness_m", 0.002, 0.25, 0.0001),
    ("nozzle_inside_diameter_m", 0.05, 2.0, 0.0001),
    ("nozzle_provided_thickness_m", 0.001, 0.25, 0.0001),
    ("external_pressure_pa", 1.0, 2_000_000.0, 0.001),
]


@pytest.mark.parametrize("dimension,min_value,max_value,delta", BOUNDED_DIMENSIONS)
def test_envelope_just_inside_values_pass(dimension: str, min_value: float, max_value: float, delta: float):
    include_external = dimension == "external_pressure_pa"
    requirement_set, design_basis, applicability_matrix = _build_handoff_inputs(
        include_external_pressure=include_external
    )

    base = _baseline_sizing_input()
    if not include_external:
        base = replace(base, external_pressure=None)

    for candidate in (min_value + delta, max_value - delta):
        sizing_input = _set_dimension_value(base, dimension, candidate)
        calc, _ = run_calculation_pipeline(
            requirement_set,
            design_basis,
            applicability_matrix,
            sizing_input=sizing_input,
            now_utc=FIXED_NOW,
        )
        expected_checks = 10 if include_external else 8
        assert len(calc.checks) == expected_checks


@pytest.mark.parametrize("dimension,min_value,max_value,delta", BOUNDED_DIMENSIONS)
def test_envelope_just_outside_values_fail_with_validity_exception(
    dimension: str,
    min_value: float,
    max_value: float,
    delta: float,
):
    include_external = dimension == "external_pressure_pa"
    requirement_set, design_basis, applicability_matrix = _build_handoff_inputs(
        include_external_pressure=include_external
    )

    base = _baseline_sizing_input()
    if not include_external:
        base = replace(base, external_pressure=None)

    outside_values = []
    if min_value > 0.0:
        outside_values.append(min_value - delta)
    else:
        outside_values.append(-delta)
    outside_values.append(max_value + delta)

    for candidate in outside_values:
        sizing_input = _set_dimension_value(base, dimension, candidate)
        expected_error = (
            r"BL-003 model-domain gate failed: joint_efficiency must be in \(0, 1\]."
            if dimension == "joint_efficiency" and candidate > 1.0
            else rf"BL-003 model-domain gate failed: .*{dimension}=.*outside validity envelope"
        )
        with pytest.raises(
            ValueError,
            match=expected_error,
        ):
            run_calculation_pipeline(
                requirement_set,
                design_basis,
                applicability_matrix,
                sizing_input=sizing_input,
                now_utc=FIXED_NOW,
            )


@pytest.mark.parametrize(
    "dimension,zero_invalid,negative_invalid",
    [
        ("internal_pressure_pa", True, True),
        ("allowable_stress_pa", True, True),
        ("joint_efficiency", True, True),
        ("shell_inside_diameter_m", True, True),
        ("head_inside_diameter_m", True, True),
        ("nozzle_inside_diameter_m", True, True),
        ("shell_provided_thickness_m", True, True),
        ("head_provided_thickness_m", True, True),
        ("nozzle_provided_thickness_m", True, True),
        ("external_pressure_pa", True, True),
        ("corrosion_allowance_m", False, True),
    ],
)
def test_zero_and_negative_inputs_fail_for_physically_invalid_cases(
    dimension: str,
    zero_invalid: bool,
    negative_invalid: bool,
):
    include_external = dimension == "external_pressure_pa"
    requirement_set, design_basis, applicability_matrix = _build_handoff_inputs(
        include_external_pressure=include_external
    )

    base = _baseline_sizing_input()
    if not include_external:
        base = replace(base, external_pressure=None)

    if zero_invalid:
        zero_input = _set_dimension_value(base, dimension, 0.0)
        with pytest.raises(ValueError, match="BL-003 model-domain gate failed"):
            run_calculation_pipeline(
                requirement_set,
                design_basis,
                applicability_matrix,
                sizing_input=zero_input,
                now_utc=FIXED_NOW,
            )

    if negative_invalid:
        negative_input = _set_dimension_value(base, dimension, -0.001)
        with pytest.raises(ValueError, match="BL-003 model-domain gate failed"):
            run_calculation_pipeline(
                requirement_set,
                design_basis,
                applicability_matrix,
                sizing_input=negative_input,
                now_utc=FIXED_NOW,
            )
