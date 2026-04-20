#!/usr/bin/env python3
"""Generate machine-readable governance checklist evidence for PR consumption."""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from pressure_vessels.governance_checks import generate_governance_checklist_evidence_main  # noqa: E402

main = generate_governance_checklist_evidence_main


if __name__ == "__main__":
    raise SystemExit(main())
