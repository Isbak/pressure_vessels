#!/usr/bin/env python3
"""Evaluate CI gate results against governance policy and persist audit report."""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from pressure_vessels.governance_checks import (  # noqa: E402
    PolicyException,
    _eligible_exceptions,
    _is_expired,
    _parse_iso8601,
    _scope_matches,
    _validate_control_drift,
    _validate_exceptions_document,
    check_ci_governance_main,
)

main = check_ci_governance_main


if __name__ == "__main__":
    raise SystemExit(main())
