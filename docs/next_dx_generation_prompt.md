# Next DX Generation Prompt (Roadmap-Aligned)

DX-006 is the next eligible item in `docs/platform_roadmap.yaml` as of 2026-04-19.

```text
Implement DX-006 from docs/platform_roadmap.yaml.

Reference documents to use:
- docs/developer_experience_principles.md
- docs/tech-stack.md#current
- docs/runbooks/platform_runtime_stack_operations.md#service-ownership-boundaries
- AGENT_GOVERNANCE.md

Eligibility rationale:
1) DX-001 is marked status: done.
2) DX-002 is marked status: done.
3) DX-003 is marked status: done.
4) DX-004 is marked status: done.
5) DX-005 is marked status: done.
6) DX-006 is the first item with status: todo.
7) DX-006 dependency is satisfied (depends_on: [DX-005]).

Execution rules:
1) Implement only this single roadmap item with minimal, focused changes.
2) Follow AGENT_GOVERNANCE.md workflow and controls.
3) Do not start DX-006+ work in the same change.
4) Preserve developer experience principles (fast onboarding, reproducibility,
   governance-by-default, and clear ownership boundaries).

DX-006 acceptance criteria:
- One-command local startup for frontend/backend integration profile.
- Environment variables and service dependencies documented.

DX-006 deliverables:
- Local runtime profile (compose/devcontainer/or equivalent)
- Local runtime troubleshooting guide

Required close-out actions in the same PR:
1) Update docs/platform_roadmap.yaml and set DX-006 status to done once
   acceptance criteria are met.
2) Regenerate/update docs/next_dx_generation_prompt.md so it points to the next
   eligible roadmap item (expected next: DX-007 after DX-006 is done).
```

## Upcoming queue

After DX-006 is completed, the next queued item is DX-007 (depends on DX-003
and DX-006), then DX-008 (depends on DX-007).
