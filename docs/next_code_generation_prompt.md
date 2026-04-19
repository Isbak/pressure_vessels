# Next Code Generation Prompt (Roadmap-Aligned)

A new Phase 5 runtime-deployment tranche (BL-027..BL-033) was queued on 2026-04-19 to cover the remaining `planned` components in `docs/platform_runtime_stack_registry.yaml`.

```text
You are working from `docs/development_backlog.yaml` for the `pressure_vessels` repository.

1) Identify the first backlog item whose status is not `done`.
2) Restate the selected item ID/title, dependencies, and roadmap source before coding.
3) If dependencies are not all `done`, set the item to `blocked` and stop with a dependency report.
4) If dependencies are complete, implement the item with minimal focused changes, tests, and docs updates.
5) Update the item status when complete and refresh this prompt to point at the next pending item.
```

## Upcoming queue

The following items are queued in dependency order. Each delivers a runtime
module skeleton (`infra/platform/<component>/`), wires the module into
`infra/platform/environment.bootstrap.yaml` for the targeted environments, and
flips the corresponding entry in `docs/platform_runtime_stack_registry.yaml`
and the `## Current` section of `docs/tech-stack.md` from `planned` to
`deployed`.

- **BL-027** Deliver identity (Keycloak) runtime module — depends on BL-018, BL-021, BL-022.
- **BL-028** Deliver workflow orchestration (Temporal) runtime module — depends on BL-016, BL-018, BL-021.
- **BL-029** Deliver knowledge graph (Neo4j) runtime module — depends on BL-006, BL-018, BL-021.
- **BL-030** Deliver vector retrieval (Qdrant) runtime module — depends on BL-018, BL-021.
- **BL-031** Deliver search/analytics (OpenSearch) runtime module — depends on BL-018, BL-021.
- **BL-032** Deliver LLM serving (vLLM) runtime module — depends on BL-018, BL-021, BL-022.
- **BL-033** Deliver model catalog (Llama/Mistral/Qwen) runtime module — depends on BL-018, BL-032.
