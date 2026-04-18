"""Deterministic ASME Div 1 sizing checks for BL-003."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from .design_basis_pipeline import DesignBasis
from .requirements_pipeline import RequirementSet

CALCULATION_RECORDS_VERSION = "CalculationRecords.v1"
NON_CONFORMANCE_LIST_VERSION = "NonConformanceList.v1"

_EXPECTED_REQUIREMENT_UNITS = {
    "design_pressure": "Pa",
    "corrosion_allowance": "mm",
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


@dataclass(frozen=True)
class CalculationRecord:
    check_id: str
    component: str
    formula: str
    inputs: dict[str, float]
    required_thickness_m: float
    provided_thickness_m: float
    pass_status: bool
    reproducibility: ReproducibilityMetadata

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "component": self.component,
            "formula": self.formula,
            "inputs": self.inputs,
            "required_thickness_m": self.required_thickness_m,
            "provided_thickness_m": self.provided_thickness_m,
            "pass_status": self.pass_status,
            "reproducibility": self.reproducibility.to_json_dict(),
        }


@dataclass(frozen=True)
class NonConformanceEntry:
    check_id: str
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
    checks: list[CalculationRecord]
    deterministic_hash: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at_utc": self.generated_at_utc,
            "source_requirement_set_hash": self.source_requirement_set_hash,
            "source_design_basis_signature": self.source_design_basis_signature,
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
    sizing_input: SizingCheckInput | None = None,
    *,
    now_utc: datetime | None = None,
) -> tuple[CalculationRecordsArtifact, NonConformanceListArtifact]:
    """Run deterministic shell/head/nozzle sizing checks for BL-003 MVP."""
    _validate_handoff_gate(requirement_set=requirement_set, design_basis=design_basis)

    generated_at = (now_utc or datetime.now(tz=timezone.utc)).replace(microsecond=0).isoformat()
    normalized_input = _normalize_and_resolve_inputs(requirement_set, sizing_input)

    checks = [
        _build_shell_check(normalized_input),
        _build_head_check(normalized_input),
        _build_nozzle_check(normalized_input),
    ]

    calc_payload = {
        "schema_version": CALCULATION_RECORDS_VERSION,
        "generated_at_utc": generated_at,
        "source_requirement_set_hash": requirement_set.deterministic_hash,
        "source_design_basis_signature": design_basis.deterministic_signature,
        "checks": [record.to_json_dict() for record in checks],
    }
    calc_hash = _sha256_payload(calc_payload)

    calc_artifact = CalculationRecordsArtifact(
        schema_version=CALCULATION_RECORDS_VERSION,
        generated_at_utc=generated_at,
        source_requirement_set_hash=requirement_set.deterministic_hash,
        source_design_basis_signature=design_basis.deterministic_signature,
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


def _validate_handoff_gate(requirement_set: RequirementSet, design_basis: DesignBasis) -> None:
    if requirement_set.downstream_blocked:
        raise ValueError("BL-003 handoff gate failed: requirement_set.downstream_blocked must be false.")
    if requirement_set.unresolved_gaps:
        raise ValueError("BL-003 handoff gate failed: requirement_set.unresolved_gaps must be empty.")
    if design_basis.primary_standard != "ASME Section VIII Division 1":
        raise ValueError("BL-003 MVP supports only ASME Section VIII Division 1 design basis.")

    for field, expected_unit in _EXPECTED_REQUIREMENT_UNITS.items():
        if field in requirement_set.requirements and requirement_set.requirements[field].unit != expected_unit:
            raise ValueError(
                f"BL-003 handoff gate failed: expected {field} unit {expected_unit}, "
                f"got {requirement_set.requirements[field].unit}."
            )


def _normalize_and_resolve_inputs(
    requirement_set: RequirementSet,
    sizing_input: SizingCheckInput | None,
) -> SizingCheckInput:
    if sizing_input is not None:
        return SizingCheckInput(
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
        )

    pressure_pa = float(requirement_set.requirements["design_pressure"].value)
    corrosion = requirement_set.requirements.get("corrosion_allowance")
    ca_mm = float(corrosion.value) if corrosion else 1.5
    ca_m = round(ca_mm / 1000.0, 9)

    return SizingCheckInput(
        internal_pressure=Quantity(value=pressure_pa, unit="Pa"),
        allowable_stress=Quantity(value=138_000_000.0, unit="Pa"),
        joint_efficiency=0.85,
        corrosion_allowance=Quantity(value=ca_m, unit="m"),
        shell_inside_diameter=Quantity(value=2.0, unit="m"),
        shell_provided_thickness=Quantity(value=0.020, unit="m"),
        head_inside_diameter=Quantity(value=2.0, unit="m"),
        head_provided_thickness=Quantity(value=0.018, unit="m"),
        nozzle_inside_diameter=Quantity(value=0.35, unit="m"),
        nozzle_provided_thickness=Quantity(value=0.004, unit="m"),
    )


def _build_shell_check(inputs: SizingCheckInput) -> CalculationRecord:
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
    )


def _build_head_check(inputs: SizingCheckInput) -> CalculationRecord:
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
    )


def _build_nozzle_check(inputs: SizingCheckInput) -> CalculationRecord:
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
    )


def _to_record(
    *,
    check_id: str,
    component: str,
    formula: str,
    inputs: dict[str, float],
    required: float,
    provided: float,
) -> CalculationRecord:
    required_rounded = round(required, 9)
    provided_rounded = round(provided, 9)
    pass_status = provided_rounded >= required_rounded

    canonical = {
        "check_id": check_id,
        "component": component,
        "formula": formula,
        "inputs": inputs,
        "required_thickness_m": required_rounded,
        "provided_thickness_m": provided_rounded,
        "pass_status": pass_status,
    }
    check_hash = _sha256_payload(canonical)

    return CalculationRecord(
        check_id=check_id,
        component=component,
        formula=formula,
        inputs=inputs,
        required_thickness_m=required_rounded,
        provided_thickness_m=provided_rounded,
        pass_status=pass_status,
        reproducibility=ReproducibilityMetadata(
            canonical_payload_sha256=check_hash,
            hash_algorithm="sha256",
        ),
    )


def _build_non_conformances(checks: list[CalculationRecord]) -> list[NonConformanceEntry]:
    return [
        NonConformanceEntry(
            check_id=record.check_id,
            component=record.component,
            observed=f"provided={record.provided_thickness_m:.6f} m",
            required=f"minimum={record.required_thickness_m:.6f} m",
            severity="major",
        )
        for record in checks
        if not record.pass_status
    ]


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
    return Quantity(value=round(quantity.value * factors[unit], 9), unit="Pa")


def _to_si_length(quantity: Quantity) -> Quantity:
    unit = quantity.unit.lower()
    factors = {
        "m": 1.0,
        "mm": 0.001,
        "cm": 0.01,
    }
    if unit not in factors:
        raise ValueError(f"Unsupported length unit for BL-003: {quantity.unit}")
    return Quantity(value=round(quantity.value * factors[unit], 9), unit="m")


def _sha256_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
