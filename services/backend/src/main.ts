import {
  DesignRunArtifact,
  PersistedDesignRunRecord,
} from './adapters/interfaces';
import { createAdapterRegistry, readDesignRunRecord } from './adapters/registry';
import { getRuntimeAuthSecret } from './secrets';

export type BackendResponse<T> = {
  status: number;
  body: T;
};

export type HealthResponse = {
  service: 'pressure-vessels-backend';
  status: 'ok';
};

export type DesignRunRequest = {
  designPressureBar: number;
  designTemperatureC: number;
  volumeM3: number;
  code: string;
};

export type DesignRunRecord = PersistedDesignRunRecord;

export type StartDesignRunResponse = {
  apiVersion: 'v1';
  runId: string;
  statusUrl: string;
};

export type ErrorResponse = {
  error: string;
};

const DESIGN_RUN_API_VERSION = 'v1';
const AUTH_TOKEN_VERSION = 'v1';
const ALLOWED_AUTH_ROLES = ['engineer', 'reviewer', 'approver'] as const;

type AuthRole = (typeof ALLOWED_AUTH_ROLES)[number];

export type RuntimeAuthContext = {
  actorId: string;
  role: AuthRole;
  scope: 'design_runs:write' | 'design_runs:read';
};

const adapterRegistry = createAdapterRegistry(process.env);

function normalizeCode(code: string): string {
  return code.trim().toUpperCase().replace(/\s+/g, ' ');
}

function toDeterministicRunId(request: DesignRunRequest): string {
  const raw = [
    request.designPressureBar.toFixed(3),
    request.designTemperatureC.toFixed(3),
    request.volumeM3.toFixed(3),
    normalizeCode(request.code),
  ].join('|');

  const encoded = Buffer.from(raw).toString('base64url').slice(0, 16);
  return `run-${encoded}`;
}

function isValidDesignRunRequest(request: DesignRunRequest): boolean {
  return (
    Number.isFinite(request.designPressureBar) &&
    request.designPressureBar > 0 &&
    Number.isFinite(request.designTemperatureC) &&
    Number.isFinite(request.volumeM3) &&
    request.volumeM3 > 0 &&
    normalizeCode(request.code).length > 0
  );
}

function toDesignRunArtifacts(runId: string): DesignRunArtifact[] {
  return [
    {
      artifactId: `${runId}-workflow`,
      artifactType: 'WorkflowExecutionReport.v1',
      location: 'artifacts/bl-016/WorkflowExecutionReport.v1.sample.json',
    },
    {
      artifactId: `${runId}-compliance`,
      artifactType: 'ComplianceDossierMachine.v1',
      location: 'artifacts/bl-004/ComplianceDossierMachine.v1.json',
    },
  ];
}

function toPersistedRecord(runId: string, request: DesignRunRequest): PersistedDesignRunRecord {
  return {
    runId,
    workflowState: 'completed',
    complianceSummary: {
      status: 'pass',
      code: normalizeCode(request.code),
      checksPassed: 3,
      checksFailed: 0,
    },
    artifacts: toDesignRunArtifacts(runId),
  };
}

function toAdapterConfigurationError(): BackendResponse<ErrorResponse> {
  if (adapterRegistry.ok) {
    return {
      status: 500,
      body: { error: 'unexpected adapter configuration state' },
    };
  }

  return {
    status: 503,
    body: {
      error: `backend adapter configuration error (${adapterRegistry.error.adapter}): ${adapterRegistry.error.message}`,
    },
  };
}

export function getHealth(): BackendResponse<HealthResponse> {
  return {
    status: 200,
    body: {
      service: 'pressure-vessels-backend',
      status: 'ok',
    },
  };
}

export function startDesignRun(
  request: DesignRunRequest,
  authToken: string,
): BackendResponse<StartDesignRunResponse | ErrorResponse> {
  const authResult = authorizeRuntimeToken(authToken, 'design_runs:write');
  if (authResult.status !== 200) {
    return authResult;
  }

  if (!adapterRegistry.ok) {
    return toAdapterConfigurationError();
  }

  if (!isValidDesignRunRequest(request)) {
    return {
      status: 400,
      body: {
        error:
          'designPressureBar, designTemperatureC, volumeM3, and code are required in the request body',
      },
    };
  }

  const runId = toDeterministicRunId({
    ...request,
    code: normalizeCode(request.code),
  });
  const record = toPersistedRecord(runId, request);

  const persisted = adapterRegistry.value.runStateStore.persist(record);
  if (!persisted.ok) {
    return {
      status: 503,
      body: {
        error: `failed to persist design run via ${persisted.error.adapter}: ${persisted.error.message}`,
      },
    };
  }

  const cached = adapterRegistry.value.runCache.write(record);
  if (!cached.ok) {
    return {
      status: 503,
      body: {
        error: `failed to cache design run via ${cached.error.adapter}: ${cached.error.message}`,
      },
    };
  }

  return {
    status: 201,
    body: {
      apiVersion: DESIGN_RUN_API_VERSION,
      runId,
      statusUrl: `/api/${DESIGN_RUN_API_VERSION}/design-runs/${runId}`,
    },
  };
}

export function getDesignRunStatus(
  runId: string,
  authToken: string,
): BackendResponse<DesignRunRecord | ErrorResponse> {
  const authResult = authorizeRuntimeToken(authToken, 'design_runs:read');
  if (authResult.status !== 200) {
    return authResult;
  }

  if (!adapterRegistry.ok) {
    return toAdapterConfigurationError();
  }

  const record = readDesignRunRecord(adapterRegistry.value, runId);
  if (!record.ok) {
    return {
      status: 503,
      body: {
        error: `failed to read design run via ${record.error.adapter}: ${record.error.message}`,
      },
    };
  }

  if (!record.value) {
    return {
      status: 404,
      body: {
        error: 'design run not found',
      },
    };
  }

  return {
    status: 200,
    body: record.value,
  };
}

export function bootstrap(): string {
  return 'pressure-vessels backend API initialized';
}

export function authorizeRuntimeToken(
  authToken: string,
  requiredScope: RuntimeAuthContext['scope'],
): BackendResponse<RuntimeAuthContext | ErrorResponse> {
  if (!authToken || authToken.trim().length === 0) {
    return {
      status: 401,
      body: {
        error: 'missing authorization token',
      },
    };
  }

  const secret = getRuntimeAuthSecret();
  const [version, actorId, role, scope, tokenSecret] = authToken.split(':');
  if (
    version !== AUTH_TOKEN_VERSION ||
    !actorId ||
    !ALLOWED_AUTH_ROLES.includes(role as AuthRole) ||
    (scope !== 'design_runs:write' && scope !== 'design_runs:read') ||
    tokenSecret !== secret
  ) {
    return {
      status: 401,
      body: {
        error: 'invalid authorization token',
      },
    };
  }

  if (scope !== requiredScope && !(requiredScope === 'design_runs:read' && scope === 'design_runs:write')) {
    return {
      status: 403,
      body: {
        error: `insufficient scope: requires ${requiredScope}`,
      },
    };
  }

  return {
    status: 200,
    body: {
      actorId,
      role,
      scope,
    },
  };
}
