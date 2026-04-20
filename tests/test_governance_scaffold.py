from __future__ import annotations

import json
from pathlib import Path

from pressure_vessels.governance_scaffold import (
    BASELINE_FILES,
    METADATA_PATH,
    scaffold_governance_baseline_main,
)


def test_scaffold_governance_baseline_writes_files_and_metadata(tmp_path: Path) -> None:
    exit_code = scaffold_governance_baseline_main(["--target", str(tmp_path)])
    assert exit_code == 0

    for relative_path in BASELINE_FILES:
        assert (tmp_path / relative_path).exists()

    metadata = json.loads((tmp_path / METADATA_PATH).read_text(encoding="utf-8"))
    assert metadata["baseline_id"] == "pressure-vessels-governance-baseline"
    assert metadata["baseline_version"] == "1.0.0"
    assert metadata["source_repository"] == "pressure-vessels/pressure_vessels"
    assert len(metadata["files"]) == len(BASELINE_FILES)
