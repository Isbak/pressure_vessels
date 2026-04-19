# Next DX Generation Prompt (Roadmap-Aligned)

DX-005 is the next eligible item in `docs/platform_roadmap.yaml` as of 2026-04-19.

```text
Implement DX-005 from docs/platform_roadmap.yaml.

Reference documents to use:
- docs/developer_experience_principles.md
- services/backend/README.md#backend-service-skeleton
- AGENT_GOVERNANCE.md

Eligibility rationale:
1) DX-001 is marked status: done.
2) DX-002 is marked status: done.
3) DX-003 is marked status: done.
4) DX-004 is marked status: done.
5) DX-005 is the first item with status: todo.
6) DX-005 dependency is satisfied (depends_on: [DX-004]).

Execution rules:
1) Implement only this single roadmap item with minimal, focused changes.
2) Follow AGENT_GOVERNANCE.md workflow and controls.
3) Do not start DX-005+ work in the same change.
4) Preserve developer experience principles (fast onboarding, reproducibility,
   governance-by-default, and clear ownership boundaries).

DX-005 acceptance criteria:
- Backend exposes health endpoint and one deterministic pipeline route.
- API contract documented for frontend consumption.

DX-005 deliverables:
- Backend endpoints
- API contract document

Required close-out actions in the same PR:
1) Update docs/platform_roadmap.yaml and set DX-005 status to done once
   acceptance criteria are met.
2) Regenerate/update docs/next_dx_generation_prompt.md so it points to the next
   eligible roadmap item (expected next: DX-006 after DX-005 is done).
```

## Upcoming queue

After DX-005 is completed, the next queued item is DX-006 (depends on DX-005),
then DX-007 (depends on DX-003 and DX-006).
