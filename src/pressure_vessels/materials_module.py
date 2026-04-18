"""Deterministic material allowables + corrosion policy resolver for BL-013."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .design_basis_pipeline import DesignBasis
from .requirements_pipeline import RequirementSet

MATERIAL_BASIS_VERSION = "MaterialBasis.v1"

_MATERIAL_RULES: dict[str, dict[str, Any]] = {
    "propane": {
        "material_spec": "SA-516 Gr.70",
        "allowable_stress_pa": 138_000_000.0,
        "joint_efficiency": 0.85,
    },
    "ammonia": {
        "material_spec": "SA-516 Gr.70N",
        "allowable_stress_pa": 130_000_000.0,
        "joint_efficiency": 0.85,
    },
    "__default__": {
        "material_spec": "SA-516 Gr.70",
        "allowable_stress_pa": 138_000_000.0,
        "joint_efficiency": 0.85,
    },
}


@dataclass(frozen=True)
class MaterialBasis:
    schema_version: str
    standards_package_ref: str
    allowables_version: str
    material_spec: str
    allowable_stress_pa: float
    joint_efficiency: float
    corrosion_allowance_m: float
    corrosion_allowance_policy: dict[str, Any]

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_material_basis(requirement_set: RequirementSet, design_basis: DesignBasis) -> MaterialBasis:
    """Resolve deterministic material allowables + corrosion allowance policy."""
    fluid = str(requirement_set.requirements.get("fluid").value).strip().lower()
    rule = _MATERIAL_RULES.get(fluid, _MATERIAL_RULES["__default__"])

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
        standards_package_ref=f"{design_basis.primary_standard}:{design_basis.primary_standard_version}",
        allowables_version=f"{design_basis.primary_standard_version}.materials.2026-04",
        material_spec=str(rule["material_spec"]),
        allowable_stress_pa=float(rule["allowable_stress_pa"]),
        joint_efficiency=float(rule["joint_efficiency"]),
        corrosion_allowance_m=round(corrosion_mm / 1000.0, 9),
        corrosion_allowance_policy=corrosion_policy,
    )
