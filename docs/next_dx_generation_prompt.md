# Next DX Generation Prompt (Roadmap-Aligned)

There is currently **no remaining eligible DX roadmap item** in `docs/platform_roadmap.yaml` as of 2026-04-19 because DX-001 through DX-010 are marked `done`.

```text
No eligible DX item remains in docs/platform_roadmap.yaml.

Required next action:
1) Add the next roadmap item (for example DX-011) to docs/platform_roadmap.yaml with
   status: todo and explicit depends_on references.
2) Regenerate this prompt to target that new first eligible todo item.

Execution rules:
1) Implement only the single next eligible roadmap item with minimal, focused changes.
2) Follow AGENT_GOVERNANCE.md workflow and controls.
3) Do not batch multiple future DX roadmap items in one change.
4) Preserve developer experience principles (fast onboarding, reproducibility,
   governance-by-default, and clear ownership boundaries).
```

## Upcoming queue

After a new DX item is added with `status: todo`, select the first entry whose
dependencies are all `done`.
