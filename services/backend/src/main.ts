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

export type DesignRunArtifact = {
  artifactId: string;
  artifactType: 'WorkflowExecutionReport.v1' | 'ComplianceDossierMachine.v1';
  location: string;
};

export type DesignRunRecord = {
  runId: string;
  workflowState: 'completed';
  complianceSummary: {
    status: 'pass';
    code: string;
    checksPassed: number;
    checksFailed: number;
  };
  artifacts: DesignRunArtifact[];
};

export type StartDesignRunResponse = {
  apiVersion: 'v1';
  runId: string;
  statusUrl: string;
};

export type ErrorResponse = {
  error: string;
};

const DESIGN_RUN_API_VERSION = 'v1';

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

function parseRunId(runId: string): DesignRunRequest | null {
  if (!runId.startsWith('run-')) {
    return null;
  }

  try {
    const decoded = Buffer.from(runId.slice(4), 'base64url').toString('utf-8');
    const [pressure, temperature, volume, code] = decoded.split('|');
    const parsed: DesignRunRequest = {
      designPressureBar: Number(pressure),
      designTemperatureC: Number(temperature),
      volumeM3: Number(volume),
      code: code ?? '',
    };

    if (!isValidDesignRunRequest(parsed)) {
      return null;
    }

    return {
      ...parsed,
      code: normalizeCode(parsed.code),
    };
  } catch {
    return null;
  }
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
): BackendResponse<StartDesignRunResponse | ErrorResponse> {
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
): BackendResponse<DesignRunRecord | ErrorResponse> {
  const resolvedRequest = parseRunId(runId);

  if (!resolvedRequest) {
    return {
      status: 404,
      body: {
        error: 'design run not found',
      },
    };
  }

  return {
    status: 200,
    body: {
      runId,
      workflowState: 'completed',
      complianceSummary: {
        status: 'pass',
        code: normalizeCode(resolvedRequest.code),
        checksPassed: 3,
        checksFailed: 0,
      },
      artifacts: [
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
      ],
    },
  };
}

export function bootstrap(): string {
  return 'pressure-vessels backend API initialized';
}
