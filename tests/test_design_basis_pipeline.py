from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pytest

from pressure_vessels.design_basis_pipeline import StandardRouteConfig, build_design_basis
from pressure_vessels.requirements_pipeline import Gap, RequirementSet, RequirementValue, parse_prompt_to_requirement_set


FIXED_NOW = datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc)
SIGNATURE_FIXTURE_PATH = Path("tests/fixtures/design_basis_signature_v1_asme_route.json")

def _override_code_standard(requirement_set: RequirementSet, code_standard: str) -> RequirementSet:
    requirements = dict(requirement_set.requirements)
    requirements["code_standard"] = RequirementValue(
        value=code_standard,
        unit=None,
        source_text=f"override:{code_standard}",
    )
    canonical_for_hash = {
        field: {"value": value.value, "unit": value.unit}
        for field, value in sorted(requirements.items(), key=lambda i: i[0])
    }
    deterministic_hash = hashlib.sha256(
        json.dumps(canonical_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return RequirementSet(
        schema_version=requirement_set.schema_version,
        generated_at_utc=requirement_set.generated_at_utc,
        input_prompt=requirement_set.input_prompt,
        requirements=requirements,
        unresolved_gaps=[],
        downstream_blocked=False,
        deterministic_hash=deterministic_hash,
    )



def _valid_requirement_set(*, code_standard: str = "ASME Section VIII Div 1", with_corrosion_allowance: bool = True):
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        f"{code_standard}"
    )
    if with_corrosion_allowance:
        prompt += ", corrosion allowance 3 mm."
    return parse_prompt_to_requirement_set(prompt, now_utc=FIXED_NOW)


def test_build_design_basis_happy_path_generates_artifacts_and_standard_resolution():
    requirement_set = _valid_requirement_set(with_corrosion_allowance=True)

    design_basis, matrix = build_design_basis(requirement_set, now_utc=FIXED_NOW)

    assert design_basis.schema_version == "DesignBasis.v1"
    assert design_basis.generated_at_utc == "2026-04-18T00:00:00+00:00"
    assert design_basis.primary_standard == "ASME Section VIII Division 1"
    assert design_basis.primary_standard_version == "ASME_BPVC_2023"
    assert design_basis.selected_route_id == "route_asme_viii_div1"
    assert design_basis.secondary_standards == ["PED (EN 13445):PED_2014_68_EU_EN13445_2021"]

    assert matrix.schema_version == "ApplicabilityMatrix.v1"
    assert matrix.primary_standard == "ASME Section VIII Division 1"
    assert matrix.selected_route_id == "route_asme_viii_div1"
    assert any(record.clause_id == "UG-28" and record.applicable is False for record in matrix.records)
    assert all(record.standard_route_id == "route_asme_viii_div1" for record in matrix.records)


def test_build_design_basis_supports_ped_route_with_clause_level_traceability():
    requirement_set = _override_code_standard(
        _valid_requirement_set(code_standard="ASME Section VIII Div 1", with_corrosion_allowance=True),
        "PED EN 13445",
    )

    design_basis, matrix = build_design_basis(requirement_set, now_utc=FIXED_NOW)

    assert design_basis.primary_standard == "PED (EN 13445)"
    assert design_basis.primary_standard_version == "PED_2014_68_EU_EN13445_2021"
    assert design_basis.selected_route_id == "route_ped_en13445"
    assert any(record.selected for record in design_basis.route_selection_audit)
    assert all(record.standard_route_id == "route_ped_en13445" for record in matrix.records)
    assert all(record.evidence_fields for record in matrix.records)
    assert {record.clause_id for record in matrix.records} == {
        "PED-Article-4",
        "EN13445-3-6.2",
        "EN13445-3-6.6",
        "PED-Annex-I-2.2.3",
    }


def test_route_selection_is_deterministic_and_auditable_with_matching_routes():
    requirement_set = _valid_requirement_set(code_standard="ASME VIII-1", with_corrosion_allowance=True)
    route_configs = (
        StandardRouteConfig(
            route_id="route_legacy_asme",
            standard_name="ASME Legacy",
            standard_version="ASME_BPVC_2021",
            aliases=("ASME VIII-1",),
            route_priority=200,
        ),
        StandardRouteConfig(
            route_id="route_asme_viii_div1",
            standard_name="ASME Section VIII Division 1",
            standard_version="ASME_BPVC_2023",
            aliases=("ASME SECTION VIII DIV 1", "ASME VIII-1"),
            route_priority=100,
        ),
    )

    design_basis_a, matrix_a = build_design_basis(requirement_set, now_utc=FIXED_NOW, route_configs=route_configs)
    design_basis_b, matrix_b = build_design_basis(requirement_set, now_utc=FIXED_NOW, route_configs=route_configs)

    assert design_basis_a.selected_route_id == "route_asme_viii_div1"
    assert design_basis_a.route_selection_audit == design_basis_b.route_selection_audit
    assert design_basis_a.deterministic_signature == design_basis_b.deterministic_signature
    assert matrix_a.deterministic_hash == matrix_b.deterministic_hash

    losing_route = next(record for record in design_basis_a.route_selection_audit if record.route_id == "route_legacy_asme")
    assert losing_route.matched_input is True
    assert losing_route.selected is False


def test_build_design_basis_rejects_blocked_requirement_set():
    blocked = parse_prompt_to_requirement_set("Need a vessel for water storage, 20 m3 capacity.", now_utc=FIXED_NOW)

    with pytest.raises(ValueError, match="downstream_blocked must be false"):
        build_design_basis(blocked, now_utc=FIXED_NOW)


def test_build_design_basis_rejects_non_empty_unresolved_gaps():
    valid = _valid_requirement_set(with_corrosion_allowance=True)
    malformed = RequirementSet(
        schema_version=valid.schema_version,
        generated_at_utc=valid.generated_at_utc,
        input_prompt=valid.input_prompt,
        requirements=valid.requirements,
        unresolved_gaps=[Gap(field="design_temperature", reason="forced test gap")],
        downstream_blocked=False,
        deterministic_hash=valid.deterministic_hash,
    )

    with pytest.raises(ValueError, match="unresolved_gaps must be empty"):
        build_design_basis(malformed, now_utc=FIXED_NOW)


def test_matrix_includes_non_applicable_justification():
    requirement_set = _valid_requirement_set(with_corrosion_allowance=False)

    _, matrix = build_design_basis(requirement_set, now_utc=FIXED_NOW)

    ug25 = next(record for record in matrix.records if record.clause_id == "UG-25")
    assert ug25.applicable is False
    assert "Not applicable" in ug25.justification
    assert ug25.evidence_fields


def test_design_basis_deterministic_signature_matches_frozen_canonical_fixture():
    fixture = json.loads(SIGNATURE_FIXTURE_PATH.read_text(encoding="utf-8"))
    requirement_set = parse_prompt_to_requirement_set(
        fixture["input"]["prompt"],
        now_utc=datetime.fromisoformat(fixture["input"]["now_utc"]),
    )

    design_basis, _ = build_design_basis(requirement_set, now_utc=FIXED_NOW)
    unsigned_payload = design_basis.to_json_dict()
    unsigned_payload.pop("deterministic_signature")

    assert fixture["hash_algorithm"] == "sha256"
    assert fixture["canonicalization"] == "json.sort_keys+compact"
    assert unsigned_payload == fixture["canonical_unsigned_payload"]
    assert design_basis.deterministic_signature == fixture["expected_deterministic_signature"]
