# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **current next roadmap item: BL-017**.

```text
You are implementing backlog item **BL-017: Build QA benchmark and cross-verification harness** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved from YAML on 2026-04-18):
- `BL-017` status is `todo`.
- `BL-017` dependencies:
  - `BL-013`: `done`
  - `BL-014`: `done`
  - `BL-016`: `done`
- This makes `BL-017` the first `todo`/`in_progress` item whose `depends_on` set is fully `done`.

Restate before coding:
- Item ID/title: BL-017 — Build QA benchmark and cross-verification harness
- depends_on: [BL-013, BL-014, BL-016]
- acceptance criteria:
  1) Golden benchmark cases are versioned and runnable in CI.
  2) Cross-verification against reference calculations produces deterministic pass/fail reports.
  3) Boundary/stress tests are captured with reproducible fixtures and retained artifacts.
- deliverables:
  1) QA benchmark dataset manifest
  2) Cross-verification test harness
  3) CI quality-gate report artifact

Repository constraints:
- Keep changes minimal and focused.
- Follow existing style and module patterns in `src/pressure_vessels/`.
- Add/extend tests in `tests/` for any new behavior.
- Prefer deterministic logic (no randomness/time-dependent values unless explicitly controlled).

Likely relevant files:
- `tests/golden_examples/` (dataset manifest and fixture updates)
- `tests/` (cross-verification harness coverage)
- `src/pressure_vessels/` (support module for QA benchmark reporting if needed)
- `docs/interfaces/` and `docs/runbooks/` (quality-gate contract + operating notes)

Task:
1) Implement BL-017 behavior using existing repository patterns.
2) Satisfy each BL-017 acceptance criterion explicitly.
3) Deliver each BL-017 deliverable with minimal, auditable changes.
4) Add/extend tests under `tests/` for new behavior.
5) Update related architecture/interface docs under `docs/`.
6) Update `docs/development_backlog.yaml` status for BL-017 when complete.
7) Update `docs/next_code_generation_prompt.md` so it points at the subsequent backlog item.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
