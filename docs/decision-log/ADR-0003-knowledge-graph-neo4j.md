# ADR-0003: Knowledge Graph Store (Neo4j Community)

- Status: Accepted

- Date: 2026-04-17

## Context

The platform needs graph-native reasoning for standards clauses, requirement traceability, and evidence links across design artifacts.

## Decision

Adopt **Neo4j Community** as the primary knowledge graph store.

## Alternatives Considered

- JanusGraph

- ArangoDB

## Consequences

- Enables expressive graph traversal and lineage queries.

- Introduces dedicated graph schema and backup lifecycle to operations.

- Requires integration guidance for graph + vector hybrid retrieval.

## Rollback / Migration Trigger

Rollback if scale or operational limits materially impact delivery; fallback candidate is JanusGraph.
