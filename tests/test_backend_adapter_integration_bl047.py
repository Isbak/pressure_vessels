from __future__ import annotations

from pathlib import Path


def test_backend_main_uses_adapter_registry_for_design_run_persistence_and_reads() -> None:
    main_ts = Path('services/backend/src/main.ts').read_text(encoding='utf-8')

    assert "createAdapterRegistry(process.env)" in main_ts
    assert 'runStateStore.persist' in main_ts
    assert 'runCache.write' in main_ts
    assert 'readDesignRunRecord(adapterRegistry.value, runId)' in main_ts
    assert 'backend adapter configuration error' in main_ts


def test_backend_adapter_registry_fails_closed_without_postgres_or_redis_configuration() -> None:
    registry_ts = Path('services/backend/src/adapters/registry.ts').read_text(
        encoding='utf-8'
    )

    assert 'PV_POSTGRES_URL' in registry_ts
    assert 'PV_POSTGRES_SCHEMA' in registry_ts
    assert 'PV_REDIS_URL' in registry_ts
    assert 'PV_REDIS_NAMESPACE' in registry_ts
    assert 'ADAPTER_CONFIG_MISSING' in registry_ts
    assert 'required for backend design-run state' in registry_ts
    assert 'required for backend design-run cache' in registry_ts
    assert 'assertPlatformServicesReady(registry.platformServices)' in registry_ts


def test_platform_service_interfaces_define_required_and_deterministic_fallback_modes() -> None:
    interfaces_ts = Path('services/backend/src/adapters/interfaces.ts').read_text(
        encoding='utf-8'
    )
    platform_services_ts = Path(
        'services/backend/src/adapters/platform_services.ts'
    ).read_text(encoding='utf-8')

    assert "export type AdapterMode = 'required' | 'deterministic-fallback'" in interfaces_ts
    assert "readonly service: 'neo4j' | 'qdrant' | 'opensearch' | 'temporal' | 'llm-serving'" in interfaces_ts
    assert 'assertReady(): AdapterResult' in interfaces_ts
    assert 'if (this.mode === \"deterministic-fallback\")' not in platform_services_ts
    assert "if (this.mode === 'deterministic-fallback')" in platform_services_ts
    assert 'requires endpoint and credential in required mode' in platform_services_ts
    assert 'parseAdapterMode' in Path('services/backend/src/adapters/registry.ts').read_text(
        encoding='utf-8'
    )
    assert 'must be either required or deterministic-fallback' in Path(
        'services/backend/src/adapters/registry.ts'
    ).read_text(encoding='utf-8')


def test_backend_contract_and_environment_bootstrap_document_adapter_wiring_expectations() -> None:
    contract = Path('docs/interfaces/backend_prompt_api_contract.md').read_text(
        encoding='utf-8'
    )
    bootstrap = Path('infra/platform/environment.bootstrap.yaml').read_text(
        encoding='utf-8'
    )

    assert 'PV_POSTGRES_URL' in contract
    assert 'PV_POSTGRES_SCHEMA' in contract
    assert 'PV_REDIS_URL' in contract
    assert 'PV_REDIS_NAMESPACE' in contract
    assert 'deterministic-fallback' in contract
    assert 'PV_NEO4J_MODE' in contract
    assert 'PV_QDRANT_MODE' in contract
    assert 'PV_OPENSEARCH_MODE' in contract
    assert 'PV_TEMPORAL_MODE' in contract
    assert 'PV_LLM_SERVING_MODE' in contract
    assert 'Any other mode value fails closed during adapter registry bootstrap' in contract

    assert 'backend_adapter_env:' in bootstrap
    assert 'required:' in bootstrap
    assert 'optional:' in bootstrap
    assert 'PV_POSTGRES_URL' in bootstrap
    assert 'PV_REDIS_URL' in bootstrap
