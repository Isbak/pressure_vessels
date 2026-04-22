export type AdapterMode = 'required' | 'deterministic-fallback';

export type AdapterResult<T> =
  | { ok: true; value: T }
  | { ok: false; error: AdapterError };

export type AdapterErrorCode =
  | 'ADAPTER_CONFIG_MISSING'
  | 'ADAPTER_UNAVAILABLE'
  | 'ADAPTER_NOT_FOUND';

export type AdapterError = {
  code: AdapterErrorCode;
  adapter: string;
  message: string;
};

export type DesignRunArtifact = {
  artifactId: string;
  artifactType: 'WorkflowExecutionReport.v1' | 'ComplianceDossierMachine.v1';
  location: string;
};

export type PersistedDesignRunRecord = {
  runId: string;
  workflowState: 'completed';
  complianceSummary: {
    status: 'pass';
    code: string;
    checksPassed: number;
    checksFailed: number;
  };
  artifacts: DesignRunArtifact[];
};

export interface DesignRunStateStoreAdapter {
  readonly name: 'postgresql';
  persist(record: PersistedDesignRunRecord): AdapterResult<PersistedDesignRunRecord>;
  read(runId: string): AdapterResult<PersistedDesignRunRecord | null>;
}

export interface DesignRunCacheAdapter {
  readonly name: 'redis';
  write(record: PersistedDesignRunRecord): AdapterResult<void>;
  read(runId: string): AdapterResult<PersistedDesignRunRecord | null>;
}

export interface ServiceIntegrationAdapter {
  readonly service: 'neo4j' | 'qdrant' | 'opensearch' | 'temporal' | 'llm-serving';
  readonly mode: AdapterMode;
  assertReady(): AdapterResult<'ready' | 'deterministic-fallback'>;
}
