.PHONY: bootstrap validate ci test governance stack t g s v

PYTHON ?= python
PIP ?= pip
VALIDATE_INFRA ?= 1

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

bootstrap:
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -e . pytest

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

validate: test governance stack

ci: validate

t: test

g: governance

s: stack

v: validate
