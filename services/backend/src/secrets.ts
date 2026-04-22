export const APPROVED_SECRETS_MODULE_PATH =
  'infra/platform/secrets/module.boundaries.yaml';

export type RuntimeAuthVerificationKey = {
  kid: string;
  algorithm: 'HS256';
  secret: string;
};

export type RuntimeAuthProviderConfig = {
  issuer: string;
  audience: string;
  keys: ReadonlyArray<RuntimeAuthVerificationKey>;
};

function resolveRequiredEnvVar(name: string): string {
  const value = process.env[name];
  if (!value || value.trim().length === 0) {
    throw new Error(
      `BL-038 security baseline failed: required secret '${name}' must be provided via ${APPROVED_SECRETS_MODULE_PATH}.`,
    );
  }
  return value.trim();
}

function decodeKeySecret(raw: string): string {
  try {
    return Buffer.from(raw, 'base64url').toString('utf8');
  } catch (_error) {
    throw new Error(
      `BL-048 auth provider configuration failed: key secret must be base64url encoded via ${APPROVED_SECRETS_MODULE_PATH}.`,
    );
  }
}

export function getRuntimeAuthProviderConfig(): RuntimeAuthProviderConfig {
  const issuer = resolveRequiredEnvVar('PV_AUTH_PROVIDER_ISSUER');
  const audience = resolveRequiredEnvVar('PV_AUTH_PROVIDER_AUDIENCE');
  const keysetRaw = resolveRequiredEnvVar('PV_AUTH_PROVIDER_JWKS_JSON');

  let keyset: unknown;
  try {
    keyset = JSON.parse(keysetRaw);
  } catch (_error) {
    throw new Error(
      `BL-048 auth provider configuration failed: PV_AUTH_PROVIDER_JWKS_JSON must be valid JSON from ${APPROVED_SECRETS_MODULE_PATH}.`,
    );
  }

  const keys = (keyset as { keys?: unknown }).keys;
  if (!Array.isArray(keys) || keys.length === 0) {
    throw new Error(
      `BL-048 auth provider configuration failed: PV_AUTH_PROVIDER_JWKS_JSON must include at least one key from ${APPROVED_SECRETS_MODULE_PATH}.`,
    );
  }

  const normalizedKeys = keys.map((entry) => {
    const key = entry as {
      kid?: unknown;
      alg?: unknown;
      k?: unknown;
    };
    if (
      typeof key.kid !== 'string' ||
      key.kid.trim().length === 0 ||
      key.alg !== 'HS256' ||
      typeof key.k !== 'string' ||
      key.k.trim().length === 0
    ) {
      throw new Error(
        `BL-048 auth provider configuration failed: each key must provide kid, alg=HS256, and k in PV_AUTH_PROVIDER_JWKS_JSON.`,
      );
    }

    return {
      kid: key.kid.trim(),
      algorithm: 'HS256' as const,
      secret: decodeKeySecret(key.k.trim()),
    };
  });

  return {
    issuer,
    audience,
    keys: normalizedKeys,
  };
}
