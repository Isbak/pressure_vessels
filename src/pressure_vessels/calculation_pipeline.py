"""Deterministic ASME Div 1 sizing checks for BL-003."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
import warnings

from .design_basis_pipeline import ApplicabilityMatrix, DesignBasis
from .geometry_module import GeometryInput, adapt_geometry_input, build_cad_ready_parameter_export
from .materials_module import MaterialBasis, resolve_material_basis
from .requirements_pipeline import CANONICAL_UNITS, RequirementSet

CALCULATION_RECORDS_VERSION = "CalculationRecords.v1"
NON_CONFORMANCE_LIST_VERSION = "NonConformanceList.v1"
DEFAULT_NEAR_LIMIT_THRESHOLD = 0.9
_SAFETY_CRITICAL_ROUNDING_DECIMALS = 9

# BL-003 MVP geometry defaults used when sizing_input is not supplied.
# Stress/joint-efficiency/corrosion policy are now resolved by BL-013 material basis.
_MVP_DEFAULTS = {
    "shell_inside_diameter_m": 2.0,
    "shell_provided_thickness_m": 0.020,
    "head_inside_diameter_m": 2.0,
    "head_provided_thickness_m": 0.018,
    "nozzle_inside_diameter_m": 0.35,
    "nozzle_provided_thickness_m": 0.004,
    "source": "BL-003 MVP geometry placeholder; replace with Geometry/CAD module outputs.",
}

_MVP_DEFAULT_FIELDS = (
    "shell_inside_diameter_m",
    "shell_provided_thickness_m",
    "head_inside_diameter_m",
    "head_provided_thickness_m",
    "nozzle_inside_diameter_m",
    "nozzle_provided_thickness_m",
)
_MVP_DEFAULT_AUDIT_EVENT = {
    "event_id": "BL-003-MVP-GEOMETRY-DEFAULTS-NON-PRODUCTION",
    "event_type": "non_production_mvp_defaults_opt_in",
}


def _round_safety_critical(value: float) -> float:
    """Round deterministic sizing values to 9 decimals per ADR-0006.

    BL-003 checks use SI units (`m`, `Pa`) with pass/fail comparisons that are
    sensitive to floating-point noise. Nine decimals sets a deterministic
    quantization floor of 1e-9 in SI units (nanometer-scale for lengths), which
    is far below fabrication and inspection tolerances while still stabilizing
    reproducibility hashes and near-boundary outcomes across runtimes.
    Changes to this precision require ADR review before implementation.
    """

    return round(value, _SAFETY_CRITICAL_ROUNDING_DECIMALS)


class MissingGeometryInputError(ValueError):
    """Raised when BL-003 geometry inputs are missing without explicit MVP-default opt-in."""

# Maps each BL-003 check to the ApplicabilityMatrix clause it implements.
_CHECK_CLAUSE_MAP: dict[str, str] = {
    "UG-27-shell": "UG-27",
    "UG-32-head": "UG-32",
    "UG-45-nozzle": "UG-45",
    "UG-27-shell-mawp": "UG-27",
    "UG-32-head-mawp": "UG-32",
    "UG-45-nozzle-mawp": "UG-45",
    "UG-28-shell-external": "UG-28",
    "UG-28-head-external": "UG-28",
    "UG-37-nozzle-shell-reinforcement": "UG-37",
    "UG-37-nozzle-head-reinforcement": "UG-37",
}

_MODEL_VALIDITY_ENVELOPES: dict[str, dict[str, Any]] = {
    "UG-27-shell": {
        "model_id": "ug27_shell_thickness_v1",
        "bounds": {
            "internal_pressure_pa": {"min": 1.0, "max": 20_000_000.0},
            "allowable_stress_pa": {"min": 50_000_000.0, "max": 500_000_000.0},
            "joint_efficiency": {"min": 0.5, "max": 1.0},
            "shell_inside_diameter_m": {"min": 0.25, "max": 8.0},
            "corrosion_allowance_m": {"min": 0.0, "max": 0.02},
        },
    },
    "UG-32-head": {
        "model_id": "ug32_head_thickness_v1",
        "bounds": {
            "internal_pressure_pa": {"min": 1.0, "max": 20_000_000.0},
            "allowable_stress_pa": {"min": 50_000_000.0, "max": 500_000_000.0},
            "joint_efficiency": {"min": 0.5, "max": 1.0},
            "head_inside_diameter_m": {"min": 0.25, "max": 8.0},
            "corrosion_allowance_m": {"min": 0.0, "max": 0.02},
        },
    },
    "UG-45-nozzle": {
        "model_id": "ug45_nozzle_thickness_v1",
        "bounds": {
            "internal_pressure_pa": {"min": 1.0, "max": 20_000_000.0},
            "allowable_stress_pa": {"min": 50_000_000.0, "max": 500_000_000.0},
            "joint_efficiency": {"min": 0.5, "max": 1.0},
            "nozzle_inside_diameter_m": {"min": 0.05, "max": 2.0},
            "corrosion_allowance_m": {"min": 0.0, "max": 0.02},
        },
    },
    "UG-27-shell-mawp": {
        "model_id": "ug27_shell_mawp_v1",
        "bounds": {
            "allowable_stress_pa": {"min": 50_000_000.0, "max": 500_000_000.0},
            "joint_efficiency": {"min": 0.5, "max": 1.0},
            "shell_inside_diameter_m": {"min": 0.25, "max": 8.0},
            "shell_provided_thickness_m": {"min": 0.002, "max": 0.25},
            "corrosion_allowance_m": {"min": 0.0, "max": 0.02},
        },
    },
    "UG-32-head-mawp": {
        "model_id": "ug32_head_mawp_v1",
        "bounds": {
            "allowable_stress_pa": {"min": 50_000_000.0, "max": 500_000_000.0},
            "joint_efficiency": {"min": 0.5, "max": 1.0},
            "head_inside_diameter_m": {"min": 0.25, "max": 8.0},
            "head_provided_thickness_m": {"min": 0.002, "max": 0.25},
            "corrosion_allowance_m": {"min": 0.0, "max": 0.02},
        },
    },
    "UG-45-nozzle-mawp": {
        "model_id": "ug45_nozzle_mawp_v1",
        "bounds": {
            "allowable_stress_pa": {"min": 50_000_000.0, "max": 500_000_000.0},
            "joint_efficiency": {"min": 0.5, "max": 1.0},
            "nozzle_inside_diameter_m": {"min": 0.05, "max": 2.0},
            "nozzle_provided_thickness_m": {"min": 0.001, "max": 0.25},
            "corrosion_allowance_m": {"min": 0.0, "max": 0.02},
        },
    },
    "UG-37-nozzle-shell-reinforcement": {
        "model_id": "ug37_nozzle_shell_reinforcement_v1",
        "bounds": {
            "shell_inside_diameter_m": {"min": 0.25, "max": 8.0},
            "nozzle_inside_diameter_m": {"min": 0.05, "max": 2.0},
            "shell_provided_thickness_m": {"min": 0.002, "max": 0.25},
            "nozzle_provided_thickness_m": {"min": 0.001, "max": 0.25},
        },
    },
    "UG-37-nozzle-head-reinforcement": {
        "model_id": "ug37_nozzle_head_reinforcement_v1",
        "bounds": {
            "head_inside_diameter_m": {"min": 0.25, "max": 8.0},
            "nozzle_inside_diameter_m": {"min": 0.05, "max": 2.0},
            "head_provided_thickness_m": {"min": 0.002, "max": 0.25},
            "nozzle_provided_thickness_m": {"min": 0.001, "max": 0.25},
        },
    },
    "UG-28-shell-external": {
        "model_id": "ug28_shell_external_v1",
        "bounds": {
            "external_pressure_pa": {"min": 1.0, "max": 2_000_000.0},
            "shell_inside_diameter_m": {"min": 0.25, "max": 8.0},
            "shell_provided_thickness_m": {"min": 0.002, "max": 0.25},
            "corrosion_allowance_m": {"min": 0.0, "max": 0.02},
        },
    },
    "UG-28-head-external": {
        "model_id": "ug28_head_external_v1",
        "bounds": {
            "external_pressure_pa": {"min": 1.0, "max": 2_000_000.0},
            "head_inside_diameter_m": {"min": 0.25, "max": 8.0},
            "head_provided_thickness_m": {"min": 0.002, "max": 0.25},
            "corrosion_allowance_m": {"min": 0.0, "max": 0.02},
        },
    },
}


@dataclass(frozen=True)
class Quantity:
    value: float
    unit: str


@dataclass(frozen=True)
class ReproducibilityMetadata:
    canonical_payload_sha256: str
    hash_algorithm: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "canonical_payload_sha256": self.canonical_payload_sha256,
            "hash_algorithm": self.hash_algorithm,
        }


@dataclass(frozen=True)
class SizingCheckInput:
    internal_pressure: Quantity
    allowable_stress: Quantity
    joint_efficiency: float
    corrosion_allowance: Quantity
    shell_inside_diameter: Quantity
    shell_provided_thickness: Quantity
    head_inside_diameter: Quantity
    head_provided_thickness: Quantity
    nozzle_inside_diameter: Quantity
    nozzle_provided_thickness: Quantity
    external_pressure: Quantity | None = None


@dataclass(frozen=True)
class CalculationRecord:
    check_id: str
    clause_id: str
    component: str
    formula: str
    inputs: dict[str, float]
    required_thickness_m: float
    provided_thickness_m: float
    margin_m: float
    utilization_ratio: float | None
    utilization_invalid_reason: str | None
    near_limit_threshold: float
    is_near_limit: bool
    pass_status: bool
    reproducibility: ReproducibilityMetadata
    parent_component: str | None = None
    parent_check_id: str | None = None
    design_pressure_pa: float | None = None
    computed_mawp_pa: float | None = None
    pressure_margin_pa: float | None = None
    validity_envelope: dict[str, Any] | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "clause_id": self.clause_id,
            "component": self.component,
            "formula": self.formula,
            "inputs": self.inputs,
            "required_thickness_m": self.required_thickness_m,
            "provided_thickness_m": self.provided_thickness_m,
            "margin_m": self.margin_m,
            "utilization_ratio": self.utilization_ratio,
            "utilization_invalid_reason": self.utilization_invalid_reason,
            "near_limit_threshold": self.near_limit_threshold,
            "is_near_limit": self.is_near_limit,
            "parent_component": self.parent_component,
            "parent_check_id": self.parent_check_id,
            "design_pressure_pa": self.design_pressure_pa,
            "computed_mawp_pa": self.computed_mawp_pa,
            "pressure_margin_pa": self.pressure_margin_pa,
            "validity_envelope": self.validity_envelope,
            "pass_status": self.pass_status,
            "reproducibility": self.reproducibility.to_json_dict(),
        }


@dataclass(frozen=True)
class NonConformanceEntry:
    check_id: str
    clause_id: str
    component: str
    observed: str
    required: str
    severity: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CalculationRecordsArtifact:
    schema_version: str
    generated_at_utc: str
    source_requirement_set_hash: str
    source_design_basis_signature: str
    source_applicability_matrix_hash: str
    material_basis: dict[str, Any]
    geometry_basis: dict[str, Any]
    applied_defaults: dict[str, Any]
    cad_ready_parameter_export: dict[str, Any] | None
    checks: list[CalculationRecord]
    deterministic_hash: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at_utc": self.generated_at_utc,
            "source_requirement_set_hash": self.source_requirement_set_hash,
            "source_design_basis_signature": self.source_design_basis_signature,
            "source_applicability_matrix_hash": self.source_applicability_matrix_hash,
            "material_basis": self.material_basis,
            "geometry_basis": self.geometry_basis,
            "applied_defaults": self.applied_defaults,
            "cad_ready_parameter_export": self.cad_ready_parameter_export,
            "checks": [record.to_json_dict() for record in self.checks],
            "deterministic_hash": self.deterministic_hash,
        }


@dataclass(frozen=True)
class NonConformanceListArtifact:
    schema_version: str
    generated_at_utc: str
    source_calculation_records_hash: str
    entries: list[NonConformanceEntry]
    deterministic_hash: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at_utc": self.generated_at_utc,
            "source_calculation_records_hash": self.source_calculation_records_hash,
            "entries": [entry.to_json_dict() for entry in self.entries],
            "deterministic_hash": self.deterministic_hash,
        }


def run_calculation_pipeline(
    requirement_set: RequirementSet,
    design_basis: DesignBasis,
    applicability_matrix: ApplicabilityMatrix,
    sizing_input: SizingCheckInput | None = None,
    geometry_input: GeometryInput | None = None,
    *,
    now_utc: datetime | None = None,
    near_limit_threshold: float = DEFAULT_NEAR_LIMIT_THRESHOLD,
    strict_sizing_input_gate: bool = False,
    use_mvp_defaults: bool = False,
) -> tuple[CalculationRecordsArtifact, NonConformanceListArtifact]:
    """Run deterministic shell/head/nozzle sizing checks for BL-003 MVP."""
    _validate_handoff_gate(
        requirement_set=requirement_set,
        design_basis=design_basis,
        applicability_matrix=applicability_matrix,
    )

    generated_at = (now_utc or datetime.now(tz=timezone.utc)).replace(microsecond=0).isoformat()
    material_basis = resolve_material_basis(requirement_set, design_basis)
    normalized_input, applied_defaults, geometry_basis = _normalize_and_resolve_inputs(
        requirement_set,
        sizing_input,
        geometry_input,
        material_basis,
        strict_sizing_input_gate,
        use_mvp_defaults,
    )
    _validate_model_domain_gate(normalized_input, near_limit_threshold)
    _validate_validity_envelopes(normalized_input)

    shell_check = _build_shell_check(normalized_input, near_limit_threshold)
    head_check = _build_head_check(normalized_input, near_limit_threshold)
    nozzle_check = _build_nozzle_check(normalized_input, near_limit_threshold)
    shell_mawp_check = _build_shell_mawp_check(normalized_input, near_limit_threshold)
    head_mawp_check = _build_head_mawp_check(normalized_input, near_limit_threshold)
    nozzle_mawp_check = _build_nozzle_mawp_check(normalized_input, near_limit_threshold)
    reinforcement_checks = _build_reinforcement_checks(
        inputs=normalized_input,
        nozzle_thickness_check=nozzle_check,
        parent_thickness_checks=[shell_check, head_check],
        near_limit_threshold=near_limit_threshold,
    )

    checks = [
        shell_check,
        head_check,
        nozzle_check,
        shell_mawp_check,
        head_mawp_check,
        nozzle_mawp_check,
        *reinforcement_checks,
    ]
    checks.extend(_build_external_pressure_checks(normalized_input, near_limit_threshold))

    _validate_clause_coverage(checks, applicability_matrix)

    calc_payload = {
        "schema_version": CALCULATION_RECORDS_VERSION,
        "generated_at_utc": generated_at,
        "source_requirement_set_hash": requirement_set.deterministic_hash,
        "source_design_basis_signature": design_basis.deterministic_signature,
        "source_applicability_matrix_hash": applicability_matrix.deterministic_hash,
        "material_basis": material_basis.to_json_dict(),
        "geometry_basis": geometry_basis,
        "applied_defaults": applied_defaults,
        "checks": [record.to_json_dict() for record in checks],
    }
    calc_hash = _sha256_payload(calc_payload)

    cad_export = None
    if geometry_input is not None:
        cad_export = build_cad_ready_parameter_export(
            geometry_input,
            calculation_records_hash=calc_hash,
        ).to_json_dict()

    calc_artifact = CalculationRecordsArtifact(
        schema_version=CALCULATION_RECORDS_VERSION,
        generated_at_utc=generated_at,
        source_requirement_set_hash=requirement_set.deterministic_hash,
        source_design_basis_signature=design_basis.deterministic_signature,
        source_applicability_matrix_hash=applicability_matrix.deterministic_hash,
        material_basis=material_basis.to_json_dict(),
        geometry_basis=geometry_basis,
        applied_defaults=applied_defaults,
        cad_ready_parameter_export=cad_export,
        checks=checks,
        deterministic_hash=calc_hash,
    )

    entries = _build_non_conformances(checks)
    nc_payload = {
        "schema_version": NON_CONFORMANCE_LIST_VERSION,
        "generated_at_utc": generated_at,
        "source_calculation_records_hash": calc_artifact.deterministic_hash,
        "entries": [entry.to_json_dict() for entry in entries],
    }
    nc_hash = _sha256_payload(nc_payload)

    non_conformance_artifact = NonConformanceListArtifact(
        schema_version=NON_CONFORMANCE_LIST_VERSION,
        generated_at_utc=generated_at,
        source_calculation_records_hash=calc_artifact.deterministic_hash,
        entries=entries,
        deterministic_hash=nc_hash,
    )

    return calc_artifact, non_conformance_artifact


def write_calculation_artifacts(
    calc_artifact: CalculationRecordsArtifact,
    non_conformance_artifact: NonConformanceListArtifact,
    directory: str | Path,
    *,
    filename_prefix: str = "",
) -> tuple[Path, Path]:
    """Persist BL-003 artifacts to disk in canonical JSON form."""
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)

    calc_path = target / f"{filename_prefix}{CALCULATION_RECORDS_VERSION}.json"
    nc_path = target / f"{filename_prefix}{NON_CONFORMANCE_LIST_VERSION}.json"

    calc_path.write_text(
        json.dumps(calc_artifact.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    nc_path.write_text(
        json.dumps(non_conformance_artifact.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return calc_path, nc_path


def _validate_handoff_gate(
    requirement_set: RequirementSet,
    design_basis: DesignBasis,
    applicability_matrix: ApplicabilityMatrix,
) -> None:
    if requirement_set.downstream_blocked:
        raise ValueError("BL-003 handoff gate failed: requirement_set.downstream_blocked must be false.")
    if requirement_set.unresolved_gaps:
        raise ValueError("BL-003 handoff gate failed: requirement_set.unresolved_gaps must be empty.")
    if design_basis.primary_standard != "ASME Section VIII Division 1":
        raise ValueError("BL-003 MVP supports only ASME Section VIII Division 1 design basis.")
    if applicability_matrix.source_requirement_set_hash != requirement_set.deterministic_hash:
        raise ValueError(
            "BL-003 handoff gate failed: applicability_matrix.source_requirement_set_hash "
            "does not match the provided requirement_set."
        )

    # Unit-consistency gate: every canonical field present on the RequirementSet
    # must match the canonical unit policy defined in BL-001.
    for field, expected_unit in CANONICAL_UNITS.items():
        value = requirement_set.requirements.get(field)
        if value is None:
            continue
        if value.unit != expected_unit:
            raise ValueError(
                f"BL-003 handoff gate failed: expected {field} unit {expected_unit}, "
                f"got {value.unit}."
            )


def _validate_clause_coverage(
    checks: list[CalculationRecord],
    applicability_matrix: ApplicabilityMatrix,
) -> None:
    applicable_clauses = {
        record.clause_id for record in applicability_matrix.records if record.applicable
    }
    for check in checks:
        if check.clause_id not in applicable_clauses:
            raise ValueError(
                f"BL-003 clause-coverage gate failed: clause {check.clause_id} for check "
                f"{check.check_id} is not marked applicable in the ApplicabilityMatrix."
            )


def _normalize_and_resolve_inputs(
    requirement_set: RequirementSet,
    sizing_input: SizingCheckInput | None,
    geometry_input: GeometryInput | None,
    material_basis: MaterialBasis,
    strict_sizing_input_gate: bool,
    use_mvp_defaults: bool,
) -> tuple[SizingCheckInput, dict[str, Any], dict[str, Any]]:
    if sizing_input is not None:
        normalized = SizingCheckInput(
            internal_pressure=_to_si_pressure(sizing_input.internal_pressure),
            allowable_stress=_to_si_pressure(sizing_input.allowable_stress),
            joint_efficiency=sizing_input.joint_efficiency,
            corrosion_allowance=_to_si_length(sizing_input.corrosion_allowance),
            shell_inside_diameter=_to_si_length(sizing_input.shell_inside_diameter),
            shell_provided_thickness=_to_si_length(sizing_input.shell_provided_thickness),
            head_inside_diameter=_to_si_length(sizing_input.head_inside_diameter),
            head_provided_thickness=_to_si_length(sizing_input.head_provided_thickness),
            nozzle_inside_diameter=_to_si_length(sizing_input.nozzle_inside_diameter),
            nozzle_provided_thickness=_to_si_length(sizing_input.nozzle_provided_thickness),
            external_pressure=(
                _to_si_pressure(sizing_input.external_pressure)
                if sizing_input.external_pressure is not None
                else None
            ),
        )
        applied_defaults = {
            "applied_mvp_defaults": False,
            "non_production_flag": False,
            "values": {},
            "source": "caller-provided",
        }
        geometry_basis = {"source": "sizing_input", "geometry_revision_id": None}
        return normalized, applied_defaults, geometry_basis

    if geometry_input is not None:
        geometry_payload = adapt_geometry_input(geometry_input)
        normalized = SizingCheckInput(
            internal_pressure=Quantity(value=float(requirement_set.requirements["design_pressure"].value), unit="Pa"),
            allowable_stress=Quantity(value=material_basis.allowable_stress_pa, unit="Pa"),
            joint_efficiency=material_basis.joint_efficiency,
            corrosion_allowance=Quantity(value=material_basis.corrosion_allowance_m, unit="m"),
            shell_inside_diameter=Quantity(value=float(geometry_payload["shell_inside_diameter_m"]), unit="m"),
            shell_provided_thickness=Quantity(
                value=float(geometry_payload["shell_provided_thickness_m"]),
                unit="m",
            ),
            head_inside_diameter=Quantity(value=float(geometry_payload["head_inside_diameter_m"]), unit="m"),
            head_provided_thickness=Quantity(
                value=float(geometry_payload["head_provided_thickness_m"]),
                unit="m",
            ),
            nozzle_inside_diameter=Quantity(value=float(geometry_payload["nozzle_inside_diameter_m"]), unit="m"),
            nozzle_provided_thickness=Quantity(
                value=float(geometry_payload["nozzle_provided_thickness_m"]),
                unit="m",
            ),
            external_pressure=(
                Quantity(value=float(geometry_payload["external_pressure_pa"]), unit="Pa")
                if geometry_payload["external_pressure_pa"] is not None
                else _external_pressure_from_requirements(requirement_set)
            ),
        )
        applied_defaults = {
            "applied_geometry_defaults": False,
            "applied_mvp_defaults": False,
            "non_production_flag": False,
            "values": {},
            "source": "geometry-module+materials-module",
            "material_source": "materials_module.resolve_material_basis",
            "corrosion_allowance_policy": material_basis.corrosion_allowance_policy,
        }
        geometry_basis = {
            "source": "geometry_module.GeometryInput.v1",
            "geometry_revision_id": geometry_input.geometry_revision_id,
            "source_system": geometry_input.source_system,
            "source_model_sha256": geometry_input.source_model_sha256,
        }
        return normalized, applied_defaults, geometry_basis

    if strict_sizing_input_gate:
        raise ValueError(
            "BL-014 strict sizing-input gate failed: sizing_input or geometry_input is required."
        )

    if not use_mvp_defaults:
        missing_fields = ", ".join(_MVP_DEFAULT_FIELDS)
        raise MissingGeometryInputError(
            "BL-003 geometry input required: missing sizing_input or geometry_input; "
            f"missing fields: {missing_fields}."
        )

    warnings.warn(
        "NON-PRODUCTION ONLY: BL-003 using MVP geometry defaults for missing fields: "
        + ", ".join(_MVP_DEFAULT_FIELDS),
        UserWarning,
        stacklevel=2,
    )

    pressure_pa = float(requirement_set.requirements["design_pressure"].value)
    ca_m = material_basis.corrosion_allowance_m

    normalized = SizingCheckInput(
        internal_pressure=Quantity(value=pressure_pa, unit="Pa"),
        allowable_stress=Quantity(value=material_basis.allowable_stress_pa, unit="Pa"),
        joint_efficiency=material_basis.joint_efficiency,
        corrosion_allowance=Quantity(value=ca_m, unit="m"),
        shell_inside_diameter=Quantity(value=_MVP_DEFAULTS["shell_inside_diameter_m"], unit="m"),
        shell_provided_thickness=Quantity(
            value=_MVP_DEFAULTS["shell_provided_thickness_m"], unit="m"
        ),
        head_inside_diameter=Quantity(value=_MVP_DEFAULTS["head_inside_diameter_m"], unit="m"),
        head_provided_thickness=Quantity(
            value=_MVP_DEFAULTS["head_provided_thickness_m"], unit="m"
        ),
        nozzle_inside_diameter=Quantity(value=_MVP_DEFAULTS["nozzle_inside_diameter_m"], unit="m"),
        nozzle_provided_thickness=Quantity(
            value=_MVP_DEFAULTS["nozzle_provided_thickness_m"], unit="m"
        ),
        external_pressure=_external_pressure_from_requirements(requirement_set),
    )
    applied_defaults = {
        "applied_geometry_defaults": True,
        "applied_mvp_defaults": True,
        "non_production_flag": True,
        "audit_event": {
            **_MVP_DEFAULT_AUDIT_EVENT,
            "message": "NON-PRODUCTION ONLY: Explicit opt-in via use_mvp_defaults=True.",
        },
        "values": dict(_MVP_DEFAULTS),
        "source": _MVP_DEFAULTS["source"],
        "material_source": "materials_module.resolve_material_basis",
        "corrosion_allowance_policy": material_basis.corrosion_allowance_policy,
    }
    geometry_basis = {
        "source": "BL-003 MVP geometry placeholder",
        "geometry_revision_id": None,
        "source_system": "placeholder",
        "source_model_sha256": None,
    }
    return normalized, applied_defaults, geometry_basis


def _build_shell_check(inputs: SizingCheckInput, near_limit_threshold: float) -> CalculationRecord:
    """Build the UG-27(c)(1) cylindrical-shell internal-pressure thickness check."""
    p = inputs.internal_pressure.value
    s = inputs.allowable_stress.value
    e = inputs.joint_efficiency
    d = inputs.shell_inside_diameter.value
    ca = inputs.corrosion_allowance.value
    provided = inputs.shell_provided_thickness.value

    # Placeholder extension point for full UG-27(c)(1) cylindrical shell logic.
    required = ((p * d) / (2.0 * (s * e - 0.6 * p))) + ca
    return _to_record(
        check_id="UG-27-shell",
        component="shell",
        formula="t = (P*D)/(2*(S*E-0.6P)) + CA",
        inputs={"P_Pa": p, "S_Pa": s, "E": e, "D_m": d, "CA_m": ca},
        required=required,
        provided=provided,
        near_limit_threshold=near_limit_threshold,
    )


def _build_head_check(inputs: SizingCheckInput, near_limit_threshold: float) -> CalculationRecord:
    """Build the UG-32(c) ellipsoidal-head internal-pressure thickness check."""
    p = inputs.internal_pressure.value
    s = inputs.allowable_stress.value
    e = inputs.joint_efficiency
    d = inputs.head_inside_diameter.value
    ca = inputs.corrosion_allowance.value
    provided = inputs.head_provided_thickness.value

    # Placeholder extension point for full hemispherical/ellipsoidal head formula selection.
    required = ((0.885 * p * d) / (2.0 * s * e - 0.2 * p)) + ca
    return _to_record(
        check_id="UG-32-head",
        component="head",
        formula="t = (0.885*P*D)/(2*S*E-0.2P) + CA",
        inputs={"P_Pa": p, "S_Pa": s, "E": e, "D_m": d, "CA_m": ca},
        required=required,
        provided=provided,
        near_limit_threshold=near_limit_threshold,
    )


def _build_nozzle_check(inputs: SizingCheckInput, near_limit_threshold: float) -> CalculationRecord:
    """Build the UG-45 nozzle-neck internal-pressure minimum-thickness check."""
    p = inputs.internal_pressure.value
    s = inputs.allowable_stress.value
    e = inputs.joint_efficiency
    d = inputs.nozzle_inside_diameter.value
    ca = inputs.corrosion_allowance.value
    provided = inputs.nozzle_provided_thickness.value

    # Placeholder extension point for full UG-45 nozzle neck and reinforcement-area logic.
    required = ((0.5 * p * d) / (s * e - 0.4 * p)) + ca
    return _to_record(
        check_id="UG-45-nozzle",
        component="nozzle",
        formula="t = (0.5*P*d)/(S*E-0.4P) + CA",
        inputs={"P_Pa": p, "S_Pa": s, "E": e, "d_m": d, "CA_m": ca},
        required=required,
        provided=provided,
        near_limit_threshold=near_limit_threshold,
    )


def _build_shell_mawp_check(inputs: SizingCheckInput, near_limit_threshold: float) -> CalculationRecord:
    """Build the UG-27(c)(1) cylindrical-shell MAWP back-calculation check."""
    s = inputs.allowable_stress.value
    e = inputs.joint_efficiency
    d = inputs.shell_inside_diameter.value
    ca = inputs.corrosion_allowance.value
    p_design = inputs.internal_pressure.value
    provided = inputs.shell_provided_thickness.value
    net = max(provided - ca, 0.0)
    mawp = (2.0 * s * e * net) / (d + 1.2 * net) if net > 0.0 else 0.0

    return _to_record(
        check_id="UG-27-shell-mawp",
        component="shell",
        formula="MAWP = (2*S*E*(t-CA))/(D+1.2*(t-CA))",
        inputs={"S_Pa": s, "E": e, "D_m": d, "CA_m": ca, "t_m": provided, "P_design_Pa": p_design},
        required=p_design,
        provided=provided,
        design_pressure_pa=p_design,
        computed_mawp_pa=mawp,
        near_limit_threshold=near_limit_threshold,
    )


def _build_head_mawp_check(inputs: SizingCheckInput, near_limit_threshold: float) -> CalculationRecord:
    """Build the UG-32(c) ellipsoidal-head MAWP back-calculation check."""
    s = inputs.allowable_stress.value
    e = inputs.joint_efficiency
    d = inputs.head_inside_diameter.value
    ca = inputs.corrosion_allowance.value
    p_design = inputs.internal_pressure.value
    provided = inputs.head_provided_thickness.value
    net = max(provided - ca, 0.0)
    mawp = (2.0 * s * e * net) / ((0.885 * d) + (0.2 * net)) if net > 0.0 else 0.0

    return _to_record(
        check_id="UG-32-head-mawp",
        component="head",
        formula="MAWP = (2*S*E*(t-CA))/((0.885*D)+0.2*(t-CA))",
        inputs={"S_Pa": s, "E": e, "D_m": d, "CA_m": ca, "t_m": provided, "P_design_Pa": p_design},
        required=p_design,
        provided=provided,
        design_pressure_pa=p_design,
        computed_mawp_pa=mawp,
        near_limit_threshold=near_limit_threshold,
    )


def _build_nozzle_mawp_check(inputs: SizingCheckInput, near_limit_threshold: float) -> CalculationRecord:
    """Build the UG-45 nozzle-neck MAWP back-calculation check."""
    s = inputs.allowable_stress.value
    e = inputs.joint_efficiency
    d = inputs.nozzle_inside_diameter.value
    ca = inputs.corrosion_allowance.value
    p_design = inputs.internal_pressure.value
    provided = inputs.nozzle_provided_thickness.value
    net = max(provided - ca, 0.0)
    mawp = (s * e * net) / ((0.5 * d) + (0.4 * net)) if net > 0.0 else 0.0

    return _to_record(
        check_id="UG-45-nozzle-mawp",
        component="nozzle",
        formula="MAWP = (S*E*(t-CA))/((0.5*d)+0.4*(t-CA))",
        inputs={"S_Pa": s, "E": e, "d_m": d, "CA_m": ca, "t_m": provided, "P_design_Pa": p_design},
        required=p_design,
        provided=provided,
        design_pressure_pa=p_design,
        computed_mawp_pa=mawp,
        near_limit_threshold=near_limit_threshold,
    )


def _build_external_pressure_checks(
    inputs: SizingCheckInput, near_limit_threshold: float
) -> list[CalculationRecord]:
    """Build paired UG-28 external-pressure checks for shell and head components."""
    if inputs.external_pressure is None:
        return []

    p_external = inputs.external_pressure.value
    checks = [
        _build_ug28_external_check(
            check_id="UG-28-shell-external",
            component="shell",
            diameter_m=inputs.shell_inside_diameter.value,
            provided_thickness_m=inputs.shell_provided_thickness.value,
            corrosion_allowance_m=inputs.corrosion_allowance.value,
            p_external_pa=p_external,
            near_limit_threshold=near_limit_threshold,
        ),
        _build_ug28_external_check(
            check_id="UG-28-head-external",
            component="head",
            diameter_m=inputs.head_inside_diameter.value,
            provided_thickness_m=inputs.head_provided_thickness.value,
            corrosion_allowance_m=inputs.corrosion_allowance.value,
            p_external_pa=p_external,
            near_limit_threshold=near_limit_threshold,
        ),
    ]
    return checks


def _build_reinforcement_checks(
    *,
    inputs: SizingCheckInput,
    nozzle_thickness_check: CalculationRecord,
    parent_thickness_checks: list[CalculationRecord],
    near_limit_threshold: float,
) -> list[CalculationRecord]:
    """Build UG-37 opening-reinforcement area checks for shell and head nozzle attachments."""
    parent_index = {record.component: record for record in parent_thickness_checks}
    return [
        _build_ug37_reinforcement_check(
            check_id="UG-37-nozzle-shell-reinforcement",
            parent_component="shell",
            opening_diameter_m=inputs.nozzle_inside_diameter.value,
            parent_diameter_m=inputs.shell_inside_diameter.value,
            parent_provided_thickness_m=inputs.shell_provided_thickness.value,
            parent_required_thickness_m=parent_index["shell"].required_thickness_m,
            parent_check_id=parent_index["shell"].check_id,
            nozzle_provided_thickness_m=inputs.nozzle_provided_thickness.value,
            nozzle_required_thickness_m=nozzle_thickness_check.required_thickness_m,
            corrosion_allowance_m=inputs.corrosion_allowance.value,
            near_limit_threshold=near_limit_threshold,
        ),
        _build_ug37_reinforcement_check(
            check_id="UG-37-nozzle-head-reinforcement",
            parent_component="head",
            opening_diameter_m=inputs.nozzle_inside_diameter.value,
            parent_diameter_m=inputs.head_inside_diameter.value,
            parent_provided_thickness_m=inputs.head_provided_thickness.value,
            parent_required_thickness_m=parent_index["head"].required_thickness_m,
            parent_check_id=parent_index["head"].check_id,
            nozzle_provided_thickness_m=inputs.nozzle_provided_thickness.value,
            nozzle_required_thickness_m=nozzle_thickness_check.required_thickness_m,
            corrosion_allowance_m=inputs.corrosion_allowance.value,
            near_limit_threshold=near_limit_threshold,
        ),
    ]


def _build_ug37_reinforcement_check(
    *,
    check_id: str,
    parent_component: str,
    opening_diameter_m: float,
    parent_diameter_m: float,
    parent_provided_thickness_m: float,
    parent_required_thickness_m: float,
    parent_check_id: str,
    nozzle_provided_thickness_m: float,
    nozzle_required_thickness_m: float,
    corrosion_allowance_m: float,
    near_limit_threshold: float,
) -> CalculationRecord:
    """Build one UG-37 area-replacement check for a nozzle opening in a parent component."""
    parent_excess_m = max(parent_provided_thickness_m - parent_required_thickness_m, 0.0)
    nozzle_excess_m = max(nozzle_provided_thickness_m - nozzle_required_thickness_m, 0.0)

    # Deterministic UG-37/UG-45 reinforcement-area route:
    # required area is opening diameter multiplied by required parent thickness.
    # available area is parent excess area + nozzle excess area over an effective
    # reinforcement width related to opening and parent geometry.
    effective_half_width_m = min(0.5 * opening_diameter_m, (opening_diameter_m * parent_diameter_m) ** 0.5)
    available_area_m2 = (opening_diameter_m * parent_excess_m) + (2.0 * effective_half_width_m * nozzle_excess_m)
    required_area_m2 = opening_diameter_m * parent_required_thickness_m

    return _to_record(
        check_id=check_id,
        component="nozzle",
        parent_component=parent_component,
        formula=(
            "UG-37/UG-45 reinforcement area: A_req=d*t_r_parent; "
            "A_avail=d*max(t_parent-t_r_parent,0)+2*w*max(t_nozzle-t_r_nozzle,0), "
            "w=min(d/2,sqrt(d*D_parent))"
        ),
        inputs={
            "d_opening_m": opening_diameter_m,
            "D_parent_m": parent_diameter_m,
            "CA_m": corrosion_allowance_m,
            "t_parent_m": parent_provided_thickness_m,
            "t_required_parent_m": parent_required_thickness_m,
            "t_nozzle_m": nozzle_provided_thickness_m,
            "t_required_nozzle_m": nozzle_required_thickness_m,
            "w_effective_m": effective_half_width_m,
            "A_available_m2": available_area_m2,
        },
        required=required_area_m2,
        provided=available_area_m2,
        parent_check_id=parent_check_id,
        near_limit_threshold=near_limit_threshold,
    )


def _build_ug28_external_check(
    *,
    check_id: str,
    component: str,
    diameter_m: float,
    provided_thickness_m: float,
    corrosion_allowance_m: float,
    p_external_pa: float,
    near_limit_threshold: float,
) -> CalculationRecord:
    """Build one UG-28 external-pressure capacity check using the deterministic A/B-factor route."""
    # Deterministic UG-28 chart/equation route placeholder:
    # A-factor is computed from geometry; B-factor is selected via a bounded
    # monotonic interpolation to represent a chart lookup deterministically.
    e_modulus_pa = 200_000_000_000.0
    poisson_ratio = 0.3
    safety_factor = 3.0
    net_thickness_m = max(provided_thickness_m - corrosion_allowance_m, 0.0)
    a_factor = net_thickness_m / diameter_m if diameter_m > 0.0 else 0.0
    b_factor = min(0.95, max(0.2, 0.35 + (12.0 * a_factor)))
    elastic_critical_pa = (
        (2.0 * e_modulus_pa * (a_factor**3)) / (1.0 - (poisson_ratio**2)) if a_factor > 0.0 else 0.0
    )
    allowable_external_pa = (b_factor * elastic_critical_pa) / safety_factor

    return _to_record(
        check_id=check_id,
        component=component,
        formula=(
            "UG-28 deterministic route: A=(t-CA)/D, B=clip(0.35+12A,0.2,0.95), "
            "P_allow=(B*(2E*A^3/(1-nu^2)))/SF"
        ),
        inputs={
            "P_external_Pa": p_external_pa,
            "D_m": diameter_m,
            "t_m": provided_thickness_m,
            "CA_m": corrosion_allowance_m,
            "t_net_m": net_thickness_m,
            "A_factor": a_factor,
            "B_factor": b_factor,
            "E_modulus_Pa": e_modulus_pa,
            "poisson_ratio": poisson_ratio,
            "safety_factor": safety_factor,
        },
        required=p_external_pa,
        provided=provided_thickness_m,
        design_pressure_pa=p_external_pa,
        computed_mawp_pa=allowable_external_pa,
        near_limit_threshold=near_limit_threshold,
    )


def _to_record(
    *,
    check_id: str,
    component: str,
    formula: str,
    inputs: dict[str, float],
    required: float,
    provided: float,
    parent_component: str | None = None,
    parent_check_id: str | None = None,
    design_pressure_pa: float | None = None,
    computed_mawp_pa: float | None = None,
    near_limit_threshold: float = DEFAULT_NEAR_LIMIT_THRESHOLD,
) -> CalculationRecord:
    required_rounded = _round_safety_critical(required)
    provided_rounded = _round_safety_critical(provided)
    margin = _round_safety_critical(provided_rounded - required_rounded)
    utilization: float | None = None
    utilization_invalid_reason: str | None = None
    if provided_rounded > 0.0:
        utilization = _round_safety_critical(required_rounded / provided_rounded)
    else:
        utilization_invalid_reason = "provided_thickness_non_positive"
    is_near_limit = pass_status = False
    pressure_margin_pa = None
    if design_pressure_pa is None or computed_mawp_pa is None:
        pass_status = provided_rounded >= required_rounded
    else:
        pressure_margin_pa = _round_safety_critical(computed_mawp_pa - design_pressure_pa)
        pass_status = pressure_margin_pa >= 0.0
    is_near_limit = pass_status and utilization is not None and utilization >= near_limit_threshold
    clause_id = _CHECK_CLAUSE_MAP[check_id]
    validity_envelope = _build_validity_envelope_metadata(
        check_id=check_id,
        inputs=_model_domain_inputs_from_record_inputs(inputs),
    )

    canonical = {
        "check_id": check_id,
        "clause_id": clause_id,
        "component": component,
        "formula": formula,
        "inputs": inputs,
        "required_thickness_m": required_rounded,
        "provided_thickness_m": provided_rounded,
        "margin_m": margin,
        "utilization_ratio": utilization,
        "utilization_invalid_reason": utilization_invalid_reason,
        "near_limit_threshold": near_limit_threshold,
        "is_near_limit": is_near_limit,
        "parent_component": parent_component,
        "parent_check_id": parent_check_id,
        "design_pressure_pa": design_pressure_pa,
        "computed_mawp_pa": computed_mawp_pa,
        "pressure_margin_pa": pressure_margin_pa,
        "validity_envelope": validity_envelope,
        "pass_status": pass_status,
    }
    check_hash = _sha256_payload(canonical)

    return CalculationRecord(
        check_id=check_id,
        clause_id=clause_id,
        component=component,
        formula=formula,
        inputs=inputs,
        required_thickness_m=required_rounded,
        provided_thickness_m=provided_rounded,
        margin_m=margin,
        utilization_ratio=utilization,
        utilization_invalid_reason=utilization_invalid_reason,
        near_limit_threshold=near_limit_threshold,
        is_near_limit=is_near_limit,
        parent_component=parent_component,
        parent_check_id=parent_check_id,
        design_pressure_pa=design_pressure_pa,
        computed_mawp_pa=_round_safety_critical(computed_mawp_pa) if computed_mawp_pa is not None else None,
        pressure_margin_pa=pressure_margin_pa,
        validity_envelope=validity_envelope,
        pass_status=pass_status,
        reproducibility=ReproducibilityMetadata(
            canonical_payload_sha256=check_hash,
            hash_algorithm="sha256",
        ),
    )


def _build_non_conformances(checks: list[CalculationRecord]) -> list[NonConformanceEntry]:
    entries: list[NonConformanceEntry] = []
    for record in checks:
        if record.pass_status:
            continue

        if record.design_pressure_pa is not None and record.computed_mawp_pa is not None:
            pressure_key = "mawp" if record.check_id.endswith("-mawp") else "allowable_pressure"
            observed = f"{pressure_key}={record.computed_mawp_pa:.3f} Pa"
            required = f"minimum_design_pressure={record.design_pressure_pa:.3f} Pa"
        else:
            observed = f"provided={record.provided_thickness_m:.6f} m"
            required = f"minimum={record.required_thickness_m:.6f} m"

        entries.append(
            NonConformanceEntry(
                check_id=record.check_id,
                clause_id=record.clause_id,
                component=record.component,
                observed=observed,
                required=required,
                severity="major",
            )
        )

    return entries


def _to_si_pressure(quantity: Quantity) -> Quantity:
    unit = quantity.unit.lower()
    factors = {
        "pa": 1.0,
        "kpa": 1_000.0,
        "mpa": 1_000_000.0,
        "bar": 100_000.0,
    }
    if unit not in factors:
        raise ValueError(f"Unsupported pressure unit for BL-003: {quantity.unit}")
    return Quantity(value=_round_safety_critical(quantity.value * factors[unit]), unit="Pa")


def _to_si_length(quantity: Quantity) -> Quantity:
    unit = quantity.unit.lower()
    factors = {
        "m": 1.0,
        "mm": 0.001,
        "cm": 0.01,
    }
    if unit not in factors:
        raise ValueError(f"Unsupported length unit for BL-003: {quantity.unit}")
    return Quantity(value=_round_safety_critical(quantity.value * factors[unit]), unit="m")


def _sha256_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _external_pressure_from_requirements(requirement_set: RequirementSet) -> Quantity | None:
    external_pressure = requirement_set.requirements.get("external_pressure")
    if external_pressure is None:
        return None
    return Quantity(value=float(external_pressure.value), unit="Pa")


def _validate_model_domain_gate(inputs: SizingCheckInput, near_limit_threshold: float) -> None:
    if not (0.0 < inputs.joint_efficiency <= 1.0):
        raise ValueError("BL-003 model-domain gate failed: joint_efficiency must be in (0, 1].")

    if inputs.allowable_stress.value <= 0.0 or inputs.internal_pressure.value <= 0.0:
        raise ValueError(
            "BL-003 model-domain gate failed: allowable_stress and internal_pressure must be positive."
        )
    if not (0.0 < near_limit_threshold <= 1.0):
        raise ValueError("BL-003 model-domain gate failed: near_limit_threshold must be in (0, 1].")

    dimensional_values = {
        "shell_inside_diameter": inputs.shell_inside_diameter.value,
        "head_inside_diameter": inputs.head_inside_diameter.value,
        "nozzle_inside_diameter": inputs.nozzle_inside_diameter.value,
        "shell_provided_thickness": inputs.shell_provided_thickness.value,
        "head_provided_thickness": inputs.head_provided_thickness.value,
        "nozzle_provided_thickness": inputs.nozzle_provided_thickness.value,
    }
    for name, value in dimensional_values.items():
        if value <= 0.0:
            raise ValueError(f"BL-003 model-domain gate failed: {name} must be positive.")


def _model_domain_inputs(inputs: SizingCheckInput) -> dict[str, float]:
    domain_inputs = {
        "internal_pressure_pa": inputs.internal_pressure.value,
        "allowable_stress_pa": inputs.allowable_stress.value,
        "joint_efficiency": inputs.joint_efficiency,
        "corrosion_allowance_m": inputs.corrosion_allowance.value,
        "shell_inside_diameter_m": inputs.shell_inside_diameter.value,
        "shell_provided_thickness_m": inputs.shell_provided_thickness.value,
        "head_inside_diameter_m": inputs.head_inside_diameter.value,
        "head_provided_thickness_m": inputs.head_provided_thickness.value,
        "nozzle_inside_diameter_m": inputs.nozzle_inside_diameter.value,
        "nozzle_provided_thickness_m": inputs.nozzle_provided_thickness.value,
    }
    if inputs.external_pressure is not None:
        domain_inputs["external_pressure_pa"] = inputs.external_pressure.value
    return domain_inputs


def _model_domain_inputs_from_record_inputs(record_inputs: dict[str, float]) -> dict[str, float]:
    field_map = {
        "P_Pa": "internal_pressure_pa",
        "S_Pa": "allowable_stress_pa",
        "E": "joint_efficiency",
        "CA_m": "corrosion_allowance_m",
        "D_m": "shell_inside_diameter_m",
        "d_m": "nozzle_inside_diameter_m",
        "t_m": "shell_provided_thickness_m",
        "P_external_Pa": "external_pressure_pa",
    }
    normalized: dict[str, float] = {}
    for key, value in record_inputs.items():
        mapped = field_map.get(key)
        if mapped is not None:
            normalized[mapped] = value

    # Some check routes overload D_m/t_m for head/nozzle. Keep deterministic
    # aliases so validity-envelope metadata can project the expected key names.
    if "D_m" in record_inputs and "P_Pa" in record_inputs and "head_inside_diameter_m" not in normalized:
        normalized["head_inside_diameter_m"] = record_inputs["D_m"]
    if "D_m" in record_inputs and "t_m" in record_inputs and "head_inside_diameter_m" not in normalized:
        normalized["head_inside_diameter_m"] = record_inputs["D_m"]
    if "d_m" in record_inputs and "t_m" in record_inputs:
        normalized["nozzle_provided_thickness_m"] = record_inputs["t_m"]
    if "t_m" in record_inputs:
        normalized["shell_provided_thickness_m"] = record_inputs["t_m"]
        normalized["head_provided_thickness_m"] = record_inputs["t_m"]
        normalized["nozzle_provided_thickness_m"] = record_inputs["t_m"]
    if "D_parent_m" in record_inputs:
        normalized["shell_inside_diameter_m"] = record_inputs["D_parent_m"]
        normalized["head_inside_diameter_m"] = record_inputs["D_parent_m"]
    if "d_opening_m" in record_inputs:
        normalized["nozzle_inside_diameter_m"] = record_inputs["d_opening_m"]
    if "t_parent_m" in record_inputs:
        normalized["shell_provided_thickness_m"] = record_inputs["t_parent_m"]
        normalized["head_provided_thickness_m"] = record_inputs["t_parent_m"]
    if "t_nozzle_m" in record_inputs:
        normalized["nozzle_provided_thickness_m"] = record_inputs["t_nozzle_m"]
    return normalized


def _planned_check_ids(inputs: SizingCheckInput) -> list[str]:
    check_ids = [
        "UG-27-shell",
        "UG-32-head",
        "UG-45-nozzle",
        "UG-27-shell-mawp",
        "UG-32-head-mawp",
        "UG-45-nozzle-mawp",
        "UG-37-nozzle-shell-reinforcement",
        "UG-37-nozzle-head-reinforcement",
    ]
    if inputs.external_pressure is not None:
        check_ids.extend(["UG-28-shell-external", "UG-28-head-external"])
    return check_ids


def _validate_validity_envelopes(inputs: SizingCheckInput) -> None:
    domain_inputs = _model_domain_inputs(inputs)
    for check_id in _planned_check_ids(inputs):
        envelope = _MODEL_VALIDITY_ENVELOPES[check_id]
        for input_name, bounds in envelope["bounds"].items():
            value = domain_inputs[input_name]
            if value < bounds["min"] or value > bounds["max"]:
                raise ValueError(
                    "BL-003 model-domain gate failed: "
                    f"{check_id} input {input_name}={value} is outside validity envelope "
                    f"[{bounds['min']}, {bounds['max']}]."
                )


def _build_validity_envelope_metadata(check_id: str, inputs: dict[str, float]) -> dict[str, Any]:
    envelope = _MODEL_VALIDITY_ENVELOPES[check_id]
    declared_bounds = envelope["bounds"]
    evaluated_inputs = {name: inputs[name] for name in declared_bounds}
    return {
        "model_id": envelope["model_id"],
        "status": "in_envelope",
        "bounds": declared_bounds,
        "evaluated_inputs": evaluated_inputs,
    }
