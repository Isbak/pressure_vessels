.PHONY: bootstrap bootstrap-py bootstrap-js validate-js validate-style validate ci test governance stack integration-up integration-down integration-logs lint-py lint-js format-py format-js t g s v up down logs

PYTHON ?= python
PIP ?= pip
NPM ?= npm
VALIDATE_INFRA ?= 1
JS_VALIDATE ?= 1
NODE_VERSION_PIN_FILE ?= tools/versions.json
NODE_VERSION_PIN ?= $(shell $(PYTHON) -c "import json, pathlib; print(json.loads(pathlib.Path('$(NODE_VERSION_PIN_FILE)').read_text(encoding='utf-8'))['node'])")
INFRA_BOUNDARY_MANIFEST ?= infra/platform/infra_boundary_files.manifest
INFRA_BOUNDARY_FILES ?=

bootstrap: bootstrap-py bootstrap-js

bootstrap-py:
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -e . pytest

bootstrap-js:
	@command -v node >/dev/null 2>&1 || { echo "Node.js $(NODE_VERSION_PIN).x or newer is required for JS service bootstrap. Install a supported version using $(NODE_VERSION_PIN_FILE) as the minimum baseline, then rerun 'make bootstrap'."; exit 1; }
	@actual_node_version=$$(node -p "process.versions.node"); \
	actual_node_major=$$(node -p "process.versions.node.split('.')[0]"); \
	if [ "$$actual_node_major" -lt "$(NODE_VERSION_PIN)" ]; then \
		echo "Unsupported Node.js version $$actual_node_version detected (requires >= $(NODE_VERSION_PIN).x per $(NODE_VERSION_PIN_FILE))."; \
		exit 1; \
	fi
	@command -v $(NPM) >/dev/null 2>&1 || { echo "npm is required for JS service bootstrap. Install npm, then rerun 'make bootstrap'."; exit 1; }
	$(NPM) --prefix services/frontend ci
	$(NPM) --prefix services/backend ci

test:
	pytest -q

governance:
	PYTHONPATH=src $(PYTHON) -m pressure_vessels.dev_cli check-readme-anchors

stack:
	PYTHONPATH=src $(PYTHON) -m pressure_vessels.dev_cli check-tech-stack
	@if [ "$(VALIDATE_INFRA)" = "1" ]; then \
		if [ -n "$(INFRA_BOUNDARY_FILES)" ]; then \
			for file in $(INFRA_BOUNDARY_FILES); do \
				test -f "$$file" || { echo "Missing required infra file: $$file"; exit 1; }; \
			done; \
		else \
			test -f "$(INFRA_BOUNDARY_MANIFEST)" || { echo "Missing required infra boundary manifest: $(INFRA_BOUNDARY_MANIFEST)"; exit 1; }; \
			while IFS= read -r file || [ -n "$$file" ]; do \
				case "$$file" in \
					''|\#*) continue ;; \
				esac; \
				test -f "$$file" || { echo "Missing required infra file: $$file"; exit 1; }; \
			done < "$(INFRA_BOUNDARY_MANIFEST)"; \
		fi; \
	fi

validate-js:
	@if [ "$(JS_VALIDATE)" = "0" ]; then \
		echo "Skipping JS validation because JS_VALIDATE=0."; \
	else \
		command -v node >/dev/null 2>&1 || { echo "Node.js $(NODE_VERSION_PIN).x or newer is required for JS validation. Install a supported version using $(NODE_VERSION_PIN_FILE) as the minimum baseline, then rerun 'make validate' or set JS_VALIDATE=0 to skip locally."; exit 1; }; \
		actual_node_version=$$(node -p "process.versions.node"); \
		actual_node_major=$$(node -p "process.versions.node.split('.')[0]"); \
		if [ "$$actual_node_major" -lt "$(NODE_VERSION_PIN)" ]; then \
			echo "Unsupported Node.js version $$actual_node_version detected (requires >= $(NODE_VERSION_PIN).x per $(NODE_VERSION_PIN_FILE))."; \
			exit 1; \
		fi; \
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
