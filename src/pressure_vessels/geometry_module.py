"""Deterministic geometry/CAD schema, adapters, and export artifacts for BL-014."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any

GEOMETRY_INPUT_VERSION = "GeometryInput.v1"
CAD_PARAMETER_EXPORT_VERSION = "CadReadyParameterExport.v1"


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


def adapt_geometry_input(geometry_input: GeometryInput) -> dict[str, float | None]:
    """Return canonical geometry sizing payload used by the calculation pipeline."""
    if geometry_input.schema_version != GEOMETRY_INPUT_VERSION:
        raise ValueError("BL-014 geometry adapter failed: unsupported geometry schema version.")
    if not geometry_input.geometry_revision_id:
        raise ValueError("BL-014 geometry adapter failed: geometry_revision_id is required.")
    if not geometry_input.source_model_sha256:
        raise ValueError("BL-014 geometry adapter failed: source_model_sha256 is required.")

    payload = {
        "shell_inside_diameter_m": float(geometry_input.shell_inside_diameter_m),
        "shell_provided_thickness_m": float(geometry_input.shell_provided_thickness_m),
        "head_inside_diameter_m": float(geometry_input.head_inside_diameter_m),
        "head_provided_thickness_m": float(geometry_input.head_provided_thickness_m),
        "nozzle_inside_diameter_m": float(geometry_input.nozzle_inside_diameter_m),
        "nozzle_provided_thickness_m": float(geometry_input.nozzle_provided_thickness_m),
        "external_pressure_pa": (
            None
            if geometry_input.external_pressure_pa is None
            else float(geometry_input.external_pressure_pa)
        ),
    }
    return payload


def build_cad_ready_parameter_export(
    geometry_input: GeometryInput,
    *,
    calculation_records_hash: str,
) -> CadReadyParameterExport:
    """Create deterministic CAD-ready parameter export linked to calculation evidence."""
    parameters = {
        "head_inside_diameter_m": float(geometry_input.head_inside_diameter_m),
        "head_provided_thickness_m": float(geometry_input.head_provided_thickness_m),
        "nozzle_inside_diameter_m": float(geometry_input.nozzle_inside_diameter_m),
        "nozzle_provided_thickness_m": float(geometry_input.nozzle_provided_thickness_m),
        "shell_inside_diameter_m": float(geometry_input.shell_inside_diameter_m),
        "shell_provided_thickness_m": float(geometry_input.shell_provided_thickness_m),
    }
    if geometry_input.external_pressure_pa is not None:
        parameters["external_pressure_pa"] = float(geometry_input.external_pressure_pa)

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
