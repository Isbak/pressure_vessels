import { execFileSync } from 'node:child_process';

import { AdapterResult, DesignRunCacheAdapter, PersistedDesignRunRecord } from './interfaces';

function toKey(namespace: string, runId: string): string {
  return `${namespace}:${runId}`;
}

function toRedisUnavailable(message: string): AdapterResult<never> {
  return {
    ok: false,
    error: {
      code: 'ADAPTER_UNAVAILABLE',
      adapter: 'redis',
      message,
    },
  };
}

export class RedisDesignRunCacheAdapter implements DesignRunCacheAdapter {
  readonly name = 'redis' as const;

  constructor(private readonly redisUrl: string, private readonly namespace: string) {}

  write(record: PersistedDesignRunRecord): AdapterResult<void> {
    if (!this.redisUrl || !this.namespace) {
      return {
        ok: false,
        error: {
          code: 'ADAPTER_UNAVAILABLE',
          adapter: this.name,
          message: 'Redis adapter is not configured for writes',
        },
      };
    }

    try {
      execFileSync(
        'redis-cli',
        ['-u', this.redisUrl, 'SET', toKey(this.namespace, record.runId), JSON.stringify(record)],
        { stdio: 'pipe' },
      );
      return { ok: true, value: undefined };
    } catch (error) {
      return toRedisUnavailable(`Redis write failed: ${String(error)}`);
    }
  }

  read(runId: string): AdapterResult<PersistedDesignRunRecord | null> {
    if (!this.redisUrl || !this.namespace) {
      return {
        ok: false,
        error: {
          code: 'ADAPTER_UNAVAILABLE',
          adapter: this.name,
          message: 'Redis adapter is not configured for reads',
        },
      };
    }

    try {
      const output = execFileSync('redis-cli', ['-u', this.redisUrl, 'GET', toKey(this.namespace, runId)], {
        encoding: 'utf-8',
        stdio: ['ignore', 'pipe', 'pipe'],
      }).trim();

      if (!output) {
        return { ok: true, value: null };
      }

      return { ok: true, value: JSON.parse(output) as PersistedDesignRunRecord };
    } catch (error) {
      return toRedisUnavailable(`Redis read failed: ${String(error)}`);
    }
  }
}
