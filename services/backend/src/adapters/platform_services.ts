import { AdapterMode, AdapterResult, ServiceIntegrationAdapter } from './interfaces';

type PlatformService = 'neo4j' | 'qdrant' | 'opensearch' | 'temporal' | 'llm-serving';

export class PlatformServiceAdapter implements ServiceIntegrationAdapter {
  constructor(
    readonly service: PlatformService,
    readonly mode: AdapterMode,
    private readonly endpoint: string | undefined,
    private readonly credential: string | undefined,
  ) {}

  assertReady(): AdapterResult<'ready' | 'deterministic-fallback'> {
    if (this.endpoint && this.credential) {
      return { ok: true, value: 'ready' };
    }

    if (this.mode === 'deterministic-fallback') {
      return { ok: true, value: 'deterministic-fallback' };
    }

    return {
      ok: false,
      error: {
        code: 'ADAPTER_CONFIG_MISSING',
        adapter: this.service,
        message: `${this.service} adapter requires endpoint and credential in required mode`,
      },
    };
  }
}
