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

reason: ## Reasoner consistency check (HermiT via containerized ROBOT, gist imported; needs Docker)
	docker run --rm -v "$$PWD":/work -w /work obolibrary/robot robot reason \
		--reasoner hermit --catalog ontology/catalog-v001.xml \
		--input ontology/music_vocabulary_comprehensive.ttl \
		--output /work/.robot_reasoned.ttl
	@rm -f .robot_reasoned.ttl
	@echo "OK — ontology is consistent, no unsatisfiable classes (gist v14.1.0 imported locally)."

check: validate test shacl ## Run the full validation gate (CI; reasoner is separate, needs Docker)

clean: ## Remove the virtual environment
	rm -rf .venv
