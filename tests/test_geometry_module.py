import pytest

from pressure_vessels.geometry_module import (
    CAD_PARAMETER_EXPORT_VERSION,
    GEOMETRY_INPUT_VERSION,
    GeometryInput,
    GeometryInputValidationError,
    adapt_geometry_input,
    build_cad_ready_parameter_export,
)


def _valid_geometry_input(**overrides):
    payload = {
        "schema_version": GEOMETRY_INPUT_VERSION,
        "geometry_revision_id": "REV-2026-04-20-A",
        "source_system": "cad-system",
        "source_model_sha256": "a" * 64,
        "shell_inside_diameter_m": 2.4,
        "shell_provided_thickness_m": 0.022,
        "head_inside_diameter_m": 2.4,
        "head_provided_thickness_m": 0.020,
        "nozzle_inside_diameter_m": 0.30,
        "nozzle_provided_thickness_m": 0.007,
        "external_pressure_pa": 10_000.0,
    }
    payload.update(overrides)
    return GeometryInput(**payload)


def test_adapt_geometry_input_raises_typed_error_for_non_numeric_and_null_fields():
    geometry_input = _valid_geometry_input(
        shell_inside_diameter_m="not-a-number",
        head_inside_diameter_m=None,
    )

    with pytest.raises(GeometryInputValidationError) as exc_info:
        adapt_geometry_input(geometry_input)

    assert exc_info.value.failures == {
        "head_inside_diameter_m": "null value is not allowed.",
        "shell_inside_diameter_m": "non-numeric value 'not-a-number'.",
    }


def test_adapt_geometry_input_raises_typed_error_for_out_of_range_fields():
    geometry_input = _valid_geometry_input(
        shell_provided_thickness_m=0.0,
        external_pressure_pa=-1.0,
    )

    with pytest.raises(GeometryInputValidationError) as exc_info:
        adapt_geometry_input(geometry_input)

    assert exc_info.value.failures == {
        "external_pressure_pa": "out-of-range value -1.0; expected >= 0.",
        "shell_provided_thickness_m": "out-of-range value 0.0; expected > 0.",
    }


def test_build_cad_export_routes_through_geometry_validation():
    geometry_input = _valid_geometry_input(nozzle_provided_thickness_m="bad")

    with pytest.raises(GeometryInputValidationError, match="nozzle_provided_thickness_m"):
        build_cad_ready_parameter_export(geometry_input, calculation_records_hash="b" * 64)


def test_valid_geometry_inputs_preserve_happy_path_behavior():
    geometry_input = _valid_geometry_input()

    payload = adapt_geometry_input(geometry_input)
    export = build_cad_ready_parameter_export(geometry_input, calculation_records_hash="b" * 64)

    assert payload["shell_inside_diameter_m"] == 2.4
    assert payload["external_pressure_pa"] == 10_000.0
    assert export.schema_version == CAD_PARAMETER_EXPORT_VERSION
    assert export.parameters["head_inside_diameter_m"] == 2.4
    assert export.parameters["external_pressure_pa"] == 10_000.0
