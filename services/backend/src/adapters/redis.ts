import { AdapterResult, DesignRunCacheAdapter, PersistedDesignRunRecord } from './interfaces';

const cache = new Map<string, PersistedDesignRunRecord>();

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

    cache.set(record.runId, record);
    return { ok: true, value: undefined };
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

    return { ok: true, value: cache.get(runId) ?? null };
  }
}
