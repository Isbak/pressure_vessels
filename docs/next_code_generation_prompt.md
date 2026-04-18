# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **current next roadmap item: BL-018**.

```text
You are implementing backlog item **BL-018: Implement platform runtime stack foundations** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved from YAML on 2026-04-18):
- `BL-018` status is `todo`.
- `BL-018` dependencies:
  - `BL-012`: `done`
- This makes `BL-018` the first `todo`/`in_progress` item whose `depends_on` set is fully `done`.

Restate before coding:
- Item ID/title: BL-018 — Implement platform runtime stack foundations
- depends_on: [BL-012]
- acceptance criteria:
  1) Frontend and backend service skeletons are created in-repo with documented ownership boundaries.
  2) Data, retrieval, observability, auth, secrets, and runtime platform choices are mapped to deployable infrastructure modules.
  3) CI includes environment checks proving declared stack components are either deployed or explicitly marked planned.
- deliverables:
  1) Stack foundation implementation plan and bootstrap modules
  2) Environment provisioning manifests
  3) Updated operations runbook

Repository constraints:
- Keep changes minimal and focused.
- Follow existing style and module patterns in `src/pressure_vessels/`.
- Add/extend tests in `tests/` for any new behavior.
- Prefer deterministic logic (no randomness/time-dependent values unless explicitly controlled).

Likely relevant files:
- `docs/tech-stack.md`
- `scripts/check_tech_stack.py`
- `tests/` (stack/governance verification coverage)
- `docs/runbooks/` (runtime operations notes)

Task:
1) Implement BL-018 behavior using existing repository patterns.
2) Satisfy each BL-018 acceptance criterion explicitly.
3) Deliver each BL-018 deliverable with minimal, auditable changes.
4) Add/extend tests under `tests/` for new behavior.
5) Update related architecture/interface docs under `docs/`.
6) Update `docs/development_backlog.yaml` status for BL-018 when complete.
7) Update `docs/next_code_generation_prompt.md` so it points at the subsequent backlog item.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
