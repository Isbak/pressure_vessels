import { AdapterResult, DesignRunStateStoreAdapter, PersistedDesignRunRecord } from './interfaces';

const records = new Map<string, PersistedDesignRunRecord>();

export class PostgresqlDesignRunStateStoreAdapter implements DesignRunStateStoreAdapter {
  readonly name = 'postgresql' as const;

  constructor(private readonly connectionUrl: string, private readonly schema: string) {}

  persist(record: PersistedDesignRunRecord): AdapterResult<PersistedDesignRunRecord> {
    if (!this.connectionUrl || !this.schema) {
      return {
        ok: false,
        error: {
          code: 'ADAPTER_UNAVAILABLE',
          adapter: this.name,
          message: 'PostgreSQL adapter is not configured for writes',
        },
      };
    }

    records.set(record.runId, record);
    return { ok: true, value: record };
  }

  read(runId: string): AdapterResult<PersistedDesignRunRecord | null> {
    if (!this.connectionUrl || !this.schema) {
      return {
        ok: false,
        error: {
          code: 'ADAPTER_UNAVAILABLE',
          adapter: this.name,
          message: 'PostgreSQL adapter is not configured for reads',
        },
      };
    }

    return { ok: true, value: records.get(runId) ?? null };
  }
}
