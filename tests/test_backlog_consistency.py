from __future__ import annotations

from pathlib import Path


BACKLOG_PATH = Path("docs/development_backlog.yaml")
VALID_STATUSES = {"todo", "in_progress", "done", "blocked"}


def _parse_backlog_items() -> list[dict[str, object]]:
    lines = BACKLOG_PATH.read_text(encoding="utf-8").splitlines()

    items: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    in_depends_on = False

    for line in lines:
        if line.startswith("- id: "):
            if current is not None:
                items.append(current)
            current = {"id": line.split(": ", 1)[1].strip(), "depends_on": []}
            in_depends_on = False
            continue

        if current is None:
            continue

        if line.startswith("  status: "):
            current["status"] = line.split(": ", 1)[1].strip()
            in_depends_on = False
            continue

        if line.startswith("  depends_on:"):
            in_depends_on = True
            continue

        if in_depends_on and line.startswith("  - "):
            current["depends_on"].append(line.strip()[2:])
            continue

        if in_depends_on and not line.startswith("  - "):
            in_depends_on = False

    if current is not None:
        items.append(current)

    return items


def test_todo_and_in_progress_items_only_depend_on_done_items() -> None:
    items = _parse_backlog_items()
    item_by_id = {str(item["id"]): item for item in items}

    for item in items:
        status = str(item.get("status", ""))
        item_id = str(item["id"])
        assert status in VALID_STATUSES, f"{item_id} has invalid status: {status!r}"

        depends_on = [str(dep_id) for dep_id in item.get("depends_on", [])]
        for dep_id in depends_on:
            assert dep_id in item_by_id, f"{item_id} depends on missing item {dep_id}"

        if status in {"todo", "in_progress"}:
            not_done = [
                dep_id
                for dep_id in depends_on
                if str(item_by_id[dep_id].get("status", "")) != "done"
            ]
            assert not not_done, (
                f"{item_id} is {status} but has dependencies not done: {not_done}. "
                "Mark the item blocked or complete dependencies first."
            )
