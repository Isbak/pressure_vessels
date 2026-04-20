import json
from datetime import datetime, timezone

import pytest

from pressure_vessels.design_basis_pipeline import build_design_basis
from pressure_vessels.materials_module import (
    _DEFAULT_MATERIAL_PACKAGE_PATHS,
    MaterialAllowablesPackageError,
    resolve_material_basis,
)
from pressure_vessels.requirements_pipeline import parse_prompt_to_requirement_set

FIXED_NOW = datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc)


def _build_inputs(prompt: str):
    requirement_set = parse_prompt_to_requirement_set(prompt, now_utc=FIXED_NOW)
    design_basis, _ = build_design_basis(requirement_set, now_utc=FIXED_NOW)
    return requirement_set, design_basis


def _default_prompt() -> str:
    return (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )


def test_resolve_material_basis_reads_standards_package_metadata():
    requirement_set, design_basis = _build_inputs(_default_prompt())

    material_basis = resolve_material_basis(requirement_set, design_basis)

    assert material_basis.standards_package_id == "ASME_BPVC_2023_MATERIALS_2026-04"
    assert material_basis.effective_date == "2026-04-01"
    assert material_basis.allowables_version == "ASME_BPVC_2023.materials.2026-04"


def test_resolve_material_basis_fails_when_package_path_is_missing(monkeypatch, tmp_path):
    requirement_set, design_basis = _build_inputs(_default_prompt())
    missing_path = tmp_path / "missing-materials-package.json"
    monkeypatch.setitem(_DEFAULT_MATERIAL_PACKAGE_PATHS, "ASME_BPVC_2023", missing_path)

    with pytest.raises(MaterialAllowablesPackageError, match="path does not exist"):
        resolve_material_basis(requirement_set, design_basis)


def test_resolve_material_basis_fails_when_package_is_expired(monkeypatch, tmp_path):
    requirement_set, design_basis = _build_inputs(_default_prompt())
    expired_path = tmp_path / "expired-materials-package.json"
    expired_payload = {
        "schema_version": "MaterialAllowablesPackage.v1",
        "standards_package_id": "ASME_BPVC_2023_MATERIALS_2024-01",
        "standards_package_ref": "ASME Section VIII Division 1:ASME_BPVC_2023",
        "allowables_version": "ASME_BPVC_2023.materials.2024-01",
        "effective_date": "2024-01-01",
        "expires_on": "2024-12-31",
        "materials": {
            "propane": {
                "material_spec": "SA-516 Gr.70",
                "allowable_stress_pa": 138000000.0,
                "joint_efficiency": 0.85,
            },
            "__default__": {
                "material_spec": "SA-516 Gr.70",
                "allowable_stress_pa": 138000000.0,
                "joint_efficiency": 0.85,
            },
        },
    }
    expired_path.write_text(json.dumps(expired_payload), encoding="utf-8")
    monkeypatch.setitem(_DEFAULT_MATERIAL_PACKAGE_PATHS, "ASME_BPVC_2023", expired_path)

    with pytest.raises(MaterialAllowablesPackageError, match="is expired"):
        resolve_material_basis(requirement_set, design_basis)
