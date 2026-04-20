from __future__ import annotations

from pressure_vessels import dev_cli


def test_entry_points_delegate_to_expected_scripts(monkeypatch) -> None:
    called: list[tuple[str, list[str] | None]] = []

    def fake_runner(script_name: str, argv: list[str] | None) -> int:
        called.append((script_name, argv))
        return 0

    monkeypatch.setattr(dev_cli, "_run_repo_script", fake_runner)

    assert dev_cli.suggest_risk_label_main(["a", "b", "c"]) == 0
    assert dev_cli.check_tech_stack_main(["--help"]) == 0
    assert dev_cli.check_readme_anchors_main(["--help"]) == 0

    assert called == [
        ("suggest_risk_label.py", ["a", "b", "c"]),
        ("check_tech_stack.py", ["--help"]),
        ("check_readme_anchors.py", ["--help"]),
    ]


def test_readme_entry_point_accepts_backlog_positional_for_ci_compat(monkeypatch) -> None:
    called: list[tuple[str, list[str] | None]] = []

    def fake_runner(script_name: str, argv: list[str] | None) -> int:
        called.append((script_name, argv))
        return 0

    monkeypatch.setattr(dev_cli, "_run_repo_script", fake_runner)

    assert dev_cli.check_readme_anchors_main(["docs/development_backlog.yaml"]) == 0
    assert called == [
        ("check_readme_anchors.py", ["--backlog", "docs/development_backlog.yaml"]),
    ]
