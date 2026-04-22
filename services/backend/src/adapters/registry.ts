import {
  AdapterMode,
  AdapterResult,
  DesignRunCacheAdapter,
  DesignRunStateStoreAdapter,
  PersistedDesignRunRecord,
  ServiceIntegrationAdapter,
} from './interfaces';
import { PlatformServiceAdapter } from './platform_services';
import { PostgresqlDesignRunStateStoreAdapter } from './postgresql';
import { RedisDesignRunCacheAdapter } from './redis';

export type AdapterRegistry = {
  runStateStore: DesignRunStateStoreAdapter;
  runCache: DesignRunCacheAdapter;
  platformServices: Record<'neo4j' | 'qdrant' | 'opensearch' | 'temporal' | 'llm-serving', ServiceIntegrationAdapter>;
};

export type AdapterRegistryResult = AdapterResult<AdapterRegistry>;

export function createAdapterRegistry(env: NodeJS.ProcessEnv): AdapterRegistryResult {
  const postgresUrl = env.PV_POSTGRES_URL;
  const postgresSchema = env.PV_POSTGRES_SCHEMA;
  const redisUrl = env.PV_REDIS_URL;
  const redisNamespace = env.PV_REDIS_NAMESPACE;

  if (!postgresUrl || !postgresSchema) {
    return {
      ok: false,
      error: {
        code: 'ADAPTER_CONFIG_MISSING',
        adapter: 'postgresql',
        message: 'PV_POSTGRES_URL and PV_POSTGRES_SCHEMA are required for backend design-run state',
      },
    };
  }

  if (!redisUrl || !redisNamespace) {
    return {
      ok: false,
      error: {
        code: 'ADAPTER_CONFIG_MISSING',
        adapter: 'redis',
        message: 'PV_REDIS_URL and PV_REDIS_NAMESPACE are required for backend design-run cache',
      },
    };
  }

  const neo4j = toPlatformServiceAdapter(env, 'neo4j', 'PV_NEO4J_ENDPOINT', 'PV_NEO4J_TOKEN', 'PV_NEO4J_MODE');
  if (!neo4j.ok) {
    return neo4j;
  }
  const qdrant = toPlatformServiceAdapter(env, 'qdrant', 'PV_QDRANT_ENDPOINT', 'PV_QDRANT_API_KEY', 'PV_QDRANT_MODE');
  if (!qdrant.ok) {
    return qdrant;
  }
  const opensearch = toPlatformServiceAdapter(
    env,
    'opensearch',
    'PV_OPENSEARCH_ENDPOINT',
    'PV_OPENSEARCH_API_KEY',
    'PV_OPENSEARCH_MODE',
  );
  if (!opensearch.ok) {
    return opensearch;
  }
  const temporal = toPlatformServiceAdapter(env, 'temporal', 'PV_TEMPORAL_ENDPOINT', 'PV_TEMPORAL_TOKEN', 'PV_TEMPORAL_MODE');
  if (!temporal.ok) {
    return temporal;
  }
  const llmServing = toPlatformServiceAdapter(
    env,
    'llm-serving',
    'PV_LLM_SERVING_ENDPOINT',
    'PV_LLM_SERVING_API_KEY',
    'PV_LLM_SERVING_MODE',
  );
  if (!llmServing.ok) {
    return llmServing;
  }

  const registry: AdapterRegistry = {
    runStateStore: new PostgresqlDesignRunStateStoreAdapter(postgresUrl, postgresSchema),
    runCache: new RedisDesignRunCacheAdapter(redisUrl, redisNamespace),
    platformServices: {
      neo4j: neo4j.value,
      qdrant: qdrant.value,
      opensearch: opensearch.value,
      temporal: temporal.value,
      'llm-serving': llmServing.value,
    },
  };

  const platformServiceCheck = assertPlatformServicesReady(registry.platformServices);
  if (!platformServiceCheck.ok) {
    return platformServiceCheck;
  }

  return { ok: true, value: registry };
}

function toPlatformServiceAdapter(
  env: NodeJS.ProcessEnv,
  service: 'neo4j' | 'qdrant' | 'opensearch' | 'temporal' | 'llm-serving',
  endpointVar: string,
  credentialVar: string,
  modeVar: string,
): AdapterResult<ServiceIntegrationAdapter> {
  const modeResult = parseAdapterMode(env, modeVar, service);
  if (!modeResult.ok) {
    return modeResult;
  }
  const mode = modeResult.value;

  return {
    ok: true,
    value: new PlatformServiceAdapter(service, mode, env[endpointVar], env[credentialVar]),
  };
}

function parseAdapterMode(
  env: NodeJS.ProcessEnv,
  modeVar: string,
  adapter: string,
): AdapterResult<AdapterMode> {
  const mode = env[modeVar];
  if (!mode) {
    return { ok: true, value: 'deterministic-fallback' };
  }

  if (mode === 'required' || mode === 'deterministic-fallback') {
    return { ok: true, value: mode };
  }

  return {
    ok: false,
    error: {
      code: 'ADAPTER_CONFIG_MISSING',
      adapter,
      message: `${modeVar} must be either required or deterministic-fallback`,
    },
  };
}

function assertPlatformServicesReady(
  services: Record<'neo4j' | 'qdrant' | 'opensearch' | 'temporal' | 'llm-serving', ServiceIntegrationAdapter>,
): AdapterResult<void> {
  const checks = Object.values(services).map((adapter) => adapter.assertReady()).find((result) => !result.ok);
  if (checks && !checks.ok) {
    return checks;
  }

  return { ok: true, value: undefined };
}

export function readDesignRunRecord(
  registry: AdapterRegistry,
  runId: string,
): AdapterResult<PersistedDesignRunRecord | null> {
  const cacheRecord = registry.runCache.read(runId);
  if (cacheRecord.ok && cacheRecord.value) {
    return cacheRecord;
  }

  const persisted = registry.runStateStore.read(runId);
  if (persisted.ok && persisted.value) {
    registry.runCache.write(persisted.value);
  }

  return persisted;
}
