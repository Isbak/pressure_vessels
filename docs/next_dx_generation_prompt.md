# Next DX Generation Prompt (Roadmap-Aligned)

DX-004 is the next eligible item in `docs/platform_roadmap.yaml` as of 2026-04-19.

```text
Implement DX-004 from docs/platform_roadmap.yaml.

Reference documents to use:
- docs/developer_experience_principles.md
- services/frontend/README.md#frontend-service-skeleton
- AGENT_GOVERNANCE.md

Eligibility rationale:
1) DX-001 is marked status: done.
2) DX-002 is marked status: done.
3) DX-003 is marked status: done.
4) DX-004 is the first item with status: todo.
5) DX-004 dependency is satisfied (depends_on: [DX-001]).

Execution rules:
1) Implement only this single roadmap item with minimal, focused changes.
2) Follow AGENT_GOVERNANCE.md workflow and controls.
3) Do not start DX-004+ work in the same change.
4) Preserve developer experience principles (fast onboarding, reproducibility,
   governance-by-default, and clear ownership boundaries).

DX-004 acceptance criteria:
- Frontend can collect prompt input and render backend response.
- Local dev server supports hot reload.

DX-004 deliverables:
- Frontend route(s) for prompt and result view
- Frontend run instructions

Required close-out actions in the same PR:
1) Update docs/platform_roadmap.yaml and set DX-004 status to done once
   acceptance criteria are met.
2) Regenerate/update docs/next_dx_generation_prompt.md so it points to the next
   eligible roadmap item (expected next: DX-005 after DX-004 is done).
```

## Upcoming queue

After DX-004 is completed, the next queued item is DX-005 (depends on DX-004),
then DX-006 (depends on DX-005).
