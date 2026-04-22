web: cd services/frontend && npm ci && npm run build && npm run start -- --hostname 0.0.0.0 --port ${PORT:-3000}
backend: cd services/backend && npm ci && BACKEND_HOST=0.0.0.0 BACKEND_PORT=${BACKEND_PORT:-8000} node local-integration-server.js
