# ADR-0004: Vector Retrieval Store (Qdrant)

- Status: Accepted

- Date: 2026-04-17


## Context

Agentic retrieval workflows require open-source semantic retrieval integrated with knowledge graph and standards-aware search.

## Decision

Adopt **Qdrant** as the default vector retrieval store.

## Alternatives Considered

- Weaviate

- Milvus


## Consequences

- Supports high-quality semantic retrieval with manageable operational footprint.

- Requires embedding schema governance and re-index processes.

- Must be validated regularly against retrieval quality benchmarks.


## Rollback / Migration Trigger

Rollback if quality, latency, or maintenance burden degrades beyond SLO thresholds; fallback candidate is Weaviate.
