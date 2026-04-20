.PHONY: bootstrap bootstrap-py bootstrap-js validate-js validate-style validate ci test governance stack integration-up integration-down integration-logs lint-py lint-js format-py format-js t g s v up down logs

PYTHON ?= python
PIP ?= pip
NPM ?= npm
VALIDATE_INFRA ?= 1
JS_VALIDATE ?= 1

INFRA_BOUNDARY_FILES ?= \
	infra/platform/environment.bootstrap.yaml \
	infra/platform/iac/module.primitives.yaml \
	infra/platform/secrets/module.boundaries.yaml \
	infra/platform/observability/module.boundaries.yaml \
	infra/platform/postgresql/module.boundaries.yaml \
	infra/platform/redis/module.boundaries.yaml \
	infra/platform/runtime/module.boundaries.yaml \
	infra/platform/keycloak/module.boundaries.yaml \
	infra/platform/temporal/module.boundaries.yaml \
	infra/platform/neo4j/module.boundaries.yaml \
	infra/platform/qdrant/module.boundaries.yaml \
	infra/platform/opensearch/module.boundaries.yaml \
	infra/platform/vllm/module.boundaries.yaml \
	infra/platform/model-catalog/module.boundaries.yaml

bootstrap: bootstrap-py bootstrap-js

bootstrap-py:
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -e . pytest

bootstrap-js:
	@command -v node >/dev/null 2>&1 || { echo "Node.js is required for JS service bootstrap. Install Node.js (npm included), then rerun 'make bootstrap'."; exit 1; }
	@command -v $(NPM) >/dev/null 2>&1 || { echo "npm is required for JS service bootstrap. Install npm, then rerun 'make bootstrap'."; exit 1; }
	$(NPM) --prefix services/frontend ci
	$(NPM) --prefix services/backend ci

test:
	pytest -q

governance:
	$(PYTHON) scripts/check_readme_anchors.py

stack:
	$(PYTHON) scripts/check_tech_stack.py
	@if [ "$(VALIDATE_INFRA)" = "1" ]; then \
		for file in $(INFRA_BOUNDARY_FILES); do \
			test -f "$$file" || { echo "Missing required infra file: $$file"; exit 1; }; \
		done; \
	fi

validate-js:
	@if [ "$(JS_VALIDATE)" = "0" ]; then \
		echo "Skipping JS validation because JS_VALIDATE=0."; \
	else \
		command -v node >/dev/null 2>&1 || { echo "Node.js is required for JS validation. Install Node.js (npm included), then rerun 'make validate' or set JS_VALIDATE=0 to skip locally."; exit 1; }; \
		command -v $(NPM) >/dev/null 2>&1 || { echo "npm is required for JS validation. Install npm, then rerun 'make validate' or set JS_VALIDATE=0 to skip locally."; exit 1; }; \
		$(NPM) --prefix services/frontend run smoke; \
		$(NPM) --prefix services/backend run smoke; \
	fi

lint-py:
	$(PYTHON) scripts/check_python_style.py

format-py:
	@echo "No standalone Python formatter is wired yet; use your editor .editorconfig integration."

lint-js:
	$(PYTHON) scripts/check_js_ts_style.py

format-js:
	@echo "No standalone JS/TS formatter is wired yet; use your editor .editorconfig integration."

validate-style: lint-py lint-js

validate: test governance stack validate-js validate-style

ci: validate

integration-up:
	docker compose -f infra/local/docker-compose.integration.yml up

integration-down:
	docker compose -f infra/local/docker-compose.integration.yml down

integration-logs:
	docker compose -f infra/local/docker-compose.integration.yml logs -f

t: test

g: governance

s: stack

v: validate

up: integration-up

down: integration-down

logs: integration-logs
