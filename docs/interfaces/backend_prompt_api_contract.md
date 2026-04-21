# Backend Design-Run API Contract (BL-034)

This document defines the minimal versioned backend API contract exposed in
BL-034 for frontend design-run execution.

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

## Endpoint: `GET /api/v1/design-runs/{runId}`

### Purpose

Returns deterministic workflow state, compliance summary, and artifact
references for a previously started design run.

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

## Determinism rules

- `code` is normalized to uppercase with collapsed internal whitespace.
- Identical request payloads yield the same `runId` and status payload.
- Artifact references are fixed to immutable sample artifact locations.
