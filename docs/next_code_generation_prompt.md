# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **current next roadmap item: BL-020**.

```text
You are implementing backlog item **BL-020: Add README-anchor consistency check trigger** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved from YAML on 2026-04-18):
- `BL-020` status is `todo`.
- `BL-020` dependencies: none.
- This makes `BL-020` the first `todo`/`in_progress` item whose `depends_on` set is fully `done`.

Restate before coding:
- Item ID/title: BL-020 — Add README-anchor consistency check trigger
- depends_on: []
- source: audit 2026-04-18, observation 2

Repository constraints:
- Keep changes minimal and focused.
- Follow existing style and module patterns in `src/pressure_vessels/`.
- Add/extend tests in `tests/` for any new behavior.
- Prefer deterministic logic (no randomness/time-dependent values unless explicitly controlled).

Likely relevant files:
- `.github/workflows/ci.yml`
- `README.md`
- `scripts/` (consistency-check helper if needed)
- `tests/` (workflow/anchor wiring tests)

Task:
1) Implement BL-020 behavior using existing repository patterns.
2) Add automated README-anchor consistency checks in CI.
3) Add/extend tests under `tests/` for new behavior.
4) Update related docs under `docs/` if contracts change.
5) Update `docs/development_backlog.yaml` status for BL-020 when complete.
6) Update `docs/next_code_generation_prompt.md` so it points at the subsequent backlog item.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
