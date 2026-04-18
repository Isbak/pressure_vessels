"""Deterministic design basis + applicability matrix generation for BL-002/BL-009."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from .requirements_pipeline import RequirementSet

DESIGN_BASIS_VERSION = "DesignBasis.v1"
APPLICABILITY_MATRIX_VERSION = "ApplicabilityMatrix.v1"

_REQUIRED_FIELDS = (
    "fluid",
    "design_pressure",
    "design_temperature",
    "capacity",
    "code_standard",
)


@dataclass(frozen=True)
class StandardRouteConfig:
    route_id: str
    standard_name: str
    standard_version: str
    aliases: tuple[str, ...]
    route_priority: int


@dataclass(frozen=True)
class RouteSelectionRecord:
    route_id: str
    standard_name: str
    standard_version: str
    route_priority: int
    matched_input: bool
    selected: bool
    selection_reason: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClauseApplicabilityRecord:
    clause_id: str
    standard_route_id: str
    applicable: bool
    justification: str
    evidence_fields: list[str]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "clause_id": self.clause_id,
            "standard_route_id": self.standard_route_id,
            "applicable": self.applicable,
            "justification": self.justification,
            "evidence_fields": self.evidence_fields,
        }


@dataclass(frozen=True)
class ApplicabilityMatrix:
    schema_version: str
    generated_at_utc: str
    source_requirement_set_hash: str
    primary_standard: str
    primary_standard_version: str
    selected_route_id: str
    records: list[ClauseApplicabilityRecord]
    deterministic_hash: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at_utc": self.generated_at_utc,
            "source_requirement_set_hash": self.source_requirement_set_hash,
            "primary_standard": self.primary_standard,
            "primary_standard_version": self.primary_standard_version,
            "selected_route_id": self.selected_route_id,
            "records": [r.to_json_dict() for r in self.records],
            "deterministic_hash": self.deterministic_hash,
        }


@dataclass(frozen=True)
class DesignBasis:
    schema_version: str
    generated_at_utc: str
    source_requirement_set_hash: str
    primary_standard: str
    primary_standard_version: str
    selected_route_id: str
    secondary_standards: list[str]
    route_selection_audit: list[RouteSelectionRecord]
    assumptions: list[str]
    deterministic_signature: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at_utc": self.generated_at_utc,
            "source_requirement_set_hash": self.source_requirement_set_hash,
            "primary_standard": self.primary_standard,
            "primary_standard_version": self.primary_standard_version,
            "selected_route_id": self.selected_route_id,
            "secondary_standards": self.secondary_standards,
            "route_selection_audit": [record.to_json_dict() for record in self.route_selection_audit],
            "assumptions": self.assumptions,
            "deterministic_signature": self.deterministic_signature,
        }


_DEFAULT_ROUTE_CONFIGS: tuple[StandardRouteConfig, ...] = (
    StandardRouteConfig(
        route_id="route_asme_viii_div1",
        standard_name="ASME Section VIII Division 1",
        standard_version="ASME_BPVC_2023",
        aliases=("ASME SECTION VIII DIV 1", "ASME VIII-1"),
        route_priority=100,
    ),
    StandardRouteConfig(
        route_id="route_ped_en13445",
        standard_name="PED (EN 13445)",
        standard_version="PED_2014_68_EU_EN13445_2021",
        aliases=(
            "PED",
            "PED EN 13445",
            "PRESSURE EQUIPMENT DIRECTIVE",
            "EN 13445",
        ),
        route_priority=200,
    ),
)


def build_design_basis(
    requirement_set: RequirementSet,
    now_utc: datetime | None = None,
    route_configs: tuple[StandardRouteConfig, ...] | None = None,
) -> tuple[DesignBasis, ApplicabilityMatrix]:
    """Build deterministic BL-002/BL-009 artifacts from a valid RequirementSet.v1."""
    _validate_handoff_gate(requirement_set)

    generated_at = (now_utc or datetime.now(tz=timezone.utc)).replace(microsecond=0).isoformat()
    configured_routes = tuple(sorted(route_configs or _DEFAULT_ROUTE_CONFIGS, key=lambda r: (r.route_priority, r.route_id)))

    raw_standard = str(requirement_set.requirements["code_standard"].value)
    selected_route, route_audit = _select_route(raw_standard, configured_routes)
    secondary_standards = [
        f"{route.standard_name}:{route.standard_version}"
        for route in configured_routes
        if route.route_id != selected_route.route_id
    ]

    matrix_records = _build_clause_records_for_route(requirement_set, selected_route.route_id)
    matrix_canonical = {
        "schema_version": APPLICABILITY_MATRIX_VERSION,
        "generated_at_utc": generated_at,
        "source_requirement_set_hash": requirement_set.deterministic_hash,
        "primary_standard": selected_route.standard_name,
        "primary_standard_version": selected_route.standard_version,
        "selected_route_id": selected_route.route_id,
        "records": [asdict(r) for r in matrix_records],
    }
    matrix_hash = _sha256_payload(matrix_canonical)

    matrix = ApplicabilityMatrix(
        schema_version=APPLICABILITY_MATRIX_VERSION,
        generated_at_utc=generated_at,
        source_requirement_set_hash=requirement_set.deterministic_hash,
        primary_standard=selected_route.standard_name,
        primary_standard_version=selected_route.standard_version,
        selected_route_id=selected_route.route_id,
        records=matrix_records,
        deterministic_hash=matrix_hash,
    )

    assumptions = [
        "Deterministic route selection uses priority then route_id tie-break with canonical code_standard aliases.",
        "Internal pressure basis is assumed unless external pressure input is provided.",
    ]

    design_basis_unsigned = {
        "schema_version": DESIGN_BASIS_VERSION,
        "generated_at_utc": generated_at,
        "source_requirement_set_hash": requirement_set.deterministic_hash,
        "primary_standard": selected_route.standard_name,
        "primary_standard_version": selected_route.standard_version,
        "selected_route_id": selected_route.route_id,
        "secondary_standards": secondary_standards,
        "route_selection_audit": [record.to_json_dict() for record in route_audit],
        "assumptions": assumptions,
    }
    signature = _sha256_payload(design_basis_unsigned)

    design_basis = DesignBasis(
        schema_version=DESIGN_BASIS_VERSION,
        generated_at_utc=generated_at,
        source_requirement_set_hash=requirement_set.deterministic_hash,
        primary_standard=selected_route.standard_name,
        primary_standard_version=selected_route.standard_version,
        selected_route_id=selected_route.route_id,
        secondary_standards=secondary_standards,
        route_selection_audit=route_audit,
        assumptions=assumptions,
        deterministic_signature=signature,
    )

    return design_basis, matrix


def _validate_handoff_gate(requirement_set: RequirementSet) -> None:
    if requirement_set.downstream_blocked:
        raise ValueError("BL-001 handoff gate failed: downstream_blocked must be false.")

    if requirement_set.unresolved_gaps:
        raise ValueError("BL-001 handoff gate failed: unresolved_gaps must be empty.")

    missing_fields = [field for field in _REQUIRED_FIELDS if field not in requirement_set.requirements]
    if missing_fields:
        raise ValueError(
            "BL-001 handoff gate failed: missing required normalized fields "
            f"{', '.join(missing_fields)}."
        )


def _select_route(
    code_standard_value: str,
    route_configs: tuple[StandardRouteConfig, ...],
) -> tuple[StandardRouteConfig, list[RouteSelectionRecord]]:
    canonical = " ".join(code_standard_value.strip().upper().split())
    matches = [route for route in route_configs if canonical in route.aliases]

    if not matches:
        supported = ", ".join(sorted({alias for route in route_configs for alias in route.aliases}))
        raise ValueError(
            "Unsupported code_standard for BL-009 route engine; expected one of configured aliases: "
            f"{supported}."
        )

    selected = sorted(matches, key=lambda route: (route.route_priority, route.route_id))[0]
    route_audit = [
        RouteSelectionRecord(
            route_id=route.route_id,
            standard_name=route.standard_name,
            standard_version=route.standard_version,
            route_priority=route.route_priority,
            matched_input=route in matches,
            selected=route.route_id == selected.route_id,
            selection_reason=(
                "Selected: matched input and won deterministic priority/order tie-break."
                if route.route_id == selected.route_id
                else (
                    "Matched input but lower selection precedence than chosen route."
                    if route in matches
                    else "Configured route did not match canonical code_standard input."
                )
            ),
        )
        for route in route_configs
    ]
    return selected, route_audit


def _build_clause_records_for_route(
    requirement_set: RequirementSet,
    route_id: str,
) -> list[ClauseApplicabilityRecord]:
    if route_id == "route_asme_viii_div1":
        return _build_asme_clause_records(requirement_set, route_id=route_id)
    if route_id == "route_ped_en13445":
        return _build_ped_clause_records(requirement_set, route_id=route_id)

    raise ValueError(f"No clause routing implementation for standard route: {route_id}.")


def _build_asme_clause_records(
    requirement_set: RequirementSet,
    *,
    route_id: str,
) -> list[ClauseApplicabilityRecord]:
    pressure = float(requirement_set.requirements["design_pressure"].value)
    temperature = float(requirement_set.requirements["design_temperature"].value)
    has_corrosion_allowance = "corrosion_allowance" in requirement_set.requirements
    has_external_pressure = "external_pressure" in requirement_set.requirements

    records = [
        ClauseApplicabilityRecord(
            clause_id="UG-16",
            standard_route_id=route_id,
            applicable=True,
            justification="Applicable because design pressure is defined for pressure boundary sizing.",
            evidence_fields=["design_pressure", "code_standard"],
        ),
        ClauseApplicabilityRecord(
            clause_id="UG-20",
            standard_route_id=route_id,
            applicable=True,
            justification="Applicable because design temperature is defined for material selection limits.",
            evidence_fields=["design_temperature", "code_standard"],
        ),
        ClauseApplicabilityRecord(
            clause_id="UG-25",
            standard_route_id=route_id,
            applicable=has_corrosion_allowance,
            justification=(
                "Applicable because corrosion allowance input is provided."
                if has_corrosion_allowance
                else "Not applicable because corrosion allowance input is absent."
            ),
            evidence_fields=["corrosion_allowance"] if has_corrosion_allowance else ["requirements"],
        ),
        ClauseApplicabilityRecord(
            clause_id="UG-27",
            standard_route_id=route_id,
            applicable=True,
            justification="Applicable because cylindrical shell thickness under internal pressure must be verified.",
            evidence_fields=["design_pressure", "code_standard"],
        ),
        ClauseApplicabilityRecord(
            clause_id="UG-28",
            standard_route_id=route_id,
            applicable=has_external_pressure,
            justification=(
                "Applicable because external pressure service is declared."
                if has_external_pressure
                else "Not applicable because external pressure service is not declared and internal pressure basis is assumed."
            ),
            evidence_fields=["external_pressure"] if has_external_pressure else ["design_pressure"],
        ),
        ClauseApplicabilityRecord(
            clause_id="UG-32",
            standard_route_id=route_id,
            applicable=True,
            justification="Applicable because head thickness under internal pressure must be verified.",
            evidence_fields=["design_pressure", "code_standard"],
        ),
        ClauseApplicabilityRecord(
            clause_id="UG-37",
            standard_route_id=route_id,
            applicable=True,
            justification=(
                "Applicable because nozzle openings require reinforcement-area replacement checks against parent components."
            ),
            evidence_fields=["design_pressure", "code_standard"],
        ),
        ClauseApplicabilityRecord(
            clause_id="UG-45",
            standard_route_id=route_id,
            applicable=True,
            justification="Applicable because nozzle neck minimum thickness must be verified.",
            evidence_fields=["design_pressure", "code_standard"],
        ),
        ClauseApplicabilityRecord(
            clause_id="UCS-66",
            standard_route_id=route_id,
            applicable=temperature < -29.0,
            justification=(
                "Applicable because low-temperature service triggers impact-test considerations."
                if temperature < -29.0
                else "Not applicable because design temperature is above low-temperature impact-test threshold."
            ),
            evidence_fields=["design_temperature"],
        ),
    ]

    if pressure <= 0.0:
        raise ValueError("Invalid design_pressure: expected positive normalized pressure value.")

    return records


def _build_ped_clause_records(
    requirement_set: RequirementSet,
    *,
    route_id: str,
) -> list[ClauseApplicabilityRecord]:
    pressure = float(requirement_set.requirements["design_pressure"].value)
    fluid = str(requirement_set.requirements["fluid"].value).strip().lower()
    has_corrosion_allowance = "corrosion_allowance" in requirement_set.requirements

    if pressure <= 0.0:
        raise ValueError("Invalid design_pressure: expected positive normalized pressure value.")

    return [
        ClauseApplicabilityRecord(
            clause_id="PED-Article-4",
            standard_route_id=route_id,
            applicable=True,
            justification="Applicable because pressure equipment categorization requires Article 4 scope checks.",
            evidence_fields=["design_pressure", "capacity", "fluid", "code_standard"],
        ),
        ClauseApplicabilityRecord(
            clause_id="EN13445-3-6.2",
            standard_route_id=route_id,
            applicable=True,
            justification="Applicable because shell thickness checks are required for unfired pressure vessels.",
            evidence_fields=["design_pressure", "design_temperature", "code_standard"],
        ),
        ClauseApplicabilityRecord(
            clause_id="EN13445-3-6.6",
            standard_route_id=route_id,
            applicable=has_corrosion_allowance,
            justification=(
                "Applicable because corrosion allowance is explicitly provided."
                if has_corrosion_allowance
                else "Not applicable because no corrosion allowance was specified for this route."
            ),
            evidence_fields=["corrosion_allowance"] if has_corrosion_allowance else ["requirements"],
        ),
        ClauseApplicabilityRecord(
            clause_id="PED-Annex-I-2.2.3",
            standard_route_id=route_id,
            applicable=("steam" in fluid or "water" in fluid),
            justification=(
                "Applicable because stated fluid is a Group 2 service candidate and requires fluid-group traceability."
                if "steam" in fluid or "water" in fluid
                else "Not applicable because provided fluid requires alternate PED fluid-group categorization path."
            ),
            evidence_fields=["fluid", "code_standard"],
        ),
    ]


def _sha256_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
