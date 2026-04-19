import { NextRequest, NextResponse } from 'next/server';

export function GET(request: NextRequest): NextResponse {
  const prompt = request.nextUrl.searchParams.get('prompt')?.trim() ?? '';

  if (!prompt) {
    return NextResponse.json(
      { error: 'prompt query parameter is required' },
      { status: 400 },
    );
  }

  return NextResponse.json({
    prompt,
    response: `Backend placeholder processed prompt: ${prompt}`,
  });
}
