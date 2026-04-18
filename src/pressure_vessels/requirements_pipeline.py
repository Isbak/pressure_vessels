"""Deterministic prompt parsing and normalization for BL-001."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any

REQUIREMENT_SET_VERSION = "RequirementSet.v1"
CANONICAL_UNITS: dict[str, str] = {
    "design_pressure": "Pa",
    "design_temperature": "C",
    "capacity": "m3",
    "corrosion_allowance": "mm",
}
MANDATORY_FIELDS = (
    "fluid",
    "design_pressure",
    "design_temperature",
    "capacity",
    "code_standard",
)

PRESSURE_FACTORS = {
    "pa": 1.0,
    "kpa": 1_000.0,
    "mpa": 1_000_000.0,
    "bar": 100_000.0,
    "psi": 6_894.757293168,
}

TEMPERATURE_CONVERTERS = {
    "c": lambda v: v,
    "°c": lambda v: v,
    "f": lambda v: (v - 32.0) * (5.0 / 9.0),
    "°f": lambda v: (v - 32.0) * (5.0 / 9.0),
    "k": lambda v: v - 273.15,
}

VOLUME_FACTORS = {
    "m3": 1.0,
    "m^3": 1.0,
    "l": 0.001,
    "liter": 0.001,
    "liters": 0.001,
    "ft3": 0.028316846592,
    "ft^3": 0.028316846592,
}

LENGTH_FACTORS_TO_MM = {
    "mm": 1.0,
    "cm": 10.0,
    "m": 1000.0,
    "in": 25.4,
    "inch": 25.4,
    "inches": 25.4,
}


@dataclass(frozen=True)
class RequirementValue:
    value: Any
    unit: str | None
    source_text: str


@dataclass(frozen=True)
class Gap:
    field: str
    reason: str


@dataclass(frozen=True)
class RequirementSet:
    schema_version: str
    generated_at_utc: str
    input_prompt: str
    requirements: dict[str, RequirementValue]
    unresolved_gaps: list[Gap]
    downstream_blocked: bool
    deterministic_hash: str

    def to_json_dict(self) -> dict[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "generated_at_utc": self.generated_at_utc,
            "input_prompt": self.input_prompt,
            "requirements": {
                k: asdict(v) for k, v in sorted(self.requirements.items(), key=lambda i: i[0])
            },
            "unresolved_gaps": [asdict(g) for g in self.unresolved_gaps],
            "downstream_blocked": self.downstream_blocked,
            "deterministic_hash": self.deterministic_hash,
        }
        return payload


def parse_prompt_to_requirement_set(prompt: str, *, now_utc: datetime | None = None) -> RequirementSet:
    """Parse prompt into normalized requirements, producing unresolved gaps."""
    normalized_prompt = _normalize_text(prompt)
    extracted: dict[str, RequirementValue] = {}

    fluid = _extract_fluid(normalized_prompt)
    if fluid:
        extracted["fluid"] = fluid

    pressure = _extract_numeric(normalized_prompt, field_name="design_pressure")
    if pressure:
        extracted["design_pressure"] = pressure

    temperature = _extract_numeric(normalized_prompt, field_name="design_temperature")
    if temperature:
        extracted["design_temperature"] = temperature

    capacity = _extract_numeric(normalized_prompt, field_name="capacity")
    if capacity:
        extracted["capacity"] = capacity

    corrosion = _extract_numeric(normalized_prompt, field_name="corrosion_allowance")
    if corrosion:
        extracted["corrosion_allowance"] = corrosion

    code_standard = _extract_code_standard(normalized_prompt)
    if code_standard:
        extracted["code_standard"] = code_standard

    gaps = _detect_gaps(extracted)
    blocked = len(gaps) > 0

    generated_at = (now_utc or datetime.now(tz=timezone.utc)).replace(microsecond=0).isoformat()
    canonical_for_hash = {
        field: {"value": value.value, "unit": value.unit}
        for field, value in sorted(extracted.items(), key=lambda i: i[0])
    }
    canonical_string = json.dumps(canonical_for_hash, sort_keys=True, separators=(",", ":"))
    deterministic_hash = hashlib.sha256(canonical_string.encode("utf-8")).hexdigest()

    return RequirementSet(
        schema_version=REQUIREMENT_SET_VERSION,
        generated_at_utc=generated_at,
        input_prompt=prompt,
        requirements=extracted,
        unresolved_gaps=gaps,
        downstream_blocked=blocked,
        deterministic_hash=deterministic_hash,
    )


def _normalize_text(prompt: str) -> str:
    return " ".join(prompt.strip().split()).lower()


def _extract_fluid(prompt: str) -> RequirementValue | None:
    patterns = [
        r"for\s+([a-z][a-z0-9\- ]+?)\s+storage",
        r"fluid\s*[:=]\s*([a-z][a-z0-9\- ]+?)(?:,|$)",
        r"contents?\s*[:=]\s*([a-z][a-z0-9\- ]+?)(?:,|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt)
        if match:
            name = match.group(1).strip()
            return RequirementValue(value=name, unit=None, source_text=match.group(0))
    return None


def _extract_numeric(prompt: str, *, field_name: str) -> RequirementValue | None:
    field_patterns = {
        "design_pressure": [
            r"(?:design\s+pressure|pressure)\s*[:=]?\s*(-?\d+(?:\.\d+)?)\s*([a-z°\^0-9/]+)",
            r"(-?\d+(?:\.\d+)?)\s*([a-z°\^0-9/]+)\s*(?:design\s+pressure|pressure)",
        ],
        "design_temperature": [
            r"(?:design\s+temperature|temperature)\s*[:=]?\s*(-?\d+(?:\.\d+)?)\s*(°?[cfk])",
            r"(-?\d+(?:\.\d+)?)\s*(°?[cfk])\s*(?:design\s+temperature|temperature)",
        ],
        "capacity": [
            r"(?:capacity|volume)\s*[:=]?\s*(-?\d+(?:\.\d+)?)\s*([a-z\^0-9]+)",
            r"(-?\d+(?:\.\d+)?)\s*([a-z\^0-9]+)\s*(?:capacity|volume)",
        ],
        "corrosion_allowance": [
            r"(?:corrosion\s+allowance|ca)\s*[:=]?\s*(-?\d+(?:\.\d+)?)\s*([a-z]+)",
            r"(-?\d+(?:\.\d+)?)\s*([a-z]+)\s*(?:corrosion\s+allowance|ca)",
        ],
    }

    match = None
    for pattern in field_patterns[field_name]:
        match = re.search(pattern, prompt)
        if match:
            break
    if not match:
        return None

    raw_value = float(match.group(1))
    raw_unit = match.group(2).strip()
    normalized = _normalize_unit_value(field_name, raw_value, raw_unit)
    if normalized is None:
        return None

    value, unit = normalized
    return RequirementValue(value=value, unit=unit, source_text=match.group(0))


def _extract_code_standard(prompt: str) -> RequirementValue | None:
    patterns = [
        r"(asme\s+section\s+viii\s*div(?:ision)?\s*1)",
        r"(asme\s+viii[-\s]*1)",
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt)
        if match:
            standard = re.sub(r"\s+", " ", match.group(1).strip()).upper()
            return RequirementValue(value=standard, unit=None, source_text=match.group(0))
    return None


def _normalize_unit_value(field_name: str, raw_value: float, raw_unit: str) -> tuple[float, str] | None:
    u = raw_unit.lower()
    if field_name == "design_pressure":
        factor = PRESSURE_FACTORS.get(u)
        if factor is None:
            return None
        return (round(raw_value * factor, 6), CANONICAL_UNITS[field_name])

    if field_name == "design_temperature":
        conv = TEMPERATURE_CONVERTERS.get(u)
        if conv is None:
            return None
        return (round(conv(raw_value), 6), CANONICAL_UNITS[field_name])

    if field_name == "capacity":
        factor = VOLUME_FACTORS.get(u)
        if factor is None:
            return None
        return (round(raw_value * factor, 6), CANONICAL_UNITS[field_name])

    if field_name == "corrosion_allowance":
        factor = LENGTH_FACTORS_TO_MM.get(u)
        if factor is None:
            return None
        return (round(raw_value * factor, 6), CANONICAL_UNITS[field_name])

    return None


def _detect_gaps(extracted: dict[str, RequirementValue]) -> list[Gap]:
    gaps: list[Gap] = []
    for field in MANDATORY_FIELDS:
        if field not in extracted:
            gaps.append(Gap(field=field, reason="Mandatory field missing or not parseable from prompt."))
    return gaps
