.PHONY: generate sync-specs install dev test clean

VENV := .venv
PYTHON := $(VENV)/bin/python
COMPUTE_REPO := $(HOME)/compute
REGISTRY_REPO := $(HOME)/agent-registry

# Generate SDK from specs
generate:
	$(PYTHON) generator/generate.py

# Sync specs from product repos then generate
sync-specs:
	@echo "→ Syncing compute spec..."
	cd $(COMPUTE_REPO)/compute-controller && make swagger
	cp $(COMPUTE_REPO)/specs/json/compute-api.json specs/
	@echo "→ Syncing agentd spec..."
	cp $(COMPUTE_REPO)/specs/json/agentd-api.json specs/
	@echo "→ Syncing registry spec..."
	cp $(REGISTRY_REPO)/specs/json/agent-registry-api.json specs/
	@echo "✓ Specs synced"
	$(MAKE) generate

# Setup venv and install deps
install:
	uv venv
	$(VENV)/bin/pip install -e ".[dev]"

# Install dev deps (jinja2 for generator)
dev:
	$(VENV)/bin/pip install jinja2

# Run tests
test:
	$(PYTHON) -m pytest tests/ -v

# Verify imports work
check:
	$(PYTHON) -c "from hexel import Hexel; print('✅ hexel', __import__('hexel').__version__)"

# Clean generated files
clean:
	rm -rf hexel/compute/_*.py hexel/compute/types.py hexel/compute/__init__.py
	rm -f generator/ir.json

# Full rebuild: sync specs + generate + check
all: sync-specs check
