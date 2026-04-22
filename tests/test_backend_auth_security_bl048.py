from __future__ import annotations

from pathlib import Path


def test_backend_auth_uses_provider_backed_jwt_verification_and_claim_checks() -> None:
    main_ts = Path('services/backend/src/main.ts').read_text(encoding='utf-8')

    assert 'getRuntimeAuthProviderConfig' in main_ts
    assert "createHmac('sha256'" in main_ts
    assert 'timingSafeEqual' in main_ts
    assert "token expired or missing exp claim" in main_ts
    assert "invalid token issuer" in main_ts
    assert "invalid token audience" in main_ts
    assert "insufficient scope: requires ${requiredScope}" in main_ts


def test_backend_auth_supports_deterministic_scope_and_role_resolution() -> None:
    main_ts = Path('services/backend/src/main.ts').read_text(encoding='utf-8')

    assert 'const ALLOWED_AUTH_ROLES = [\'engineer\', \'reviewer\', \'approver\'] as const;' in main_ts
    assert 'function resolveRole' in main_ts
    assert "if (scopeClaims.includes('design_runs:write'))" in main_ts
    assert "if (scopeClaims.includes('design_runs:read'))" in main_ts


def test_backend_secrets_define_rotation_ready_provider_keyset_contract() -> None:
    secrets_ts = Path('services/backend/src/secrets.ts').read_text(encoding='utf-8')
    runbook = Path('docs/runbooks/runtime_security_hardening_checklist.md').read_text(
        encoding='utf-8'
    )

    assert 'PV_AUTH_PROVIDER_JWKS_JSON' in secrets_ts
    assert 'kid' in secrets_ts
    assert 'alg=HS256' in secrets_ts
    assert 'Normal rotation (planned)' in runbook
    assert 'Revocation (compromise)' in runbook
    assert 'Break-glass (provider outage)' in runbook
