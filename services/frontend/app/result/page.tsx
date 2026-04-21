import Link from 'next/link';
import { headers } from 'next/headers';

import type { DesignRunRequest, DesignRunResponse } from '../../lib/prompt-contract';

type ResultPageProps = {
  searchParams: {
    designPressureBar?: string;
    designTemperatureC?: string;
    volumeM3?: string;
    code?: string;
  };
};

function parsePayload(searchParams: ResultPageProps['searchParams']): DesignRunRequest | null {
  const designPressureBar = Number(searchParams.designPressureBar ?? '');
  const designTemperatureC = Number(searchParams.designTemperatureC ?? '');
  const volumeM3 = Number(searchParams.volumeM3 ?? '');
  const code = (searchParams.code ?? '').trim();

  if (
    !Number.isFinite(designPressureBar) ||
    designPressureBar <= 0 ||
    !Number.isFinite(designTemperatureC) ||
    !Number.isFinite(volumeM3) ||
    volumeM3 <= 0 ||
    !code
  ) {
    return null;
  }

  return {
    designPressureBar,
    designTemperatureC,
    volumeM3,
    code,
  };
}

async function getDesignRunResult(payload: DesignRunRequest): Promise<DesignRunResponse> {
  const headerStore = headers();
  const host = headerStore.get('host');

  if (!host) {
    throw new Error('Host header missing.');
  }

  const protocol =
    headerStore.get('x-forwarded-proto') ??
    (host.includes('localhost') ? 'http' : 'https');

  const endpoint = new URL('/api/prompt', `${protocol}://${host}`);

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error('Design run request failed.');
  }

  return (await response.json()) as DesignRunResponse;
}

export default async function ResultPage({
  searchParams,
}: ResultPageProps): Promise<JSX.Element> {
  const payload = parsePayload(searchParams);

  if (!payload) {
    return (
      <main>
        <h1>Design Run Result</h1>
        <p>Invalid or missing design input payload. Submit the form again.</p>
        <Link href="/">Back to design run form</Link>
      </main>
    );
  }

  try {
    const result = await getDesignRunResult(payload);

    return (
      <main>
        <h1>Design Run Result</h1>
        <p>
          <strong>Run ID:</strong> {result.runId}
        </p>
        <p>
          <strong>Workflow state:</strong> {result.workflowState}
        </p>
        <p>
          <strong>Compliance status:</strong> {result.complianceSummary.status} (
          {result.complianceSummary.code})
        </p>
        <p>
          <strong>Checks:</strong> {result.complianceSummary.checksPassed} passed /{' '}
          {result.complianceSummary.checksFailed} failed
        </p>
        <p>
          <strong>Data source:</strong> {result.source}
        </p>
        <h2>Artifacts</h2>
        <ul>
          {result.artifacts.map((artifact) => (
            <li key={artifact.artifactId}>
              {artifact.artifactType}: {artifact.location}
            </li>
          ))}
        </ul>
        <Link href="/">Run another design case</Link>
      </main>
    );
  } catch {
    return (
      <main>
        <h1>Design Run Result</h1>
        <p>Could not load design run status for the submitted payload.</p>
        <Link href="/">Run another design case</Link>
      </main>
    );
  }
}
