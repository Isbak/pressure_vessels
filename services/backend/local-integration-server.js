const http = require('node:http');
const { URL } = require('node:url');

const host = process.env.BACKEND_HOST || '0.0.0.0';
const port = Number(process.env.BACKEND_PORT || '8000');

function normalizeCode(code) {
  return String(code || '')
    .trim()
    .toUpperCase()
    .replace(/\s+/g, ' ');
}

function writeJson(response, statusCode, body) {
  response.writeHead(statusCode, { 'Content-Type': 'application/json' });
  response.end(JSON.stringify(body));
}

function parseJsonBody(request) {
  return new Promise((resolve, reject) => {
    let raw = '';

    request.on('data', (chunk) => {
      raw += chunk;
    });

    request.on('end', () => {
      if (!raw) {
        resolve({});
        return;
      }

      try {
        resolve(JSON.parse(raw));
      } catch (error) {
        reject(error);
      }
    });

    request.on('error', reject);
  });
}

function isValidDesignRunRequest(payload) {
  return (
    Number.isFinite(payload.designPressureBar) &&
    payload.designPressureBar > 0 &&
    Number.isFinite(payload.designTemperatureC) &&
    Number.isFinite(payload.volumeM3) &&
    payload.volumeM3 > 0 &&
    normalizeCode(payload.code).length > 0
  );
}

function toRunId(payload) {
  const raw = [
    payload.designPressureBar.toFixed(3),
    payload.designTemperatureC.toFixed(3),
    payload.volumeM3.toFixed(3),
    normalizeCode(payload.code),
  ].join('|');
  return `run-${Buffer.from(raw).toString('base64url').slice(0, 16)}`;
}

function parseRunId(runId) {
  if (!runId.startsWith('run-')) {
    return null;
  }

  try {
    const decoded = Buffer.from(runId.slice(4), 'base64url').toString('utf-8');
    const [pressure, temperature, volume, code] = decoded.split('|');
    const payload = {
      designPressureBar: Number(pressure),
      designTemperatureC: Number(temperature),
      volumeM3: Number(volume),
      code,
    };

    return isValidDesignRunRequest(payload) ? payload : null;
  } catch {
    return null;
  }
}

const server = http.createServer(async (request, response) => {
  if (!request.url || !request.method) {
    writeJson(response, 400, { error: 'invalid request' });
    return;
  }

  const parsedUrl = new URL(request.url, `http://${request.headers.host || 'localhost'}`);

  if (request.method === 'GET' && parsedUrl.pathname === '/health') {
    writeJson(response, 200, {
      service: 'pressure-vessels-backend',
      status: 'ok',
    });
    return;
  }

  if (request.method === 'POST' && parsedUrl.pathname === '/api/v1/design-runs') {
    try {
      const payload = await parseJsonBody(request);

      if (!isValidDesignRunRequest(payload)) {
        writeJson(response, 400, {
          error:
            'designPressureBar, designTemperatureC, volumeM3, and code are required in the request body',
        });
        return;
      }

      const runId = toRunId(payload);
      writeJson(response, 201, {
        apiVersion: 'v1',
        runId,
        statusUrl: `/api/v1/design-runs/${runId}`,
      });
      return;
    } catch {
      writeJson(response, 400, { error: 'request body must be valid JSON' });
      return;
    }
  }

  if (request.method === 'GET' && parsedUrl.pathname.startsWith('/api/v1/design-runs/')) {
    const runId = parsedUrl.pathname.split('/').at(-1) || '';
    const resolvedPayload = parseRunId(runId);

    if (!resolvedPayload) {
      writeJson(response, 404, { error: 'design run not found' });
      return;
    }

    writeJson(response, 200, {
      runId,
      workflowState: 'completed',
      complianceSummary: {
        status: 'pass',
        code: normalizeCode(resolvedPayload.code),
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
    });
    return;
  }

  writeJson(response, 404, { error: 'route not found' });
});

server.listen(port, host, () => {
  // eslint-disable-next-line no-console
  console.log(`pressure-vessels backend local integration server listening on http://${host}:${port}`);
});
