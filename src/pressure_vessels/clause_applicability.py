"""Authoritative clause applicability status enum shared across pipelines."""

from __future__ import annotations

from enum import Enum


class ClauseApplicabilityStatus(str, Enum):
    """Allowed clause applicability statuses for machine-readable artifacts."""

    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"
    NOT_EVALUATED = "not_evaluated"

    @classmethod
    def parse(cls, value: "ClauseApplicabilityStatus | str") -> "ClauseApplicabilityStatus":
        """Parse and validate a status value."""
        if isinstance(value, cls):
            return value
        try:
            return cls(value)
        except ValueError as exc:
            allowed = ", ".join(member.value for member in cls)
            raise ValueError(
                f"Invalid ClauseApplicabilityStatus '{value}'. Allowed values: {allowed}."
            ) from exc
