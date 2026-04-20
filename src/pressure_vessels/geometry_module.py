"""Deterministic geometry/CAD schema, adapters, and export artifacts for BL-014."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any

GEOMETRY_INPUT_VERSION = "GeometryInput.v1"
CAD_PARAMETER_EXPORT_VERSION = "CadReadyParameterExport.v1"


class GeometryInputValidationError(ValueError):
    """Raised when geometry inputs fail deterministic field-level validation."""

    def __init__(self, failures: dict[str, str]):
        self.failures = failures
        details = "; ".join(f"{field}: {reason}" for field, reason in sorted(failures.items()))
        super().__init__(f"BL-014 geometry validation failed: {details}")


@dataclass(frozen=True)
class GeometryInput:
    schema_version: str
    geometry_revision_id: str
    source_system: str
    source_model_sha256: str
    shell_inside_diameter_m: float
    shell_provided_thickness_m: float
    head_inside_diameter_m: float
    head_provided_thickness_m: float
    nozzle_inside_diameter_m: float
    nozzle_provided_thickness_m: float
    external_pressure_pa: float | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CadReadyParameterExport:
    schema_version: str
    geometry_revision_id: str
    source_system: str
    source_model_sha256: str
    source_calculation_records_hash: str
    parameters: dict[str, float]
    deterministic_hash: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


_REQUIRED_GEOMETRY_FIELDS = (
    "shell_inside_diameter_m",
    "shell_provided_thickness_m",
    "head_inside_diameter_m",
    "head_provided_thickness_m",
    "nozzle_inside_diameter_m",
    "nozzle_provided_thickness_m",
)

_OPTIONAL_NON_NEGATIVE_FIELDS = ("external_pressure_pa",)


def _validate_and_normalize_geometry_numeric_fields(
    geometry_input: GeometryInput,
) -> dict[str, float | None]:
    failures: dict[str, str] = {}
    normalized: dict[str, float | None] = {}

    for field in _REQUIRED_GEOMETRY_FIELDS:
        value = getattr(geometry_input, field)
        if value is None:
            failures[field] = "null value is not allowed."
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            failures[field] = f"non-numeric value {value!r}."
            continue
        if numeric <= 0.0:
            failures[field] = f"out-of-range value {numeric}; expected > 0."
            continue
        normalized[field] = numeric

    for field in _OPTIONAL_NON_NEGATIVE_FIELDS:
        value = getattr(geometry_input, field)
        if value is None:
            normalized[field] = None
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            failures[field] = f"non-numeric value {value!r}."
            continue
        if numeric < 0.0:
            failures[field] = f"out-of-range value {numeric}; expected >= 0."
            continue
        normalized[field] = numeric

    if failures:
        raise GeometryInputValidationError(failures)
    return normalized


def adapt_geometry_input(geometry_input: GeometryInput) -> dict[str, float | None]:
    """Return canonical geometry sizing payload used by the calculation pipeline."""
    if geometry_input.schema_version != GEOMETRY_INPUT_VERSION:
        raise ValueError("BL-014 geometry adapter failed: unsupported geometry schema version.")
    if not geometry_input.geometry_revision_id:
        raise ValueError("BL-014 geometry adapter failed: geometry_revision_id is required.")
    if not geometry_input.source_model_sha256:
        raise ValueError("BL-014 geometry adapter failed: source_model_sha256 is required.")

    return _validate_and_normalize_geometry_numeric_fields(geometry_input)


def build_cad_ready_parameter_export(
    geometry_input: GeometryInput,
    *,
    calculation_records_hash: str,
) -> CadReadyParameterExport:
    """Create deterministic CAD-ready parameter export linked to calculation evidence."""
    validated_fields = _validate_and_normalize_geometry_numeric_fields(geometry_input)
    parameters = {
        "head_inside_diameter_m": validated_fields["head_inside_diameter_m"],
        "head_provided_thickness_m": validated_fields["head_provided_thickness_m"],
        "nozzle_inside_diameter_m": validated_fields["nozzle_inside_diameter_m"],
        "nozzle_provided_thickness_m": validated_fields["nozzle_provided_thickness_m"],
        "shell_inside_diameter_m": validated_fields["shell_inside_diameter_m"],
        "shell_provided_thickness_m": validated_fields["shell_provided_thickness_m"],
    }
    if validated_fields["external_pressure_pa"] is not None:
        parameters["external_pressure_pa"] = validated_fields["external_pressure_pa"]

    payload = {
        "schema_version": CAD_PARAMETER_EXPORT_VERSION,
        "geometry_revision_id": geometry_input.geometry_revision_id,
        "source_system": geometry_input.source_system,
        "source_model_sha256": geometry_input.source_model_sha256,
        "source_calculation_records_hash": calculation_records_hash,
        "parameters": parameters,
    }
    return CadReadyParameterExport(
        schema_version=CAD_PARAMETER_EXPORT_VERSION,
        geometry_revision_id=geometry_input.geometry_revision_id,
        source_system=geometry_input.source_system,
        source_model_sha256=geometry_input.source_model_sha256,
        source_calculation_records_hash=calculation_records_hash,
        parameters=parameters,
        deterministic_hash=_sha256_payload(payload),
    )


def _sha256_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
