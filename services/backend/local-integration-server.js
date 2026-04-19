const http = require('node:http');
const { URL } = require('node:url');

const host = process.env.BACKEND_HOST || '0.0.0.0';
const port = Number(process.env.BACKEND_PORT || '8000');

function normalizePrompt(prompt) {
  return prompt.trim().replace(/\s+/g, ' ');
}

function writeJson(response, statusCode, body) {
  response.writeHead(statusCode, { 'Content-Type': 'application/json' });
  response.end(JSON.stringify(body));
}

const server = http.createServer((request, response) => {
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

  if (request.method === 'GET' && parsedUrl.pathname === '/api/prompt') {
    const normalizedPrompt = normalizePrompt(parsedUrl.searchParams.get('prompt') || '');

    if (!normalizedPrompt) {
      writeJson(response, 400, { error: 'prompt query parameter is required' });
      return;
    }

    writeJson(response, 200, {
      prompt: normalizedPrompt,
      response: `Deterministic pipeline response: ${normalizedPrompt}`,
      route: 'deterministic-pipeline-v1',
    });
    return;
  }

  writeJson(response, 404, { error: 'route not found' });
});

server.listen(port, host, () => {
  // eslint-disable-next-line no-console
  console.log(`pressure-vessels backend local integration server listening on http://${host}:${port}`);
});
