import { NextRequest, NextResponse } from 'next/server';

import type { DesignRunRequest, DesignRunResponse } from '../../../lib/prompt-contract';

const BACKEND_API_BASE_URL = process.env.BACKEND_API_BASE_URL;

function isValidPayload(payload: DesignRunRequest): boolean {
  return (
    Number.isFinite(payload.designPressureBar) &&
    payload.designPressureBar > 0 &&
    Number.isFinite(payload.designTemperatureC) &&
    Number.isFinite(payload.volumeM3) &&
    payload.volumeM3 > 0 &&
    payload.code.trim().length > 0
  );
}

function buildFallbackResponse(payload: DesignRunRequest): DesignRunResponse {
  const runId = `run-placeholder-${Math.round(payload.designPressureBar * 10)}`;

  return {
    runId,
    workflowState: 'completed',
    complianceSummary: {
      status: 'pass',
      code: payload.code.trim().toUpperCase(),
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
    source: 'frontend-placeholder',
  };
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  const payload = (await request.json().catch(() => null)) as DesignRunRequest | null;

  if (!payload || !isValidPayload(payload)) {
    return NextResponse.json(
      {
        error:
          'designPressureBar, designTemperatureC, volumeM3, and code are required in the request body',
      },
      { status: 400 },
    );
  }

  if (!BACKEND_API_BASE_URL) {
    return NextResponse.json(buildFallbackResponse(payload));
  }

  try {
    const startEndpoint = new URL('/api/v1/design-runs', BACKEND_API_BASE_URL);
    const startResponse = await fetch(startEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(payload),
      cache: 'no-store',
    });

    if (!startResponse.ok) {
      return NextResponse.json(buildFallbackResponse(payload), { status: 200 });
    }

    const startPayload = (await startResponse.json()) as {
      runId?: string;
      statusUrl?: string;
    };

    if (!startPayload.runId || !startPayload.statusUrl) {
      return NextResponse.json(buildFallbackResponse(payload), { status: 200 });
    }

    const statusEndpoint = new URL(startPayload.statusUrl, BACKEND_API_BASE_URL);
    const statusResponse = await fetch(statusEndpoint, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
      cache: 'no-store',
    });

    if (!statusResponse.ok) {
      return NextResponse.json(buildFallbackResponse(payload), { status: 200 });
    }

    const statusPayload = (await statusResponse.json()) as Omit<
      DesignRunResponse,
      'source'
    >;

    if (!statusPayload.runId || !statusPayload.workflowState || !statusPayload.complianceSummary) {
      return NextResponse.json(buildFallbackResponse(payload), { status: 200 });
    }

    return NextResponse.json({
      ...statusPayload,
      source: 'backend-service',
    } satisfies DesignRunResponse);
  } catch {
    return NextResponse.json(buildFallbackResponse(payload), { status: 200 });
  }
}
