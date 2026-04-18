# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **current next roadmap item: BL-015**.

```text
You are implementing backlog item **BL-015: Replace dossier placeholders with signed change-impact and PDF rendering** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-18):
- `BL-015` status is `todo`.
- `BL-015` dependencies are `BL-007` and `BL-008`, and both are `done`.
- Therefore `BL-015` is the next eligible item.

Restate before coding:
- Item ID/title: BL-015 — Replace dossier placeholders with signed change-impact and PDF rendering
- depends_on: [BL-007, BL-008]
- acceptance criteria:
  1) BL-007 export embeds signed BL-008 impact report instead of placeholder payloads.
  2) Canonical dossier PDF is rendered from deterministic payload templates.
  3) Inspector/regulator workflow artifacts include sign-off state transitions and evidence refs.
- deliverables:
  1) Dossier export integration with BL-008 artifacts
  2) Deterministic PDF renderer path
  3) Updated dossier export contract and runbook

Repository constraints:
- Keep changes minimal and focused.
- Follow existing style and module patterns in `src/pressure_vessels/`.
- Add/extend tests in `tests/` for any new behavior.
- Prefer deterministic logic (no randomness/time-dependent values unless explicitly controlled).

Likely relevant files:
- `src/pressure_vessels/dossier_export_pipeline.py`
- `src/pressure_vessels/change_impact_pipeline.py`
- `docs/interfaces/dossier_export_pipeline_contract.md`
- `tests/test_dossier_export_pipeline.py`
- `tests/test_change_impact_pipeline.py`

Task:
1) Implement BL-015 behavior using existing repository patterns.
2) Satisfy each BL-015 acceptance criterion explicitly.
3) Deliver each BL-015 deliverable with minimal, auditable changes.
4) Add/extend tests under `tests/` for new behavior.
5) Update related architecture/interface docs under `docs/`.
6) Update `docs/development_backlog.yaml` status for BL-015 when complete.
7) Update `docs/next_code_generation_prompt.md` so it points at the subsequent backlog item.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
