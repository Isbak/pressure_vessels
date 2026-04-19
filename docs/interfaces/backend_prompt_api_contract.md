# Backend Prompt API Contract (DX-005)

This document defines the minimal backend API contract exposed in DX-005 for
frontend consumption.

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

## Endpoint: `GET /api/prompt?prompt=<text>`

### Purpose

Provides one deterministic prompt-processing route suitable for frontend wiring
and local development feedback loops.

### Query parameters

- `prompt` (required, string): free-form input text.

### Response (`200 OK`)

```json
{
  "prompt": "<normalized prompt>",
  "response": "Deterministic pipeline response: <normalized prompt>",
  "route": "deterministic-pipeline-v1"
}
```

### Error response (`400 Bad Request`)

```json
{
  "error": "prompt query parameter is required"
}
```

## Determinism rules

- Leading/trailing whitespace in `prompt` is trimmed.
- Internal consecutive whitespace is collapsed to a single space.
- The same normalized prompt always yields the same `response` string.
