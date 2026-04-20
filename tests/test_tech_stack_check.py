from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/check_tech_stack.py"


def test_tech_stack_check_passes_for_repository_state() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Tech stack consistency check passed" in result.stdout


def test_tech_stack_check_fails_when_deployed_module_path_missing(tmp_path: Path) -> None:
    (tmp_path / "scripts").mkdir(parents=True)
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "infra/platform").mkdir(parents=True)

    script_text = SCRIPT_PATH.read_text(encoding="utf-8")
    (tmp_path / "scripts/check_tech_stack.py").write_text(script_text, encoding="utf-8")

    (tmp_path / "docs/tech-stack.md").write_text(
        "\n".join(
            [
                "# Tech Stack",
                "## Current",
                "### Runtime stack components (deployed)",
                "- Component: `frontend-nextjs`",
                "### Runtime stack components (scaffolded)",
                "## Planned",
                "### Runtime stack components (planned)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (tmp_path / "docs/platform_runtime_stack_registry.yaml").write_text(
        "\n".join(
            [
                "version: 1",
                "components:",
                "  - key: frontend-nextjs",
                "    status: deployed",
                "    module_path: services/frontend",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (tmp_path / "infra/platform/environment.bootstrap.yaml").write_text(
        "\n".join(
            [
                "version: v1",
                "kind: PlatformEnvironmentBootstrap",
                "spec:",
                "  environments:",
                "    - name: dev",
                "      modules:",
                "        - frontend-nextjs",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(tmp_path / "scripts/check_tech_stack.py")],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "module_path does not exist" in result.stdout


def test_tech_stack_check_fails_when_iac_module_exists_but_status_is_deployed_without_hcl(
    tmp_path: Path,
) -> None:
    (tmp_path / "scripts").mkdir(parents=True)
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "infra/platform/iac").mkdir(parents=True)

    script_text = SCRIPT_PATH.read_text(encoding="utf-8")
    (tmp_path / "scripts/check_tech_stack.py").write_text(script_text, encoding="utf-8")

    (tmp_path / "docs/tech-stack.md").write_text(
        "\n".join(
            [
                "# Tech Stack",
                "## Current",
                "### Runtime stack components (deployed)",
                "### Runtime stack components (scaffolded)",
                "- Component: `iac-opentofu-or-terraform`",
                "## Planned",
                "### Runtime stack components (planned)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (tmp_path / "docs/platform_runtime_stack_registry.yaml").write_text(
        "\n".join(
            [
                "version: 1",
                "components:",
                "  - key: iac-opentofu-or-terraform",
                "    status: deployed",
                "    module_path: infra/platform/iac",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (tmp_path / "infra/platform/environment.bootstrap.yaml").write_text(
        "\n".join(
            [
                "version: v1",
                "kind: PlatformEnvironmentBootstrap",
                "spec:",
                "  environments:",
                "    - name: staging",
                "      modules:",
                "        - iac-opentofu-or-terraform",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(tmp_path / "scripts/check_tech_stack.py")],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "'iac-opentofu-or-terraform' status must be 'scaffolded'" in result.stdout
