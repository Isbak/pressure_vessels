from __future__ import annotations

from datetime import datetime, timezone
import json
import threading

from pressure_vessels.standards_ingestion_pipeline import (
    RegressionExample,
    StandardSource,
    StandardsPackageCollisionError,
    run_standards_ingestion,
    write_standards_package,
)

FIXED_NOW = datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc)


def _sample_source() -> StandardSource:
    return StandardSource(
        source_id="ASME_BPVC_VIII_DIV1_2025_MAIN",
        title="ASME BPVC Section VIII Division 1 (sample)",
        publisher="ASME",
        edition="2025",
        revision="2025.2",
        content_text=(
            "UG-27: Cylindrical shell thickness for internal pressure; equation = "
            "t = (P*R)/(S*E-0.6*P); See UG-16.\n"
            "UG-16: Minimum thickness requirements for pressure parts.\n"
            "UG-32: Head thickness under internal pressure; equation = "
            "t = (0.885*P*D)/(2*S*E-0.2*P); See UG-27.\n"
        ),
    )


def _regression_examples() -> list[RegressionExample]:
    return [
        RegressionExample(
            example_id="REG-001",
            required_clause_ids=["UG-16", "UG-27", "UG-32"],
            required_link_pairs=[("UG-27", "UG-16"), ("UG-32", "UG-27")],
        )
    ]


def test_write_standards_package_concurrent_collision_is_deterministic(tmp_path, monkeypatch):
    package = run_standards_ingestion(
        source_documents=[_sample_source()],
        standard_key="ASME_VIII_1",
        standard_version="2025.2",
        release_label="r5",
        regression_examples=_regression_examples(),
        now_utc=FIXED_NOW,
    )

    barrier = threading.Barrier(2)
    import pressure_vessels.standards_ingestion_pipeline as sip

    real_open = sip.os.open

    def _gated_open(path, flags, mode=0o777):
        if str(path).endswith(".lock"):
            barrier.wait(timeout=2)
        return real_open(path, flags, mode)

    monkeypatch.setattr(sip.os, "open", _gated_open)

    results: list[tuple[str, object]] = []
    results_lock = threading.Lock()

    def _write_once() -> None:
        try:
            result = ("success", write_standards_package(package, tmp_path))
        except Exception as exc:  # noqa: BLE001 - assert on exact type below.
            result = ("error", exc)
        with results_lock:
            results.append(result)

    t1 = threading.Thread(target=_write_once)
    t2 = threading.Thread(target=_write_once)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    successes = [value for kind, value in results if kind == "success"]
    errors = [value for kind, value in results if kind == "error"]

    assert len(successes) == 1
    assert len(errors) == 1
    assert isinstance(errors[0], StandardsPackageCollisionError)

    artifact_path = tmp_path / f"{package.package_id}.json"
    assert artifact_path.exists()
    assert successes[0] == artifact_path
    assert artifact_path.read_text(encoding="utf-8") == json.dumps(
        package.to_json_dict(),
        indent=2,
        sort_keys=True,
    ) + "\n"

    assert list(tmp_path.glob(f"{artifact_path.name}.tmp.*")) == []
    assert not (tmp_path / f"{artifact_path.name}.lock").exists()
