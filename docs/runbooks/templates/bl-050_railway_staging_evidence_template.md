# BL-050 Railway Staging Evidence Template

- Backlog item: `BL-050`
- Deployment window (UTC): `<start>` to `<end>`
- Operator: `<name>`
- Reviewer: `<name>`

## 1) Railway deployment identifiers

| Service | Railway deployment ID | Commit SHA | Timestamp (UTC) |
| --- | --- | --- | --- |
| backend | `<id>` | `<sha>` | `<ts>` |
| frontend | `<id>` | `<sha>` | `<ts>` |
| llm-serving | `<id>` | `<sha-or-n/a>` | `<ts>` |
| neo4j | `<id>` | `<sha-or-n/a>` | `<ts>` |
| qdrant | `<id>` | `<sha-or-n/a>` | `<ts>` |
| opensearch | `<id>` | `<sha-or-n/a>` | `<ts>` |
| temporal | `<id>` | `<sha-or-n/a>` | `<ts>` |

## 2) Required backend integration variable attestations

Record names only (no secret values).

- [ ] `PV_LLM_SERVING_MODE=required`
- [ ] `PV_LLM_SERVING_ENDPOINT`
- [ ] `PV_LLM_SERVING_API_KEY`
- [ ] `PV_NEO4J_MODE=required`
- [ ] `PV_NEO4J_ENDPOINT`
- [ ] `PV_NEO4J_TOKEN`
- [ ] `PV_QDRANT_MODE=required`
- [ ] `PV_QDRANT_ENDPOINT`
- [ ] `PV_QDRANT_API_KEY`
- [ ] `PV_OPENSEARCH_MODE=required`
- [ ] `PV_OPENSEARCH_ENDPOINT`
- [ ] `PV_OPENSEARCH_API_KEY`
- [ ] `PV_TEMPORAL_MODE=required`
- [ ] `PV_TEMPORAL_ENDPOINT`
- [ ] `PV_TEMPORAL_TOKEN`

## 3) Service-by-service fail-closed smoke checks

| Service | Variable temporarily removed | Expected result | Actual result | Evidence link |
| --- | --- | --- | --- | --- |
| llm-serving | `PV_LLM_SERVING_API_KEY` | Backend startup fails with `ADAPTER_CONFIG_MISSING` | `<result>` | `<log/screenshot>` |
| neo4j | `PV_NEO4J_TOKEN` | Backend startup fails with `ADAPTER_CONFIG_MISSING` | `<result>` | `<log/screenshot>` |
| qdrant | `PV_QDRANT_API_KEY` | Backend startup fails with `ADAPTER_CONFIG_MISSING` | `<result>` | `<log/screenshot>` |
| opensearch | `PV_OPENSEARCH_API_KEY` | Backend startup fails with `ADAPTER_CONFIG_MISSING` | `<result>` | `<log/screenshot>` |
| temporal | `PV_TEMPORAL_TOKEN` | Backend startup fails with `ADAPTER_CONFIG_MISSING` | `<result>` | `<log/screenshot>` |

## 4) Recovery and functional checks after variable restore

- [ ] `GET /health` returned `200` after each restore/redeploy cycle.
- [ ] `POST /api/v1/design-runs` returned `201` with valid JWT.
- [ ] `GET /api/v1/design-runs/{runId}` returned `200` with valid JWT.
- [ ] Frontend `/api/prompt` call path to backend succeeded.

## 5) Rollback execution record (if triggered)

| Trigger condition | Rollback target | Timestamp (UTC) | Validation checks after rollback | Incident/ref |
| --- | --- | --- | --- | --- |
| `<condition>` | `<backend/frontend/service>` | `<ts>` | `<health + smoke outcomes>` | `<ticket>` |

## 6) Final sign-off

- Result: `<pass | pass-with-follow-up | fail>`
- Follow-up backlog item(s): `<id list or none>`
- Operator sign-off: `<name/time>`
- Reviewer sign-off: `<name/time>`
