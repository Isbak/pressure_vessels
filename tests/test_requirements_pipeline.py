from datetime import datetime, timezone

from pressure_vessels.requirements_pipeline import parse_prompt_to_requirement_set


def test_parse_success_path_generates_no_gaps_and_not_blocked():
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    result = parse_prompt_to_requirement_set(
        prompt,
        now_utc=datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc),
    )

    assert result.downstream_blocked is False
    assert result.unresolved_gaps == []
    assert result.requirements["fluid"].value == "propane"
    assert result.requirements["design_pressure"].value == 1800000.0
    assert result.requirements["design_pressure"].unit == "Pa"
    assert result.requirements["design_temperature"].value == 65.0
    assert result.requirements["capacity"].value == 30.0
    assert result.requirements["code_standard"].value == "ASME SECTION VIII DIV 1"
    assert result.deterministic_hash == "0c5e80aae1430f1ee835da7d30f16dd1c354207fea3a5de9be552a6e30909adc"


def test_missing_mandatory_fields_produce_gap_list_and_block_downstream():
    prompt = "Need a vessel for water storage, 20 m3 capacity."
    result = parse_prompt_to_requirement_set(
        prompt,
        now_utc=datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc),
    )

    assert result.downstream_blocked is True
    gap_fields = {gap.field for gap in result.unresolved_gaps}
    assert gap_fields == {"design_pressure", "design_temperature", "code_standard"}


def test_unit_normalization_across_supported_dimensions():
    prompt = (
        "Design vessel for ammonia storage, design pressure 300 psi, "
        "design temperature 122 F, volume 1000 liters, "
        "ASME VIII-1, corrosion allowance 0.25 in"
    )
    result = parse_prompt_to_requirement_set(
        prompt,
        now_utc=datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc),
    )

    assert result.requirements["design_pressure"].value == 2068427.18795
    assert result.requirements["design_pressure"].unit == "Pa"
    assert result.requirements["design_temperature"].value == 50.0
    assert result.requirements["design_temperature"].unit == "C"
    assert result.requirements["capacity"].value == 1.0
    assert result.requirements["capacity"].unit == "m3"
    assert result.requirements["corrosion_allowance"].value == 6.35
    assert result.requirements["corrosion_allowance"].unit == "mm"
