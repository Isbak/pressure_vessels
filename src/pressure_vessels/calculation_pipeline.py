"""Deterministic ASME Div 1 sizing checks for BL-003."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from .design_basis_pipeline import ApplicabilityMatrix, DesignBasis
from .requirements_pipeline import CANONICAL_UNITS, RequirementSet

CALCULATION_RECORDS_VERSION = "CalculationRecords.v1"
NON_CONFORMANCE_LIST_VERSION = "NonConformanceList.v1"

# BL-003 MVP placeholder defaults used when sizing_input is not supplied.
# These are surfaced in the CalculationRecordsArtifact.applied_defaults section
# so that every pass/fail outcome is traceable to an explicit assumption.
_MVP_DEFAULTS = {
    "allowable_stress_Pa": 138_000_000.0,
    "joint_efficiency": 0.85,
    "shell_inside_diameter_m": 2.0,
    "shell_provided_thickness_m": 0.020,
    "head_inside_diameter_m": 2.0,
    "head_provided_thickness_m": 0.018,
    "nozzle_inside_diameter_m": 0.35,
    "nozzle_provided_thickness_m": 0.004,
    "corrosion_allowance_fallback_mm": 1.5,
    "source": "BL-003 MVP placeholder; replace with Materials Module outputs.",
}

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
    utilization_ratio: float
    pass_status: bool
    reproducibility: ReproducibilityMetadata
    design_pressure_pa: float | None = None
    computed_mawp_pa: float | None = None
    pressure_margin_pa: float | None = None

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
            "design_pressure_pa": self.design_pressure_pa,
            "computed_mawp_pa": self.computed_mawp_pa,
            "pressure_margin_pa": self.pressure_margin_pa,
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
    applied_defaults: dict[str, Any]
    checks: list[CalculationRecord]
    deterministic_hash: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at_utc": self.generated_at_utc,
            "source_requirement_set_hash": self.source_requirement_set_hash,
            "source_design_basis_signature": self.source_design_basis_signature,
            "source_applicability_matrix_hash": self.source_applicability_matrix_hash,
            "applied_defaults": self.applied_defaults,
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
    *,
    now_utc: datetime | None = None,
) -> tuple[CalculationRecordsArtifact, NonConformanceListArtifact]:
    """Run deterministic shell/head/nozzle sizing checks for BL-003 MVP."""
    _validate_handoff_gate(
        requirement_set=requirement_set,
        design_basis=design_basis,
        applicability_matrix=applicability_matrix,
    )

    generated_at = (now_utc or datetime.now(tz=timezone.utc)).replace(microsecond=0).isoformat()
    normalized_input, applied_defaults = _normalize_and_resolve_inputs(requirement_set, sizing_input)

    checks = [
        _build_shell_check(normalized_input),
        _build_head_check(normalized_input),
        _build_nozzle_check(normalized_input),
        _build_shell_mawp_check(normalized_input),
        _build_head_mawp_check(normalized_input),
        _build_nozzle_mawp_check(normalized_input),
    ]
    checks.extend(_build_external_pressure_checks(normalized_input))

    _validate_clause_coverage(checks, applicability_matrix)

    calc_payload = {
        "schema_version": CALCULATION_RECORDS_VERSION,
        "generated_at_utc": generated_at,
        "source_requirement_set_hash": requirement_set.deterministic_hash,
        "source_design_basis_signature": design_basis.deterministic_signature,
        "source_applicability_matrix_hash": applicability_matrix.deterministic_hash,
        "applied_defaults": applied_defaults,
        "checks": [record.to_json_dict() for record in checks],
    }
    calc_hash = _sha256_payload(calc_payload)

    calc_artifact = CalculationRecordsArtifact(
        schema_version=CALCULATION_RECORDS_VERSION,
        generated_at_utc=generated_at,
        source_requirement_set_hash=requirement_set.deterministic_hash,
        source_design_basis_signature=design_basis.deterministic_signature,
        source_applicability_matrix_hash=applicability_matrix.deterministic_hash,
        applied_defaults=applied_defaults,
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
) -> tuple[SizingCheckInput, dict[str, Any]]:
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
        applied_defaults = {"applied_mvp_defaults": False, "values": {}, "source": "caller-provided"}
        return normalized, applied_defaults

    pressure_pa = float(requirement_set.requirements["design_pressure"].value)
    corrosion = requirement_set.requirements.get("corrosion_allowance")
    ca_mm = float(corrosion.value) if corrosion else _MVP_DEFAULTS["corrosion_allowance_fallback_mm"]
    ca_m = round(ca_mm / 1000.0, 9)

    normalized = SizingCheckInput(
        internal_pressure=Quantity(value=pressure_pa, unit="Pa"),
        allowable_stress=Quantity(value=_MVP_DEFAULTS["allowable_stress_Pa"], unit="Pa"),
        joint_efficiency=_MVP_DEFAULTS["joint_efficiency"],
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
        "applied_mvp_defaults": True,
        "values": dict(_MVP_DEFAULTS),
        "source": _MVP_DEFAULTS["source"],
    }
    return normalized, applied_defaults


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


def _build_shell_mawp_check(inputs: SizingCheckInput) -> CalculationRecord:
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
    )


def _build_head_mawp_check(inputs: SizingCheckInput) -> CalculationRecord:
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
    )


def _build_nozzle_mawp_check(inputs: SizingCheckInput) -> CalculationRecord:
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
    )


def _build_external_pressure_checks(inputs: SizingCheckInput) -> list[CalculationRecord]:
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
        ),
        _build_ug28_external_check(
            check_id="UG-28-head-external",
            component="head",
            diameter_m=inputs.head_inside_diameter.value,
            provided_thickness_m=inputs.head_provided_thickness.value,
            corrosion_allowance_m=inputs.corrosion_allowance.value,
            p_external_pa=p_external,
        ),
    ]
    return checks


def _build_ug28_external_check(
    *,
    check_id: str,
    component: str,
    diameter_m: float,
    provided_thickness_m: float,
    corrosion_allowance_m: float,
    p_external_pa: float,
) -> CalculationRecord:
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
    )


def _to_record(
    *,
    check_id: str,
    component: str,
    formula: str,
    inputs: dict[str, float],
    required: float,
    provided: float,
    design_pressure_pa: float | None = None,
    computed_mawp_pa: float | None = None,
) -> CalculationRecord:
    required_rounded = round(required, 9)
    provided_rounded = round(provided, 9)
    margin = round(provided_rounded - required_rounded, 9)
    utilization = round(required_rounded / provided_rounded, 9) if provided_rounded > 0.0 else float("inf")
    pressure_margin_pa = None
    if design_pressure_pa is None or computed_mawp_pa is None:
        pass_status = provided_rounded >= required_rounded
    else:
        pressure_margin_pa = round(computed_mawp_pa - design_pressure_pa, 9)
        pass_status = pressure_margin_pa >= 0.0
    clause_id = _CHECK_CLAUSE_MAP[check_id]

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
        "design_pressure_pa": design_pressure_pa,
        "computed_mawp_pa": computed_mawp_pa,
        "pressure_margin_pa": pressure_margin_pa,
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
        design_pressure_pa=design_pressure_pa,
        computed_mawp_pa=round(computed_mawp_pa, 9) if computed_mawp_pa is not None else None,
        pressure_margin_pa=pressure_margin_pa,
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


def _external_pressure_from_requirements(requirement_set: RequirementSet) -> Quantity | None:
    external_pressure = requirement_set.requirements.get("external_pressure")
    if external_pressure is None:
        return None
    return Quantity(value=float(external_pressure.value), unit="Pa")
