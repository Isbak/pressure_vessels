# Next DX Generation Prompt (Roadmap-Aligned)

DX-010 is the next eligible item in `docs/platform_roadmap.yaml` as of 2026-04-19.

```text
Implement DX-010 from docs/platform_roadmap.yaml.

Reference documents to use:
- docs/developer_experience_principles.md
- docs/runbooks/platform_runtime_stack_operations.md
- AGENT_GOVERNANCE.md

Eligibility rationale:
1) DX-001 is marked status: done.
2) DX-002 is marked status: done.
3) DX-003 is marked status: done.
4) DX-004 is marked status: done.
5) DX-005 is marked status: done.
6) DX-006 is marked status: done.
7) DX-007 is marked status: done.
8) DX-008 is marked status: done.
9) DX-009 is marked status: done.
10) DX-010 is the first item with status: todo.
11) DX-010 dependencies are satisfied (depends_on: [DX-009]).

Execution rules:
1) Implement only this single roadmap item with minimal, focused changes.
2) Follow AGENT_GOVERNANCE.md workflow and controls.
3) Do not start DX-011+ work in the same change.
4) Preserve developer experience principles (fast onboarding, reproducibility,
   governance-by-default, and clear ownership boundaries).

DX-010 acceptance criteria:
- Pull requests can launch isolated preview environment links.
- Preview teardown policy is deterministic and documented.

DX-010 deliverables:
- Preview environment workflow
- Preview lifecycle operations runbook

Required close-out actions in the same PR:
1) Update docs/platform_roadmap.yaml and set DX-010 status to done once
   acceptance criteria are met.
2) Regenerate/update docs/next_dx_generation_prompt.md so it points to the next
   eligible roadmap item after DX-010.
```

## Upcoming queue

After DX-010 is completed, the next queued roadmap item should be selected from
the first remaining `status: todo` entry.
