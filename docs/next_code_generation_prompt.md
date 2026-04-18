# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **current next roadmap item: BL-013**.

```text
You are implementing backlog item **BL-013: Implement materials and corrosion module integration** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-18):
- `BL-013` status is `todo`.
- `BL-013` dependencies are `BL-003` and `BL-004`, and both are `done`.
- Therefore `BL-013` is the next eligible item.

Restate before coding:
- Item ID/title: BL-013 — Implement materials and corrosion module integration
- depends_on: [BL-003, BL-004]
- acceptance criteria:
  1) Placeholder allowable-stress and joint-efficiency defaults are replaced by materials-module outputs.
  2) Material allowables are versioned and traceable to standards package references.
  3) Corrosion allowance policy is explicit and persisted into calculation and compliance artifacts.
- deliverables:
  1) Material compatibility/allowables provider
  2) Calculation pipeline integration without placeholder stress defaults
  3) Artifact trace fields for material basis

Repository constraints:
- Keep changes minimal and focused.
- Follow existing style and module patterns in `src/pressure_vessels/`.
- Add/extend tests in `tests/` for any new behavior.
- Prefer deterministic logic (no randomness/time-dependent values unless explicitly controlled).

Likely relevant files:
- `src/pressure_vessels/calculation_pipeline.py`
- `src/pressure_vessels/compliance_pipeline.py`
- `docs/interfaces/calculation_pipeline_contract.md`
- `docs/interfaces/compliance_pipeline_contract.md`
- `tests/test_calculation_pipeline.py`
- `tests/test_compliance_pipeline.py`

Task:
1) Implement BL-013 behavior using existing repository patterns.
2) Satisfy each BL-013 acceptance criterion explicitly.
3) Deliver each BL-013 deliverable with minimal, auditable changes.
4) Add/extend tests under `tests/` for new behavior.
5) Update related architecture/interface docs under `docs/`.
6) Update `docs/development_backlog.yaml` status for BL-013 when complete.
7) Update `docs/next_code_generation_prompt.md` so it points at the subsequent backlog item.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
