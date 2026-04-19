import { NextRequest, NextResponse } from 'next/server';

import type { PromptResponse } from '../../../lib/prompt-contract';

const BACKEND_API_BASE_URL = process.env.BACKEND_API_BASE_URL;

function buildFallbackResponse(prompt: string): PromptResponse {
  return {
    prompt,
    response: `Backend placeholder processed prompt: ${prompt}`,
    source: 'frontend-placeholder',
  };
}

export async function GET(request: NextRequest): Promise<NextResponse> {
  const prompt = request.nextUrl.searchParams.get('prompt')?.trim() ?? '';

  if (!prompt) {
    return NextResponse.json(
      { error: 'prompt query parameter is required' },
      { status: 400 },
    );
  }

  if (!BACKEND_API_BASE_URL) {
    return NextResponse.json(buildFallbackResponse(prompt));
  }

  const endpoint = new URL('/api/prompt', BACKEND_API_BASE_URL);
  endpoint.searchParams.set('prompt', prompt);

  try {
    const backendResponse = await fetch(endpoint, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
      cache: 'no-store',
    });

    if (!backendResponse.ok) {
      return NextResponse.json(buildFallbackResponse(prompt), { status: 200 });
    }

    const payload = (await backendResponse.json()) as {
      prompt?: string;
      response?: string;
    };

    if (!payload.prompt || !payload.response) {
      return NextResponse.json(buildFallbackResponse(prompt), { status: 200 });
    }

    return NextResponse.json({
      prompt: payload.prompt,
      response: payload.response,
      source: 'backend-service',
    } satisfies PromptResponse);
  } catch {
    return NextResponse.json(buildFallbackResponse(prompt), { status: 200 });
  }
}
