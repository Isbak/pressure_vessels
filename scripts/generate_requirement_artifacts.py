"""Generate deterministic BL-001 sample artifacts."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from pressure_vessels.requirements_pipeline import parse_prompt_to_requirement_set


def main() -> None:
    outdir = Path("artifacts/bl-001")
    outdir.mkdir(parents=True, exist_ok=True)

    success_prompt = (
        "Design a horizontal pressure vessel for propane storage, "
        "18 bar design pressure, 65°C design temperature, 30 m3 capacity, "
        "ASME Section VIII Div 1, corrosion allowance 3 mm."
    )
    missing_fields_prompt = "Need a vessel for water storage, 20 m3 capacity."
    fixed_time = datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc)

    requirement_set = parse_prompt_to_requirement_set(success_prompt, now_utc=fixed_time)
    gap_set = parse_prompt_to_requirement_set(missing_fields_prompt, now_utc=fixed_time)

    (outdir / "RequirementSet.v1.sample.json").write_text(
        json.dumps(requirement_set.to_json_dict(), indent=2),
        encoding="utf-8",
    )
    (outdir / "unresolved_gaps.sample.json").write_text(
        json.dumps([g.__dict__ for g in gap_set.unresolved_gaps], indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
