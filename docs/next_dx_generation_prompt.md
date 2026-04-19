# Next DX Generation Prompt (Roadmap-Aligned)

DX-009 is the next eligible item in `docs/platform_roadmap.yaml` as of 2026-04-19.

```text
Implement DX-009 from docs/platform_roadmap.yaml.

Reference documents to use:
- docs/interfaces/workflow_orchestrator_contract.md
- docs/interfaces/requirements_pipeline_contract.md
- docs/developer_experience_principles.md

Eligibility rationale:
1) DX-001 is marked status: done.
2) DX-002 is marked status: done.
3) DX-003 is marked status: done.
4) DX-004 is marked status: done.
5) DX-005 is marked status: done.
6) DX-006 is marked status: done.
7) DX-007 is marked status: done.
8) DX-008 is marked status: done.
9) DX-009 is the first item with status: todo.
10) DX-009 dependencies are satisfied (depends_on: [DX-006]).

Execution rules:
1) Implement only this single roadmap item with minimal, focused changes.
2) Follow AGENT_GOVERNANCE.md workflow and controls.
3) Do not start DX-010+ work in the same change.
4) Preserve developer experience principles (fast onboarding, reproducibility,
   governance-by-default, and clear ownership boundaries).

DX-009 acceptance criteria:
- Contract tests validate core frontend/backend and pipeline interfaces.
- Contract drift fails CI before merge.

DX-009 deliverables:
- Contract test suite
- CI job wiring for contract tests

Required close-out actions in the same PR:
1) Update docs/platform_roadmap.yaml and set DX-009 status to done once
   acceptance criteria are met.
2) Regenerate/update docs/next_dx_generation_prompt.md so it points to the next
   eligible roadmap item (expected next: DX-010 after DX-009 is done).
```

## Upcoming queue

After DX-009 is completed, the next queued item is DX-010 (depends on DX-009).
