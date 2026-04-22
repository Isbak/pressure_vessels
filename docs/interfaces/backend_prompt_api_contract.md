# Backend Design-Run API Contract (BL-034, BL-047)

This document defines the versioned backend API contract exposed for frontend
integration and the BL-047 adapter wiring semantics used by runtime platform
services.

## Ownership

- Producer: `services/backend`
- Primary consumer: `services/frontend`

## Endpoint: `GET /health`

### Purpose

Provides a deterministic service health response for runtime checks.

### Response (`200 OK`)

```json
{
  "service": "pressure-vessels-backend",
  "status": "ok"
}
```

## Endpoint: `POST /api/v1/design-runs`

### Purpose

Starts a deterministic design run from a basic pressure-vessel input payload.

### Authorization

Requires `Authorization` header with provider-issued JWT bearer token:

`Authorization: Bearer <oidc-jwt>`

Provider verification is fail-closed and requires all of:

- Issuer from `PV_AUTH_PROVIDER_ISSUER`.
- Audience from `PV_AUTH_PROVIDER_AUDIENCE`.
- Verification keys from `PV_AUTH_PROVIDER_JWKS_JSON` loaded via approved module
  boundary path `infra/platform/secrets/module.boundaries.yaml`.
- JWT header constraints: `alg=HS256` and a known `kid`.
- JWT claims constraints: `sub`, `exp` (not expired), valid `iss`, valid `aud`.
- Role claim in `realm_access.roles` constrained to `engineer`, `reviewer`,
  `approver` (deterministic first-match order).
- Scope claim from `scope` or `scp`; this endpoint requires `design_runs:write`.

### Required adapter configuration (fail-closed)

The endpoint fails closed (`503`) when required runtime adapters are not fully
configured from environment:

- `PV_POSTGRES_URL`
- `PV_POSTGRES_SCHEMA`
- `PV_REDIS_URL`
- `PV_REDIS_NAMESPACE`

The backend must persist run state using the PostgreSQL adapter and write/read
hot run status through the Redis adapter. Runtime implementations use the
`psql` and `redis-cli` runtime clients so adapter wiring remains environment
driven and fails closed when either client or endpoint is unavailable.

### Request body

```json
{
  "designPressureBar": 18,
  "designTemperatureC": 65,
  "volumeM3": 30,
  "code": "ASME Section VIII Div 1"
}
```

### Response (`201 Created`)

```json
{
  "apiVersion": "v1",
  "runId": "run-<deterministic-id>",
  "statusUrl": "/api/v1/design-runs/run-<deterministic-id>"
}
```

### Error response (`400 Bad Request`)

```json
{
  "error": "designPressureBar, designTemperatureC, volumeM3, and code are required in the request body"
}
```

### Error responses (`401 Unauthorized`, `403 Forbidden`, `503 Service Unavailable`)

```json
{
  "error": "missing authorization token"
}
```

```json
{
  "error": "invalid authorization token"
}
```

```json
{
  "error": "insufficient scope: requires design_runs:write"
}
```

```json
{
  "error": "backend adapter configuration error (postgresql): PV_POSTGRES_URL and PV_POSTGRES_SCHEMA are required for backend design-run state"
}
```

## Endpoint: `GET /api/v1/design-runs/{runId}`

### Purpose

Returns deterministic workflow state, compliance summary, and artifact
references for a previously started design run.

### Authorization

Requires `Authorization` header with provider-issued JWT bearer token:

`Authorization: Bearer <oidc-jwt>`

- Role is resolved from `realm_access.roles` and must be one of `engineer`,
  `reviewer`, `approver`.
- Scope is resolved from `scope`/`scp` and must be `design_runs:read` or
  stronger `design_runs:write`.

### Response (`200 OK`)

```json
{
  "runId": "run-<deterministic-id>",
  "workflowState": "completed",
  "complianceSummary": {
    "status": "pass",
    "code": "ASME SECTION VIII DIV 1",
    "checksPassed": 3,
    "checksFailed": 0
  },
  "artifacts": [
    {
      "artifactId": "run-<deterministic-id>-workflow",
      "artifactType": "WorkflowExecutionReport.v1",
      "location": "artifacts/bl-016/WorkflowExecutionReport.v1.sample.json"
    },
    {
      "artifactId": "run-<deterministic-id>-compliance",
      "artifactType": "ComplianceDossierMachine.v1",
      "location": "artifacts/bl-004/ComplianceDossierMachine.v1.json"
    }
  ]
}
```

### Error response (`404 Not Found`)

```json
{
  "error": "design run not found"
}
```

### Error responses (`401 Unauthorized`, `403 Forbidden`, `503 Service Unavailable`)

```json
{
  "error": "missing authorization token"
}
```

```json
{
  "error": "invalid token issuer"
}
```

```json
{
  "error": "invalid token audience"
}
```

```json
{
  "error": "token expired or missing exp claim"
}
```

```json
{
  "error": "insufficient scope: requires design_runs:read"
}
```

```json
{
  "error": "failed to read design run via redis: Redis adapter is not configured for reads"
}
```

## Platform integration interfaces and deterministic semantics (BL-047)

BL-047 requires explicit interface slots for platform integrations used by
traceability, retrieval, orchestration, and LLM-assist features.

Environment mode variable for each service:

- `PV_NEO4J_MODE`
- `PV_QDRANT_MODE`
- `PV_OPENSEARCH_MODE`
- `PV_TEMPORAL_MODE`
- `PV_LLM_SERVING_MODE`

Each mode accepts:

- `required`: endpoint + credential are mandatory; missing values fail closed.
- `deterministic-fallback` (default): endpoint/credential may be omitted and the
  adapter reports deterministic fallback mode.
- Any other mode value fails closed during adapter registry bootstrap with
  `ADAPTER_CONFIG_MISSING`.

Expected endpoint + credential variables by service:

- Neo4j: `PV_NEO4J_ENDPOINT`, `PV_NEO4J_TOKEN`
- Qdrant: `PV_QDRANT_ENDPOINT`, `PV_QDRANT_API_KEY`
- OpenSearch: `PV_OPENSEARCH_ENDPOINT`, `PV_OPENSEARCH_API_KEY`
- Temporal: `PV_TEMPORAL_ENDPOINT`, `PV_TEMPORAL_TOKEN`
- LLM serving: `PV_LLM_SERVING_ENDPOINT`, `PV_LLM_SERVING_API_KEY`

## Determinism rules

- `code` is normalized to uppercase with collapsed internal whitespace.
- Identical request payloads yield the same `runId`.
- Run status resolution order is deterministic: Redis cache first, then
  PostgreSQL persistence.
- Artifact references are fixed to immutable sample artifact locations.
- Auth verification is provider-backed JWT signature + claims validation,
  followed by deterministic role/scope enforcement; all failures are fail closed.
- Required adapter configuration failures return deterministic `503` errors.
- Platform services configured in `required` mode are validated during adapter
  registry bootstrap; readiness failures fail closed before request handling.
