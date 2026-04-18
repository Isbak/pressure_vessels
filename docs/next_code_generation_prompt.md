# Next Code Generation Prompt (Roadmap-Aligned)

All backlog items in `docs/development_backlog.yaml` are currently marked `done` (through **BL-020** as of 2026-04-18).

Use this prompt for the **next newly-prioritized backlog item** once added to the backlog file.

```text
You are implementing backlog item **<NEXT-ID>: <NEXT-TITLE>** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved from YAML on 2026-04-18):
- `<NEXT-ID>` status is `todo` or `in_progress`.
- `<NEXT-ID>` dependencies are fully `done`.
- This makes `<NEXT-ID>` the first actionable item in backlog order.

Restate before coding:
- Item ID/title: <NEXT-ID> — <NEXT-TITLE>
- depends_on: <LIST>
- source: <SOURCE FIELD FROM YAML>

Repository constraints:
- Keep changes minimal and focused.
- Follow existing style and module patterns in `src/pressure_vessels/`.
- Add/extend tests in `tests/` for any new behavior.
- Prefer deterministic logic (no randomness/time-dependent values unless explicitly controlled).

Likely relevant files:
- Derive from the selected backlog item references and acceptance criteria.

Task:
1) Implement `<NEXT-ID>` behavior using existing repository patterns.
2) Update or add automated checks in CI when required by the item.
3) Add/extend tests under `tests/` for new behavior.
4) Update related docs under `docs/` if contracts change.
5) Update `docs/development_backlog.yaml` status for `<NEXT-ID>` when complete.
6) Update `docs/next_code_generation_prompt.md` so it points at the subsequent backlog item.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
