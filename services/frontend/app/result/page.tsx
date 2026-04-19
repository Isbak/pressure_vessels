'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';

type PromptApiResponse = {
  prompt: string;
  response: string;
};

export default function ResultPage(): JSX.Element {
  const searchParams = useSearchParams();
  const prompt = (searchParams.get('prompt') ?? '').trim();

  const [payload, setPayload] = useState<PromptApiResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!prompt) {
      return;
    }

    const params = new URLSearchParams({ prompt });

    fetch(`/api/prompt?${params.toString()}`)
      .then(async (result) => {
        if (!result.ok) {
          throw new Error('Prompt request failed.');
        }

        return (await result.json()) as PromptApiResponse;
      })
      .then((json) => {
        setPayload(json);
      })
      .catch(() => {
        setError('Could not load backend response for the submitted prompt.');
      });
  }, [prompt]);

  if (!prompt) {
    return (
      <main>
        <h1>Prompt Result</h1>
        <p>No prompt provided. Return to the home page and submit a prompt.</p>
        <Link href="/">Back to prompt form</Link>
      </main>
    );
  }

  return (
    <main>
      <h1>Prompt Result</h1>
      <p>
        <strong>Prompt:</strong> {prompt}
      </p>
      {error && <p>{error}</p>}
      {!error && !payload && <p>Loading backend response...</p>}
      {payload && (
        <p>
          <strong>Backend response:</strong> {payload.response}
        </p>
      )}
      <Link href="/">Run another prompt</Link>
    </main>
  );
}
