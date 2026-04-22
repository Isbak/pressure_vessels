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

  const registry: AdapterRegistry = {
    runStateStore: new PostgresqlDesignRunStateStoreAdapter(postgresUrl, postgresSchema),
    runCache: new RedisDesignRunCacheAdapter(redisUrl, redisNamespace),
    platformServices: {
      neo4j: toPlatformServiceAdapter(env, 'neo4j', 'PV_NEO4J_ENDPOINT', 'PV_NEO4J_TOKEN', 'PV_NEO4J_MODE'),
      qdrant: toPlatformServiceAdapter(env, 'qdrant', 'PV_QDRANT_ENDPOINT', 'PV_QDRANT_API_KEY', 'PV_QDRANT_MODE'),
      opensearch: toPlatformServiceAdapter(
        env,
        'opensearch',
        'PV_OPENSEARCH_ENDPOINT',
        'PV_OPENSEARCH_API_KEY',
        'PV_OPENSEARCH_MODE',
      ),
      temporal: toPlatformServiceAdapter(
        env,
        'temporal',
        'PV_TEMPORAL_ENDPOINT',
        'PV_TEMPORAL_TOKEN',
        'PV_TEMPORAL_MODE',
      ),
      'llm-serving': toPlatformServiceAdapter(
        env,
        'llm-serving',
        'PV_LLM_SERVING_ENDPOINT',
        'PV_LLM_SERVING_API_KEY',
        'PV_LLM_SERVING_MODE',
      ),
    },
  };

  return { ok: true, value: registry };
}

function toPlatformServiceAdapter(
  env: NodeJS.ProcessEnv,
  service: 'neo4j' | 'qdrant' | 'opensearch' | 'temporal' | 'llm-serving',
  endpointVar: string,
  credentialVar: string,
  modeVar: string,
): ServiceIntegrationAdapter {
  const mode = ((env[modeVar] as AdapterMode | undefined) ?? 'deterministic-fallback') as AdapterMode;

  return new PlatformServiceAdapter(service, mode, env[endpointVar], env[credentialVar]);
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
