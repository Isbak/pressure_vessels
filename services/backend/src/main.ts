import {
  DesignRunArtifact,
  PersistedDesignRunRecord,
} from './adapters/interfaces';
import { createAdapterRegistry, readDesignRunRecord } from './adapters/registry';
import { getRuntimeAuthProviderConfig } from './secrets';
import { createHmac, timingSafeEqual } from 'node:crypto';

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

  const token = parseJwt(authToken.trim());
  if (!token.ok) {
    return {
      status: 401,
      body: {
        error: token.error,
      },
    };
  }

  const validated = validateProviderClaims(token.value);
  if (!validated.ok) {
    return {
      status: 401,
      body: {
        error: validated.error,
      },
    };
  }

  const {
    actorId,
    role,
    scope,
  } = validated.value;
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

type JwtHeader = {
  alg: string;
  kid?: string;
  typ?: string;
};

type JwtPayload = {
  sub?: string;
  iss?: string;
  aud?: string | string[];
  exp?: number;
  nbf?: number;
  iat?: number;
  scope?: string;
  scp?: string[];
  realm_access?: {
    roles?: string[];
  };
};

type RuntimeJwt = {
  header: JwtHeader;
  payload: JwtPayload;
  signingInput: string;
  signature: string;
};

type AuthDecision<T> = {
  ok: true;
  value: T;
} | {
  ok: false;
  error: string;
};

function parseJwt(token: string): AuthDecision<RuntimeJwt> {
  const segments = token.split('.');
  if (segments.length !== 3) {
    return {
      ok: false,
      error: 'invalid authorization token',
    };
  }

  const [encodedHeader, encodedPayload, signature] = segments;
  if (!encodedHeader || !encodedPayload || !signature) {
    return {
      ok: false,
      error: 'invalid authorization token',
    };
  }

  try {
    const header = JSON.parse(Buffer.from(encodedHeader, 'base64url').toString('utf8')) as JwtHeader;
    const payload = JSON.parse(Buffer.from(encodedPayload, 'base64url').toString('utf8')) as JwtPayload;
    return {
      ok: true,
      value: {
        header,
        payload,
        signingInput: `${encodedHeader}.${encodedPayload}`,
        signature,
      },
    };
  } catch (_error) {
    return {
      ok: false,
      error: 'invalid authorization token',
    };
  }
}

function validateProviderClaims(token: RuntimeJwt): AuthDecision<RuntimeAuthContext> {
  const provider = getRuntimeAuthProviderConfig();
  if (token.header.alg !== 'HS256' || !token.header.kid) {
    return { ok: false, error: 'invalid authorization token' };
  }

  const key = provider.keys.find((candidate) => candidate.kid === token.header.kid);
  if (!key) {
    return { ok: false, error: 'invalid authorization token' };
  }

  const expectedSignature = createHmac('sha256', key.secret)
    .update(token.signingInput)
    .digest('base64url');
  const expectedBuffer = Buffer.from(expectedSignature, 'utf8');
  const providedBuffer = Buffer.from(token.signature, 'utf8');
  if (
    expectedBuffer.length !== providedBuffer.length ||
    !timingSafeEqual(expectedBuffer, providedBuffer)
  ) {
    return { ok: false, error: 'invalid authorization token' };
  }

  const now = Math.floor(Date.now() / 1000);
  if (typeof token.payload.exp !== 'number' || token.payload.exp <= now) {
    return { ok: false, error: 'token expired or missing exp claim' };
  }
  if (typeof token.payload.nbf === 'number' && token.payload.nbf > now) {
    return { ok: false, error: 'token is not active yet' };
  }

  if (token.payload.iss !== provider.issuer) {
    return { ok: false, error: 'invalid token issuer' };
  }

  const audiences = Array.isArray(token.payload.aud)
    ? token.payload.aud
    : typeof token.payload.aud === 'string'
      ? [token.payload.aud]
      : [];
  if (!audiences.includes(provider.audience)) {
    return { ok: false, error: 'invalid token audience' };
  }

  const role = resolveRole(token.payload.realm_access?.roles ?? []);
  if (!role) {
    return { ok: false, error: 'invalid authorization token' };
  }

  const scope = resolveScope(token.payload);
  if (!scope) {
    return { ok: false, error: 'invalid authorization token' };
  }

  if (!token.payload.sub || token.payload.sub.trim().length === 0) {
    return { ok: false, error: 'invalid authorization token' };
  }

  return {
    ok: true,
    value: {
      actorId: token.payload.sub.trim(),
      role,
      scope,
    },
  };
}

function resolveRole(roles: string[]): AuthRole | null {
  for (const allowedRole of ALLOWED_AUTH_ROLES) {
    if (roles.includes(allowedRole)) {
      return allowedRole;
    }
  }

  return null;
}

function resolveScope(payload: JwtPayload): RuntimeAuthContext['scope'] | null {
  const scopeClaims: string[] = [];
  if (typeof payload.scope === 'string') {
    scopeClaims.push(...payload.scope.split(' '));
  }
  if (Array.isArray(payload.scp)) {
    scopeClaims.push(...payload.scp);
  }

  if (scopeClaims.includes('design_runs:write')) {
    return 'design_runs:write';
  }
  if (scopeClaims.includes('design_runs:read')) {
    return 'design_runs:read';
  }
  return null;
}
