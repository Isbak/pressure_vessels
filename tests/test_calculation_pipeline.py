import json
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from pressure_vessels.calculation_pipeline import (
    MissingGeometryInputError,
    Quantity,
    SizingCheckInput,
    _MVP_DEFAULTS,
    _round_safety_critical,
    _to_record,
    run_calculation_pipeline,
    write_calculation_artifacts,
)
from pressure_vessels.geometry_module import GEOMETRY_INPUT_VERSION, GeometryInput
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


def _build_inputs_with_external_pressure(prompt: str, pressure_pa: float):
    req, _, _ = _build_inputs(prompt)
    externalized_requirements = dict(req.requirements)
    externalized_requirements["external_pressure"] = RequirementValue(
        value=pressure_pa,
        unit="Pa",
        source_text=f"external pressure {pressure_pa} Pa",
    )
    req_with_external = replace(
        req,
        requirements=externalized_requirements,
    )
    design_basis, matrix = build_design_basis(req_with_external, now_utc=FIXED_NOW)
    return req_with_external, design_basis, matrix


def test_calculation_pipeline_is_deterministic_with_fixed_timestamp():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)

    calc_a, nc_a = run_calculation_pipeline(
        req, design_basis, matrix, now_utc=FIXED_NOW, use_mvp_defaults=True
    )
    calc_b, nc_b = run_calculation_pipeline(
        req, design_basis, matrix, now_utc=FIXED_NOW, use_mvp_defaults=True
    )

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

    calc, non_conformance = run_calculation_pipeline(
        req, design_basis, matrix, now_utc=FIXED_NOW, use_mvp_defaults=True
    )

    assert [record.component for record in calc.checks] == [
        "shell",
        "head",
        "nozzle",
        "shell",
        "head",
        "nozzle",
        "nozzle",
        "nozzle",
    ]
    assert [record.clause_id for record in calc.checks] == [
        "UG-27",
        "UG-32",
        "UG-45",
        "UG-27",
        "UG-32",
        "UG-45",
        "UG-37",
        "UG-37",
    ]
    assert [record.pass_status for record in calc.checks] == [True, True, False, True, True, False, False, False]
    for record in calc.checks:
        assert record.utilization_ratio > 0.0
        assert record.near_limit_threshold == 0.9

    assert len(non_conformance.entries) == 4
    assert [entry.check_id for entry in non_conformance.entries] == [
        "UG-45-nozzle",
        "UG-45-nozzle-mawp",
        "UG-37-nozzle-shell-reinforcement",
        "UG-37-nozzle-head-reinforcement",
    ]
    assert [entry.clause_id for entry in non_conformance.entries] == ["UG-45", "UG-45", "UG-37", "UG-37"]
    assert [entry.component for entry in non_conformance.entries] == ["nozzle", "nozzle", "nozzle", "nozzle"]
    assert non_conformance.entries[0].required.startswith("minimum=")
    assert non_conformance.entries[1].required.startswith("minimum_design_pressure=")


def test_artifact_links_requirement_design_basis_and_applicability_matrix():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)

    calc, _ = run_calculation_pipeline(req, design_basis, matrix, now_utc=FIXED_NOW, use_mvp_defaults=True)

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

    with pytest.warns(UserWarning, match="MVP geometry defaults for missing fields"):
        calc, _ = run_calculation_pipeline(
            req, design_basis, matrix, now_utc=FIXED_NOW, use_mvp_defaults=True
        )

    assert calc.applied_defaults["applied_mvp_defaults"] is True
    assert calc.applied_defaults["applied_geometry_defaults"] is True
    assert calc.applied_defaults["non_production_flag"] is True
    assert calc.applied_defaults["audit_event"]["event_type"] == "non_production_mvp_defaults_opt_in"
    values = calc.applied_defaults["values"]
    assert "allowable_stress_Pa" not in values
    assert "joint_efficiency" not in values
    assert "source" in calc.applied_defaults
    assert calc.applied_defaults["material_source"] == "materials_module.resolve_material_basis"
    assert calc.applied_defaults["corrosion_allowance_policy"]["policy_id"] == "CA-INPUT-REQUIREMENT"
    assert calc.material_basis["allowable_stress_pa"] == 138_000_000.0
    assert calc.material_basis["joint_efficiency"] == 0.85
    assert calc.material_basis["standards_package_ref"] == "ASME Section VIII Division 1:ASME_BPVC_2023"
    assert calc.material_basis["standards_package_id"] == "ASME_BPVC_2023_MATERIALS_2026-04"
    assert calc.material_basis["effective_date"] == "2026-04-01"


def test_missing_geometry_input_raises_without_explicit_opt_in():
    req, design_basis, matrix = _build_inputs(
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    with pytest.raises(MissingGeometryInputError, match="missing fields: shell_inside_diameter_m"):
        run_calculation_pipeline(req, design_basis, matrix, now_utc=FIXED_NOW)


def test_explicit_mvp_defaults_opt_in_uses_expected_values_and_emits_warning():
    req, design_basis, matrix = _build_inputs(
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    with pytest.warns(UserWarning, match="MVP geometry defaults for missing fields"):
        calc, _ = run_calculation_pipeline(
            req, design_basis, matrix, now_utc=FIXED_NOW, use_mvp_defaults=True
        )

    assert calc.applied_defaults["audit_event"]["event_id"] == "BL-003-MVP-GEOMETRY-DEFAULTS-NON-PRODUCTION"
    assert "NON-PRODUCTION ONLY" in calc.applied_defaults["audit_event"]["message"]
    assert calc.applied_defaults["values"]["shell_inside_diameter_m"] == _MVP_DEFAULTS["shell_inside_diameter_m"]
    assert calc.applied_defaults["values"]["shell_provided_thickness_m"] == _MVP_DEFAULTS["shell_provided_thickness_m"]
    assert calc.applied_defaults["values"]["head_inside_diameter_m"] == _MVP_DEFAULTS["head_inside_diameter_m"]
    assert calc.applied_defaults["values"]["head_provided_thickness_m"] == _MVP_DEFAULTS["head_provided_thickness_m"]
    assert calc.applied_defaults["values"]["nozzle_inside_diameter_m"] == _MVP_DEFAULTS["nozzle_inside_diameter_m"]
    assert calc.applied_defaults["values"]["nozzle_provided_thickness_m"] == _MVP_DEFAULTS["nozzle_provided_thickness_m"]


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
    assert calc.applied_defaults["non_production_flag"] is False
    assert calc.applied_defaults["values"] == {}
    assert calc.material_basis["material_spec"] == "SA-516 Gr.70"
    assert calc.geometry_basis["source"] == "sizing_input"
    assert calc.cad_ready_parameter_export is None


def test_geometry_input_adapter_drives_deterministic_shell_head_nozzle_inputs():
    req, design_basis, matrix = _build_inputs(
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    geometry_input = GeometryInput(
        schema_version=GEOMETRY_INPUT_VERSION,
        geometry_revision_id="REV-2026-04-18-A",
        source_system="cad-system",
        source_model_sha256="a" * 64,
        shell_inside_diameter_m=2.4,
        shell_provided_thickness_m=0.022,
        head_inside_diameter_m=2.4,
        head_provided_thickness_m=0.020,
        nozzle_inside_diameter_m=0.30,
        nozzle_provided_thickness_m=0.007,
    )
    calc, _ = run_calculation_pipeline(
        req,
        design_basis,
        matrix,
        geometry_input=geometry_input,
        strict_sizing_input_gate=True,
        now_utc=FIXED_NOW,
    )

    shell = next(record for record in calc.checks if record.check_id == "UG-27-shell")
    assert shell.inputs["D_m"] == 2.4
    assert calc.applied_defaults["applied_mvp_defaults"] is False
    assert calc.geometry_basis["geometry_revision_id"] == "REV-2026-04-18-A"
    assert calc.cad_ready_parameter_export is not None
    assert calc.cad_ready_parameter_export["source_calculation_records_hash"] == calc.deterministic_hash


def test_strict_sizing_input_gate_fails_closed_when_geometry_and_sizing_inputs_missing():
    req, design_basis, matrix = _build_inputs(
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    with pytest.raises(ValueError, match="BL-014 strict sizing-input gate failed"):
        run_calculation_pipeline(
            req,
            design_basis,
            matrix,
            strict_sizing_input_gate=True,
            now_utc=FIXED_NOW,
        )


def test_corrosion_policy_fallback_is_explicit_when_requirement_is_absent():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1."
    )
    req, design_basis, matrix = _build_inputs(prompt)

    calc, _ = run_calculation_pipeline(req, design_basis, matrix, now_utc=FIXED_NOW, use_mvp_defaults=True)

    assert calc.material_basis["corrosion_allowance_policy"]["policy_id"] == "CA-DEFAULT-MM"
    assert calc.material_basis["corrosion_allowance_m"] == 0.0015


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

    calc, _ = run_calculation_pipeline(req, design_basis, matrix, now_utc=FIXED_NOW, use_mvp_defaults=True)

    hashes = [record.reproducibility.canonical_payload_sha256 for record in calc.checks]
    assert len(set(hashes)) == len(hashes)
    assert all(len(value) == 64 for value in hashes)
    assert all(record.validity_envelope is not None for record in calc.checks)


def test_validity_envelope_metadata_is_deterministic_and_model_declared():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)

    calc_a, _ = run_calculation_pipeline(req, design_basis, matrix, now_utc=FIXED_NOW, use_mvp_defaults=True)
    calc_b, _ = run_calculation_pipeline(req, design_basis, matrix, now_utc=FIXED_NOW, use_mvp_defaults=True)
    assert calc_a.to_json_dict() == calc_b.to_json_dict()

    shell = next(record for record in calc_a.checks if record.check_id == "UG-27-shell")
    assert shell.validity_envelope == {
        "model_id": "ug27_shell_thickness_v1",
        "status": "in_envelope",
        "bounds": {
            "internal_pressure_pa": {"min": 1.0, "max": 20_000_000.0},
            "allowable_stress_pa": {"min": 50_000_000.0, "max": 500_000_000.0},
            "joint_efficiency": {"min": 0.5, "max": 1.0},
            "shell_inside_diameter_m": {"min": 0.25, "max": 8.0},
            "corrosion_allowance_m": {"min": 0.0, "max": 0.02},
        },
        "evaluated_inputs": {
            "internal_pressure_pa": 1_800_000.0,
            "allowable_stress_pa": 138_000_000.0,
            "joint_efficiency": 0.85,
            "shell_inside_diameter_m": 2.0,
            "corrosion_allowance_m": 0.003,
        },
    }


def test_margin_utilization_outputs_are_deterministic():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)

    calc_a, _ = run_calculation_pipeline(req, design_basis, matrix, now_utc=FIXED_NOW, use_mvp_defaults=True)
    calc_b, _ = run_calculation_pipeline(req, design_basis, matrix, now_utc=FIXED_NOW, use_mvp_defaults=True)
    assert calc_a.to_json_dict() == calc_b.to_json_dict()

    shell = next(record for record in calc_a.checks if record.check_id == "UG-27-shell")
    assert shell.margin_m == 0.001512132
    assert shell.utilization_ratio == 0.9243934
    assert shell.is_near_limit is True
    assert shell.near_limit_threshold == 0.9


def test_round_safety_critical_helper_pins_nine_decimal_policy():
    assert _round_safety_critical(0.1234567894) == 0.123456789
    assert _round_safety_critical(0.1234567896) == 0.12345679
    assert _round_safety_critical(123.0000000004) == 123.0


def test_rounding_policy_stabilizes_boundary_sensitive_pass_fail():
    record = _to_record(
        check_id="UG-27-shell",
        component="shell",
        formula="boundary-test",
        inputs={"P_Pa": 1_800_000.0, "S_Pa": 138_000_000.0, "E": 0.85, "D_m": 2.0, "CA_m": 0.003},
        required=1.0000000004,
        provided=1.0000000003,
    )

    assert record.required_thickness_m == 1.0
    assert record.provided_thickness_m == 1.0
    assert record.margin_m == 0.0
    assert record.utilization_ratio == 1.0
    assert record.utilization_invalid_reason is None
    assert record.pass_status is True


def test_non_positive_provided_thickness_marks_utilization_as_invalid():
    record = _to_record(
        check_id="UG-27-shell",
        component="shell",
        formula="invalid-utilization-test",
        inputs={"P_Pa": 1_800_000.0, "S_Pa": 138_000_000.0, "E": 0.85, "D_m": 2.0, "CA_m": 0.003},
        required=0.01,
        provided=0.0,
        near_limit_threshold=0.5,
    )

    assert record.pass_status is False
    assert record.utilization_ratio is None
    assert record.utilization_invalid_reason == "provided_thickness_non_positive"
    assert record.is_near_limit is False


def test_negative_provided_thickness_does_not_trigger_near_limit_threshold():
    record = _to_record(
        check_id="UG-27-shell",
        component="shell",
        formula="invalid-utilization-test",
        inputs={"P_Pa": 1_800_000.0, "S_Pa": 138_000_000.0, "E": 0.85, "D_m": 2.0, "CA_m": 0.003},
        required=0.01,
        provided=-0.005,
        near_limit_threshold=0.01,
    )

    assert record.pass_status is False
    assert record.utilization_ratio is None
    assert record.utilization_invalid_reason == "provided_thickness_non_positive"
    assert record.is_near_limit is False


def test_near_limit_threshold_is_configurable_and_persisted_on_records():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)

    calc, _ = run_calculation_pipeline(
        req,
        design_basis,
        matrix,
        now_utc=FIXED_NOW,
        near_limit_threshold=0.95,
        use_mvp_defaults=True,
    )
    shell = next(record for record in calc.checks if record.check_id == "UG-27-shell")
    assert shell.near_limit_threshold == 0.95
    assert shell.is_near_limit is False


def test_near_limit_fields_are_clause_linked_and_hashed_in_reproducibility_metadata():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)
    calc_default, _ = run_calculation_pipeline(req, design_basis, matrix, now_utc=FIXED_NOW, use_mvp_defaults=True)
    calc_tuned, _ = run_calculation_pipeline(
        req, design_basis, matrix, now_utc=FIXED_NOW, near_limit_threshold=0.95, use_mvp_defaults=True
    )

    shell_default = next(record for record in calc_default.checks if record.check_id == "UG-27-shell")
    shell_tuned = next(record for record in calc_tuned.checks if record.check_id == "UG-27-shell")
    assert shell_default.clause_id == "UG-27"
    assert shell_tuned.clause_id == "UG-27"
    assert (
        shell_default.reproducibility.canonical_payload_sha256
        != shell_tuned.reproducibility.canonical_payload_sha256
    )


def test_mawp_outputs_are_deterministic_and_clause_linked():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)

    calc, _ = run_calculation_pipeline(req, design_basis, matrix, now_utc=FIXED_NOW, use_mvp_defaults=True)
    mawp_checks = [record for record in calc.checks if record.check_id.endswith("-mawp")]

    assert [record.check_id for record in mawp_checks] == [
        "UG-27-shell-mawp",
        "UG-32-head-mawp",
        "UG-45-nozzle-mawp",
    ]
    assert [record.clause_id for record in mawp_checks] == ["UG-27", "UG-32", "UG-45"]
    assert [record.design_pressure_pa for record in mawp_checks] == [1_800_000.0, 1_800_000.0, 1_800_000.0]
    assert [record.pass_status for record in mawp_checks] == [True, True, False]
    assert [record.computed_mawp_pa for record in mawp_checks] == [
        1973965.551375965,
        1984771.573604061,
        668757.126567845,
    ]
    assert [record.pressure_margin_pa for record in mawp_checks] == [
        173965.551375965,
        184771.573604061,
        -1131242.873432155,
    ]
    assert all(record.reproducibility.hash_algorithm == "sha256" for record in mawp_checks)


def test_external_pressure_checks_run_only_when_external_pressure_is_declared():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )

    req, design_basis, matrix = _build_inputs(prompt)
    calc_no_external, _ = run_calculation_pipeline(req, design_basis, matrix, now_utc=FIXED_NOW, use_mvp_defaults=True)
    assert [record.check_id for record in calc_no_external.checks if record.check_id.startswith("UG-28")] == []

    req_ext, design_basis_ext, matrix_ext = _build_inputs_with_external_pressure(
        prompt, pressure_pa=5_000.0
    )
    calc_with_external, _ = run_calculation_pipeline(
        req_ext,
        design_basis_ext,
        matrix_ext,
        now_utc=FIXED_NOW,
        use_mvp_defaults=True,
    )
    assert [record.check_id for record in calc_with_external.checks if record.check_id.startswith("UG-28")] == [
        "UG-28-shell-external",
        "UG-28-head-external",
    ]


def test_reinforcement_outputs_are_deterministic_clause_linked_and_parent_linked():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)

    calc_a, _ = run_calculation_pipeline(req, design_basis, matrix, now_utc=FIXED_NOW, use_mvp_defaults=True)
    calc_b, _ = run_calculation_pipeline(req, design_basis, matrix, now_utc=FIXED_NOW, use_mvp_defaults=True)
    assert calc_a.to_json_dict() == calc_b.to_json_dict()

    reinforcement_checks = [record for record in calc_a.checks if record.check_id.startswith("UG-37-")]
    assert [record.check_id for record in reinforcement_checks] == [
        "UG-37-nozzle-shell-reinforcement",
        "UG-37-nozzle-head-reinforcement",
    ]
    assert [record.clause_id for record in reinforcement_checks] == ["UG-37", "UG-37"]
    assert [record.parent_component for record in reinforcement_checks] == ["shell", "head"]
    assert [record.parent_check_id for record in reinforcement_checks] == ["UG-27-shell", "UG-32-head"]
    assert all(record.reproducibility.hash_algorithm == "sha256" for record in reinforcement_checks)
    assert all(len(record.reproducibility.canonical_payload_sha256) == 64 for record in reinforcement_checks)


def test_external_pressure_outputs_are_deterministic_and_clause_linked():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req_ext, design_basis_ext, matrix_ext = _build_inputs_with_external_pressure(
        prompt, pressure_pa=5_000.0
    )

    calc_a, nc_a = run_calculation_pipeline(
        req_ext, design_basis_ext, matrix_ext, now_utc=FIXED_NOW, use_mvp_defaults=True
    )
    calc_b, nc_b = run_calculation_pipeline(
        req_ext, design_basis_ext, matrix_ext, now_utc=FIXED_NOW, use_mvp_defaults=True
    )
    assert calc_a.to_json_dict() == calc_b.to_json_dict()
    assert nc_a.to_json_dict() == nc_b.to_json_dict()

    ug28 = [record for record in calc_a.checks if record.check_id.startswith("UG-28")]
    assert [record.clause_id for record in ug28] == ["UG-28", "UG-28"]
    assert all(record.reproducibility.hash_algorithm == "sha256" for record in ug28)
    assert all(len(record.reproducibility.canonical_payload_sha256) == 64 for record in ug28)
    assert [record.pass_status for record in ug28] == [True, True]
    assert [record.design_pressure_pa for record in ug28] == [5_000.0, 5_000.0]
    assert [record.pressure_margin_pa for record in ug28] == [
        35671.721611722,
        22197.802197802,
    ]


def test_external_pressure_failures_feed_non_conformance_with_clause_linkage():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req_ext, design_basis_ext, matrix_ext = _build_inputs_with_external_pressure(prompt, pressure_pa=50_000.0)
    calc, non_conformance = run_calculation_pipeline(
        req_ext, design_basis_ext, matrix_ext, now_utc=FIXED_NOW, use_mvp_defaults=True
    )

    ug28_failures = [record for record in calc.checks if record.check_id.startswith("UG-28")]
    assert [record.pass_status for record in ug28_failures] == [False, False]
    failed_entry = next(entry for entry in non_conformance.entries if entry.check_id == "UG-28-head-external")
    assert failed_entry.clause_id == "UG-28"
    assert failed_entry.observed.startswith("allowable_pressure=")
    assert failed_entry.required == "minimum_design_pressure=50000.000 Pa"
    failed_check = next(record for record in calc.checks if record.check_id == "UG-28-head-external")
    assert failed_check.pass_status is False
    assert failed_check.is_near_limit is False


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
        run_calculation_pipeline(corrupted, design_basis, matrix, now_utc=FIXED_NOW, use_mvp_defaults=True)


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
        run_calculation_pipeline(req_a, design_basis_a, matrix_b, now_utc=FIXED_NOW, use_mvp_defaults=True)


def test_model_domain_gate_rejects_out_of_range_joint_efficiency():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)

    invalid = SizingCheckInput(
        internal_pressure=Quantity(value=1.8, unit="MPa"),
        allowable_stress=Quantity(value=138.0, unit="MPa"),
        joint_efficiency=1.1,
        corrosion_allowance=Quantity(value=3.0, unit="mm"),
        shell_inside_diameter=Quantity(value=2.0, unit="m"),
        shell_provided_thickness=Quantity(value=20.0, unit="mm"),
        head_inside_diameter=Quantity(value=2.0, unit="m"),
        head_provided_thickness=Quantity(value=18.0, unit="mm"),
        nozzle_inside_diameter=Quantity(value=0.35, unit="m"),
        nozzle_provided_thickness=Quantity(value=4.0, unit="mm"),
    )

    with pytest.raises(ValueError, match="model-domain gate failed"):
        run_calculation_pipeline(
            req,
            design_basis,
            matrix,
            sizing_input=invalid,
            now_utc=FIXED_NOW,
        )


def test_model_domain_gate_fails_closed_when_validity_envelope_is_violated():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)

    out_of_envelope = SizingCheckInput(
        internal_pressure=Quantity(value=1.8, unit="MPa"),
        allowable_stress=Quantity(value=138.0, unit="MPa"),
        joint_efficiency=0.85,
        corrosion_allowance=Quantity(value=3.0, unit="mm"),
        shell_inside_diameter=Quantity(value=9.0, unit="m"),
        shell_provided_thickness=Quantity(value=20.0, unit="mm"),
        head_inside_diameter=Quantity(value=2.0, unit="m"),
        head_provided_thickness=Quantity(value=18.0, unit="mm"),
        nozzle_inside_diameter=Quantity(value=0.35, unit="m"),
        nozzle_provided_thickness=Quantity(value=4.0, unit="mm"),
    )

    with pytest.raises(ValueError, match="outside validity envelope"):
        run_calculation_pipeline(
            req,
            design_basis,
            matrix,
            sizing_input=out_of_envelope,
            now_utc=FIXED_NOW,
        )


def test_clause_linkage_and_non_conformance_behavior_remain_compatible_with_validity_metadata():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)
    calc, non_conformance = run_calculation_pipeline(
        req, design_basis, matrix, now_utc=FIXED_NOW, use_mvp_defaults=True
    )

    failed_check = next(record for record in calc.checks if record.check_id == "UG-45-nozzle")
    failed_entry = next(entry for entry in non_conformance.entries if entry.check_id == "UG-45-nozzle")
    assert failed_check.clause_id == failed_entry.clause_id == "UG-45"
    assert failed_check.validity_envelope["status"] == "in_envelope"
    assert failed_check.reproducibility.hash_algorithm == "sha256"


def test_model_domain_gate_rejects_invalid_near_limit_threshold():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)

    with pytest.raises(ValueError, match="near_limit_threshold"):
        run_calculation_pipeline(
            req,
            design_basis,
            matrix,
            now_utc=FIXED_NOW,
            near_limit_threshold=1.2,
            use_mvp_defaults=True,
        )


def test_write_calculation_artifacts_persists_canonical_json(tmp_path):
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    req, design_basis, matrix = _build_inputs(prompt)

    calc, nc = run_calculation_pipeline(req, design_basis, matrix, now_utc=FIXED_NOW, use_mvp_defaults=True)
    calc_path, nc_path = write_calculation_artifacts(calc, nc, tmp_path)

    assert calc_path.exists()
    assert nc_path.exists()

    with calc_path.open() as fh:
        calc_on_disk = json.load(fh)
    with nc_path.open() as fh:
        nc_on_disk = json.load(fh)

    assert calc_on_disk == calc.to_json_dict()
    assert nc_on_disk == nc.to_json_dict()
