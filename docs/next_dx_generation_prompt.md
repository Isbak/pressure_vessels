# Next DX Generation Prompt (Roadmap-Aligned)

DX-008 is the next eligible item in `docs/platform_roadmap.yaml` as of 2026-04-19.

```text
Implement DX-008 from docs/platform_roadmap.yaml.

Reference documents to use:
- AGENT_GOVERNANCE.md#4-change-classification-and-merge-gates
- docs/developer_experience_principles.md
- docs/developer_command_reference.md

Eligibility rationale:
1) DX-001 is marked status: done.
2) DX-002 is marked status: done.
3) DX-003 is marked status: done.
4) DX-004 is marked status: done.
5) DX-005 is marked status: done.
6) DX-006 is marked status: done.
7) DX-007 is marked status: done.
8) DX-008 is the first item with status: todo.
9) DX-008 dependencies are satisfied (depends_on: [DX-007]).

Execution rules:
1) Implement only this single roadmap item with minimal, focused changes.
2) Follow AGENT_GOVERNANCE.md workflow and controls.
3) Do not start DX-009+ work in the same change.
4) Preserve developer experience principles (fast onboarding, reproducibility,
   governance-by-default, and clear ownership boundaries).

DX-008 acceptance criteria:
- Changed-file heuristics suggest low/medium/high risk labels.
- Suggestions are visible in PR workflow without auto-merging authority.

DX-008 deliverables:
- Risk suggestion workflow job
- Risk routing documentation

Required close-out actions in the same PR:
1) Update docs/platform_roadmap.yaml and set DX-008 status to done once
   acceptance criteria are met.
2) Regenerate/update docs/next_dx_generation_prompt.md so it points to the next
   eligible roadmap item (expected next: DX-009 after DX-008 is done).
```

## Upcoming queue

After DX-008 is completed, the next queued item is DX-009 (depends on DX-006),
then DX-010 (depends on DX-009).
