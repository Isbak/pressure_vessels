from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess

BASELINE_FILES: tuple[str, ...] = (
    "AGENT_GOVERNANCE.md",
    "docs/governance/ci_governance_policy.v1.json",
    "docs/governance/policy_exceptions_schema.v1.json",
    "docs/governance/risk_label_heuristics.v1.json",
    ".github/workflows/reusable-governance-core.yml",
    "scripts/check_ci_governance.py",
)

METADATA_PATH = ".governance/baseline_source.v1.json"
BASELINE_ID = "pressure-vessels-governance-baseline"
BASELINE_VERSION = "1.0.0"
SOURCE_REPOSITORY = "pressure-vessels/pressure_vessels"


def scaffold_governance_baseline_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scaffold this repository's AGENT_GOVERNANCE baseline into a target project"
        )
    )
    parser.add_argument(
        "--target",
        default=".",
        help="Target repository root where baseline files should be written (default: current directory).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files in the target project.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[2]
    target_root = Path(args.target).resolve()

    metadata = _build_metadata(repo_root)
    copied_files: list[str] = []
    for relative_path in BASELINE_FILES:
        source = repo_root / relative_path
        destination = target_root / relative_path

        if not source.exists():
            raise FileNotFoundError(f"Baseline source file missing: {source}")

        if destination.exists() and not args.force:
            raise FileExistsError(
                f"Refusing to overwrite existing file without --force: {destination}"
            )

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied_files.append(relative_path)

    metadata["files"] = [_file_fingerprint(repo_root, path) for path in copied_files]
    metadata_output = target_root / METADATA_PATH
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    print(
        f"Scaffolded {len(copied_files)} baseline files to {target_root} and wrote {METADATA_PATH}."
    )
    return 0


def _build_metadata(repo_root: Path) -> dict[str, object]:
    return {
        "baseline_id": BASELINE_ID,
        "baseline_version": BASELINE_VERSION,
        "source_repository": SOURCE_REPOSITORY,
        "source_commit": _git_commit(repo_root),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def _git_commit(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _file_fingerprint(repo_root: Path, relative_path: str) -> dict[str, str]:
    file_path = repo_root / relative_path
    digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
    return {
        "path": relative_path,
        "sha256": digest,
    }
