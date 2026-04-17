# ADR-0002: LLM Serving Runtime (vLLM)

- Status: Accepted
- Date: 2026-04-17

## Context
The platform requires self-hosted, open-software model inference for agentic workflows, with predictable latency and high throughput.

## Decision
Adopt **vLLM** as the primary production LLM serving runtime. Use Ollama for local developer-only workflows where appropriate.

## Alternatives Considered
- Hugging Face TGI
- Ollama-only

## Consequences
- Improves production throughput and batching efficiency.
- Adds operational complexity compared with developer-local runtimes.
- Requires benchmark validation for model upgrades.

## Rollback / Migration Trigger
Rollback if vLLM cannot meet defined SLOs or blocks required model support; fallback candidate is TGI.
