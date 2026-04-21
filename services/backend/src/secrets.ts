export const APPROVED_SECRETS_MODULE_PATH =
  'infra/platform/secrets/module.boundaries.yaml';

function resolveRequiredEnvVar(name: string): string {
  const value = process.env[name];
  if (!value || value.trim().length === 0) {
    throw new Error(
      `BL-038 security baseline failed: required secret '${name}' must be provided via ${APPROVED_SECRETS_MODULE_PATH}.`,
    );
  }
  return value.trim();
}

export function getRuntimeAuthSecret(): string {
  return resolveRequiredEnvVar('PV_BACKEND_AUTH_TOKEN_SECRET');
}
