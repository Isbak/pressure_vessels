import Link from 'next/link';
import { headers } from 'next/headers';

import type { PromptResponse } from '../../lib/prompt-contract';

type ResultPageProps = {
  searchParams: {
    prompt?: string;
  };
};

async function getPromptResult(prompt: string): Promise<PromptResponse> {
  const headerStore = headers();
  const host = headerStore.get('host');

  if (!host) {
    throw new Error('Host header missing.');
  }

  const protocol =
    headerStore.get('x-forwarded-proto') ??
    (host.includes('localhost') ? 'http' : 'https');

  const endpoint = new URL('/api/prompt', `${protocol}://${host}`);
  endpoint.searchParams.set('prompt', prompt);

  const response = await fetch(endpoint, { cache: 'no-store' });

  if (!response.ok) {
    throw new Error('Prompt request failed.');
  }

  return (await response.json()) as PromptResponse;
}

export default async function ResultPage({
  searchParams,
}: ResultPageProps): Promise<JSX.Element> {
  const prompt = (searchParams.prompt ?? '').trim();

  if (!prompt) {
    return (
      <main>
        <h1>Prompt Result</h1>
        <p>No prompt provided. Return to the home page and submit a prompt.</p>
        <Link href="/">Back to prompt form</Link>
      </main>
    );
  }

  try {
    const payload = await getPromptResult(prompt);

    return (
      <main>
        <h1>Prompt Result</h1>
        <p>
          <strong>Prompt:</strong> {payload.prompt}
        </p>
        <p>
          <strong>Backend response:</strong> {payload.response}
        </p>
        <p>
          <strong>Response source:</strong> {payload.source}
        </p>
        <Link href="/">Run another prompt</Link>
      </main>
    );
  } catch {
    return (
      <main>
        <h1>Prompt Result</h1>
        <p>Could not load backend response for the submitted prompt.</p>
        <Link href="/">Run another prompt</Link>
      </main>
    );
  }
}
