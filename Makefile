# Music Ontology — task runner (thin wrapper over uv).
# Usage: make <target>.  `make check` runs the full validation gate.

.PHONY: help install validate test shacl check clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

install: ## Sync the locked Python environment
	uv sync

validate: ## Parse + SPARQL model checks (genre traversal, place roll-up, etc.)
	uv run python scripts/validate_fixes.py

test: ## CQ regression suite (one SPARQL test per competency question)
	uv run python scripts/run_cq_tests.py

shacl: ## SHACL conformance gate (fails only on Violations; Warnings advisory)
	uv run python scripts/check_shacl.py

check: validate test shacl ## Run the full validation gate

clean: ## Remove the virtual environment
	rm -rf .venv
