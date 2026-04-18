from datetime import datetime, timezone

import pytest

from pressure_vessels.design_basis_pipeline import build_design_basis
from pressure_vessels.requirements_pipeline import Gap, RequirementSet, parse_prompt_to_requirement_set


FIXED_NOW = datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc)


def _valid_requirement_set(with_corrosion_allowance: bool = True):
    prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1"
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
    assert design_basis.secondary_standards == []

    assert matrix.schema_version == "ApplicabilityMatrix.v1"
    assert matrix.primary_standard == "ASME Section VIII Division 1"
    assert any(record.clause_id == "UG-28" and record.applicable is False for record in matrix.records)
    assert any(record.clause_id == "UG-37" and record.applicable is True for record in matrix.records)


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


def test_design_basis_signature_is_deterministic_for_same_inputs():
    requirement_set = _valid_requirement_set(with_corrosion_allowance=True)

    design_basis_a, matrix_a = build_design_basis(requirement_set, now_utc=FIXED_NOW)
    design_basis_b, matrix_b = build_design_basis(requirement_set, now_utc=FIXED_NOW)

    assert design_basis_a.deterministic_signature == design_basis_b.deterministic_signature
    assert matrix_a.deterministic_hash == matrix_b.deterministic_hash


def test_matrix_includes_non_applicable_justification():
    requirement_set = _valid_requirement_set(with_corrosion_allowance=False)

    _, matrix = build_design_basis(requirement_set, now_utc=FIXED_NOW)

    ug25 = next(record for record in matrix.records if record.clause_id == "UG-25")
    assert ug25.applicable is False
    assert "Not applicable" in ug25.justification
    assert ug25.evidence_fields
