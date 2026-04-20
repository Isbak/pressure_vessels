"""Deterministic material allowables + corrosion policy resolver for BL-013."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import json
from pathlib import Path
from typing import Any

from .design_basis_pipeline import DesignBasis
from .requirements_pipeline import RequirementSet

MATERIAL_BASIS_VERSION = "MaterialBasis.v1"

_DEFAULT_MATERIAL_PACKAGE_PATHS: dict[str, Path] = {
    "ASME_BPVC_2023": Path(__file__).with_name("data") / "material_allowables" / "asme_bpvc_2023.json",
}


class MaterialAllowablesPackageError(ValueError):
    """Raised when standards-backed material allowables cannot be loaded or validated."""


@dataclass(frozen=True)
class MaterialBasis:
    schema_version: str
    standards_package_ref: str
    standards_package_id: str
    allowables_version: str
    effective_date: str
    material_spec: str
    allowable_stress_pa: float
    joint_efficiency: float
    corrosion_allowance_m: float
    corrosion_allowance_policy: dict[str, Any]

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MaterialAllowablesPackage:
    standards_package_id: str
    standards_package_ref: str
    allowables_version: str
    effective_date: str
    expires_on: str
    materials: dict[str, dict[str, Any]]


def resolve_material_basis(requirement_set: RequirementSet, design_basis: DesignBasis) -> MaterialBasis:
    """Resolve deterministic material allowables + corrosion allowance policy."""
    fluid = str(requirement_set.requirements.get("fluid").value).strip().lower()
    package = _load_material_allowables_package(design_basis)
    rule = package.materials.get(fluid, package.materials.get("__default__"))
    if rule is None:
        raise MaterialAllowablesPackageError(
            "Standards-backed material allowables package is missing '__default__' fallback record."
        )

    corrosion = requirement_set.requirements.get("corrosion_allowance")
    if corrosion is None:
        corrosion_mm = 1.5
        corrosion_policy = {
            "policy_id": "CA-DEFAULT-MM",
            "description": "Use deterministic fallback corrosion allowance when requirement is not provided.",
            "source": "materials-module-default",
            "value_mm": corrosion_mm,
        }
    else:
        corrosion_mm = float(corrosion.value)
        corrosion_policy = {
            "policy_id": "CA-INPUT-REQUIREMENT",
            "description": "Use corrosion allowance directly from normalized RequirementSet input.",
            "source": "requirement_set.corrosion_allowance",
            "value_mm": corrosion_mm,
        }

    return MaterialBasis(
        schema_version=MATERIAL_BASIS_VERSION,
        standards_package_ref=package.standards_package_ref,
        standards_package_id=package.standards_package_id,
        allowables_version=package.allowables_version,
        effective_date=package.effective_date,
        material_spec=str(rule["material_spec"]),
        allowable_stress_pa=float(rule["allowable_stress_pa"]),
        joint_efficiency=float(rule["joint_efficiency"]),
        corrosion_allowance_m=round(corrosion_mm / 1000.0, 9),
        corrosion_allowance_policy=corrosion_policy,
    )


def _load_material_allowables_package(design_basis: DesignBasis) -> MaterialAllowablesPackage:
    package_path = _DEFAULT_MATERIAL_PACKAGE_PATHS.get(design_basis.primary_standard_version)
    if package_path is None:
        raise MaterialAllowablesPackageError(
            "No standards-backed material allowables package configured for "
            f"primary_standard_version={design_basis.primary_standard_version}."
        )
    if not package_path.exists():
        raise MaterialAllowablesPackageError(
            "Standards-backed material allowables package path does not exist: "
            f"{package_path}."
        )

    payload = json.loads(package_path.read_text(encoding="utf-8"))
    required_fields = (
        "standards_package_id",
        "standards_package_ref",
        "allowables_version",
        "effective_date",
        "expires_on",
        "materials",
    )
    missing = [field for field in required_fields if field not in payload]
    if missing:
        raise MaterialAllowablesPackageError(
            "Standards-backed material allowables package missing required field(s): "
            f"{', '.join(missing)}."
        )

    effective = date.fromisoformat(str(payload["effective_date"]))
    expires_on = date.fromisoformat(str(payload["expires_on"]))
    generated_on = date.fromisoformat(design_basis.generated_at_utc[:10])
    if generated_on < effective:
        raise MaterialAllowablesPackageError(
            "Standards-backed material allowables package is not yet effective for "
            f"design basis date {generated_on.isoformat()} (effective_date={effective.isoformat()})."
        )
    if generated_on > expires_on:
        raise MaterialAllowablesPackageError(
            "Standards-backed material allowables package is expired for "
            f"design basis date {generated_on.isoformat()} (expires_on={expires_on.isoformat()})."
        )

    materials = payload["materials"]
    if not isinstance(materials, dict):
        raise MaterialAllowablesPackageError("Standards-backed material allowables package 'materials' must be an object.")

    return MaterialAllowablesPackage(
        standards_package_id=str(payload["standards_package_id"]),
        standards_package_ref=str(payload["standards_package_ref"]),
        allowables_version=str(payload["allowables_version"]),
        effective_date=str(payload["effective_date"]),
        expires_on=str(payload["expires_on"]),
        materials=materials,
    )
