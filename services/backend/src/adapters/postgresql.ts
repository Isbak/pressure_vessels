import { execFileSync } from 'node:child_process';

import { AdapterResult, DesignRunStateStoreAdapter, PersistedDesignRunRecord } from './interfaces';

const DESIGN_RUN_TABLE = 'backend_design_runs_v1';

function resolveSchema(schema: string): AdapterResult<string> {
  if (/^[a-z_][a-z0-9_]*$/i.test(schema)) {
    return { ok: true, value: schema };
  }

  return {
    ok: false,
    error: {
      code: 'ADAPTER_CONFIG_MISSING',
      adapter: 'postgresql',
      message: 'PV_POSTGRES_SCHEMA must be a valid SQL identifier',
    },
  };
}

function toCliAdapterUnavailableError(message: string): AdapterResult<never> {
  return {
    ok: false,
    error: {
      code: 'ADAPTER_UNAVAILABLE',
      adapter: 'postgresql',
      message,
    },
  };
}

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

    const schemaResult = resolveSchema(this.schema);
    if (!schemaResult.ok) {
      return schemaResult;
    }

    const payloadJson = JSON.stringify(record).replace(/'/g, "''");
    const sql = [
      `CREATE SCHEMA IF NOT EXISTS ${schemaResult.value};`,
      `CREATE TABLE IF NOT EXISTS ${schemaResult.value}.${DESIGN_RUN_TABLE} (run_id text PRIMARY KEY, payload jsonb NOT NULL);`,
      `INSERT INTO ${schemaResult.value}.${DESIGN_RUN_TABLE} (run_id, payload) VALUES ('${record.runId}', '${payloadJson}'::jsonb)`,
      'ON CONFLICT (run_id) DO UPDATE SET payload = EXCLUDED.payload;',
    ].join(' ');

    try {
      execFileSync('psql', [this.connectionUrl, '-v', 'ON_ERROR_STOP=1', '-q', '-c', sql], {
        stdio: 'pipe',
      });
      return { ok: true, value: record };
    } catch (error) {
      return toCliAdapterUnavailableError(`PostgreSQL write failed: ${String(error)}`);
    }
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

    const schemaResult = resolveSchema(this.schema);
    if (!schemaResult.ok) {
      return schemaResult;
    }

    const sql = [
      `SELECT payload::text FROM ${schemaResult.value}.${DESIGN_RUN_TABLE}`,
      `WHERE run_id = '${runId.replace(/'/g, "''")}';`,
    ].join(' ');

    try {
      const output = execFileSync('psql', [this.connectionUrl, '-t', '-A', '-q', '-c', sql], {
        encoding: 'utf-8',
        stdio: ['ignore', 'pipe', 'pipe'],
      }).trim();

      if (!output) {
        return { ok: true, value: null };
      }

      return { ok: true, value: JSON.parse(output) as PersistedDesignRunRecord };
    } catch (error) {
      return toCliAdapterUnavailableError(`PostgreSQL read failed: ${String(error)}`);
    }
  }
}
