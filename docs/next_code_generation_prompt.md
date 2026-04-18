# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to generate the **next implementation step** from the backlog:

```text
You are implementing the next roadmap item for the `pressure_vessels` repository.

Context:

- Roadmap source: `docs/development_backlog.yaml`
- Determine completed items from backlog entries where `status: done`.
- Determine the next item to implement as the first backlog entry with `status: todo` whose `depends_on` items are all done.
- If no eligible `todo` item exists, stop and report that backlog implementation is complete.

For the selected item, restate:

- Item ID and title
- `depends_on`
- acceptance criteria
- deliverables

Repository constraints:

- Keep changes minimal and focused.
- Follow existing style and module patterns in `src/pressure_vessels/`.
- Add/extend tests in `tests/` for any new behavior.
- Prefer deterministic logic (no randomness/time-dependent values unless explicitly controlled).

Existing relevant files:

- `scripts/`
- `docs/`
- `src/pressure_vessels/`
- `tests/`
- `README.md`

Task:

1) Implement the selected backlog item behavior using existing repository patterns.
2) Satisfy each acceptance criterion explicitly.
3) Deliver each listed deliverable with minimal, auditable changes.
4) Add/extend tests under `tests/` for new behavior.
5) Update related architecture/interface docs under `docs/`.
6) Update `docs/development_backlog.yaml` status for the implemented item.
7) Update `docs/next_code_generation_prompt.md` so it points at the subsequent backlog item.

Output format:

- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
