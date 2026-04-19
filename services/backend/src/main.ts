export type BackendResponse<T> = {
  status: number;
  body: T;
};

export type HealthResponse = {
  service: 'pressure-vessels-backend';
  status: 'ok';
};

export type PromptRouteResponse = {
  prompt: string;
  response: string;
  route: 'deterministic-pipeline-v1';
};

export type ErrorResponse = {
  error: string;
};

function normalizePrompt(prompt: string): string {
  return prompt.trim().replace(/\s+/g, ' ');
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

export function runDeterministicPromptPipeline(
  prompt: string,
): BackendResponse<PromptRouteResponse | ErrorResponse> {
  const normalizedPrompt = normalizePrompt(prompt);

  if (!normalizedPrompt) {
    return {
      status: 400,
      body: {
        error: 'prompt query parameter is required',
      },
    };
  }

  return {
    status: 200,
    body: {
      prompt: normalizedPrompt,
      response: `Deterministic pipeline response: ${normalizedPrompt}`,
      route: 'deterministic-pipeline-v1',
    },
  };
}

export function bootstrap(): string {
  return 'pressure-vessels backend API initialized';
}
