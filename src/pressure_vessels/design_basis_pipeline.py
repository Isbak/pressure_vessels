"""Deterministic design basis + applicability matrix generation for BL-002."""

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

_PRIMARY_STANDARD_LOOKUP: dict[str, tuple[str, str]] = {
    "ASME SECTION VIII DIV 1": ("ASME Section VIII Division 1", "ASME_BPVC_2023"),
    "ASME VIII-1": ("ASME Section VIII Division 1", "ASME_BPVC_2023"),
}


@dataclass(frozen=True)
class ClauseApplicabilityRecord:
    clause_id: str
    applicable: bool
    justification: str
    evidence_fields: list[str]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "clause_id": self.clause_id,
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
    records: list[ClauseApplicabilityRecord]
    deterministic_hash: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at_utc": self.generated_at_utc,
            "source_requirement_set_hash": self.source_requirement_set_hash,
            "primary_standard": self.primary_standard,
            "primary_standard_version": self.primary_standard_version,
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
    secondary_standards: list[str]
    assumptions: list[str]
    deterministic_signature: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at_utc": self.generated_at_utc,
            "source_requirement_set_hash": self.source_requirement_set_hash,
            "primary_standard": self.primary_standard,
            "primary_standard_version": self.primary_standard_version,
            "secondary_standards": self.secondary_standards,
            "assumptions": self.assumptions,
            "deterministic_signature": self.deterministic_signature,
        }


def build_design_basis(
    requirement_set: RequirementSet,
    now_utc: datetime | None = None,
) -> tuple[DesignBasis, ApplicabilityMatrix]:
    """Build deterministic BL-002 artifacts from a valid RequirementSet.v1."""
    _validate_handoff_gate(requirement_set)

    generated_at = (now_utc or datetime.now(tz=timezone.utc)).replace(microsecond=0).isoformat()

    raw_standard = str(requirement_set.requirements["code_standard"].value)
    primary_standard, primary_version = _resolve_primary_standard(raw_standard)
    secondary_standards: list[str] = []

    matrix_records = _build_mvp_clause_records(requirement_set)
    matrix_canonical = {
        "schema_version": APPLICABILITY_MATRIX_VERSION,
        "generated_at_utc": generated_at,
        "source_requirement_set_hash": requirement_set.deterministic_hash,
        "primary_standard": primary_standard,
        "primary_standard_version": primary_version,
        "records": [asdict(r) for r in matrix_records],
    }
    matrix_hash = _sha256_payload(matrix_canonical)

    matrix = ApplicabilityMatrix(
        schema_version=APPLICABILITY_MATRIX_VERSION,
        generated_at_utc=generated_at,
        source_requirement_set_hash=requirement_set.deterministic_hash,
        primary_standard=primary_standard,
        primary_standard_version=primary_version,
        records=matrix_records,
        deterministic_hash=matrix_hash,
    )

    assumptions = [
        "MVP assumes internal pressure service unless external pressure input is provided.",
        "No secondary standards are auto-selected in BL-002 MVP.",
    ]

    design_basis_unsigned = {
        "schema_version": DESIGN_BASIS_VERSION,
        "generated_at_utc": generated_at,
        "source_requirement_set_hash": requirement_set.deterministic_hash,
        "primary_standard": primary_standard,
        "primary_standard_version": primary_version,
        "secondary_standards": secondary_standards,
        "assumptions": assumptions,
    }
    signature = _sha256_payload(design_basis_unsigned)

    design_basis = DesignBasis(
        schema_version=DESIGN_BASIS_VERSION,
        generated_at_utc=generated_at,
        source_requirement_set_hash=requirement_set.deterministic_hash,
        primary_standard=primary_standard,
        primary_standard_version=primary_version,
        secondary_standards=secondary_standards,
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


def _resolve_primary_standard(code_standard_value: str) -> tuple[str, str]:
    canonical = " ".join(code_standard_value.strip().upper().split())
    resolved = _PRIMARY_STANDARD_LOOKUP.get(canonical)
    if not resolved:
        raise ValueError(
            "Unsupported code_standard for BL-002 MVP; expected ASME Section VIII Div 1 variant."
        )
    return resolved


def _build_mvp_clause_records(requirement_set: RequirementSet) -> list[ClauseApplicabilityRecord]:
    pressure = float(requirement_set.requirements["design_pressure"].value)
    temperature = float(requirement_set.requirements["design_temperature"].value)
    has_corrosion_allowance = "corrosion_allowance" in requirement_set.requirements

    records = [
        ClauseApplicabilityRecord(
            clause_id="UG-16",
            applicable=True,
            justification="Applicable because design pressure is defined for pressure boundary sizing.",
            evidence_fields=["design_pressure", "code_standard"],
        ),
        ClauseApplicabilityRecord(
            clause_id="UG-20",
            applicable=True,
            justification="Applicable because design temperature is defined for material selection limits.",
            evidence_fields=["design_temperature", "code_standard"],
        ),
        ClauseApplicabilityRecord(
            clause_id="UG-25",
            applicable=has_corrosion_allowance,
            justification=(
                "Applicable because corrosion allowance input is provided."
                if has_corrosion_allowance
                else "Not applicable in MVP because corrosion allowance input is absent."
            ),
            evidence_fields=["corrosion_allowance"] if has_corrosion_allowance else ["requirements"],
        ),
        ClauseApplicabilityRecord(
            clause_id="UG-28",
            applicable=False,
            justification=(
                "Not applicable in MVP because external pressure service is not declared "
                "and internal pressure basis is assumed."
            ),
            evidence_fields=["design_pressure"],
        ),
        ClauseApplicabilityRecord(
            clause_id="UCS-66",
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


def _sha256_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
