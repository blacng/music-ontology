# Music Ontology — task runner (thin wrapper over uv).
# Usage: make <target>.  `make check` runs the full validation gate.

.PHONY: help install validate test shacl shacl-negative coverage check dataset demo-updates viz reason reason-negative serve fuseki-load down clean

# Fuseki endpoint knobs (override on the CLI, e.g. `make fuseki-load FUSEKI_PW=secret`)
FUSEKI_URL ?= http://localhost:3030
FUSEKI_DS  ?= music
FUSEKI_PW  ?= admin

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-13s %s\n", $$1, $$2}'

install: ## Sync the locked Python environment
	uv sync

validate: ## Parse + SPARQL model checks (genre traversal, place roll-up, etc.)
	uv run python scripts/validate_fixes.py

test: ## CQ regression suite (one SPARQL test per competency question)
	uv run python scripts/run_cq_tests.py

shacl: ## SHACL conformance gate (fails only on Violations; Warnings advisory)
	uv run python scripts/check_shacl.py

shacl-negative: ## Non-vacuity gate — prove each shape can actually FAIL (tests/negative/)
	uv run python scripts/check_shacl_negative.py

coverage: ## ABox coverage report — can the real catalogue answer each CQ? (advisory, never fails)
	uv run python scripts/cq_coverage.py

reason: ## Reasoner consistency check (HermiT via ROBOT; docker compose service `reasoner`)
	docker compose run --rm reasoner
	@rm -f .robot_reasoned.ttl
	@echo "OK — ontology is consistent, no unsatisfiable classes (TBox+ABox merged, gist v14.1.0 imported locally)."

reason-negative: ## Non-vacuity gate for the REASONER — prove HermiT can actually report inconsistency
	@# Until v3.0.0 the domain TBox had ZERO owl:disjointWith axioms, so HermiT had nothing to
	@# contradict and `make reason` could not fail on any input — a green light wired to nothing.
	@# This merges a deliberately inconsistent fixture and REQUIRES a non-zero exit.
	@if docker compose run --rm reasoner merge --catalog ontology/catalog-v001.xml \
		--input ontology/music_vocabulary_comprehensive.ttl \
		--input ontology/music_catalog_data.ttl \
		--input tests/negative/reasoner_inconsistent.ttl \
		reason --reasoner hermit --output /work/.robot_neg.ttl >/dev/null 2>&1; then \
		rm -f .robot_neg.ttl; \
		echo "FAIL — HermiT accepted a group that is also a person. The disjointness axioms are"; \
		echo "       gone, and `make reason` is certifying nothing. See tests/negative/reasoner_inconsistent.ttl."; \
		exit 1; \
	else \
		rm -f .robot_neg.ttl; \
		echo "OK — HermiT rejects the inconsistent fixture. The reasoner gate is not vacuous."; \
	fi

dataset: ## Assemble the named-graph dataset for triplestore ingest (dist/*.trig, load.ru, manifest)
	uv run python scripts/load_graphs.py

demo-updates: ## SPARQL write path — INSERT/DELETE against named graphs + a SHACL-rejected write
	uv run python scripts/demo_updates.py

report: ## Regenerate docs/mc2-graph-queries.md from a real run (writes a tracked file)
	uv run python scripts/demo_updates.py --report

viz: ## Render CQ answer subgraphs to dist/viz/*.svg (+ .mmd, .dot). Artifact, not a gate.
	uv run python scripts/viz_subgraph.py

serve: ## Start the Fuseki SPARQL server (http://localhost:3030, dataset `music`)
	FUSEKI_ADMIN_PASSWORD=$(FUSEKI_PW) docker compose up -d fuseki
	@echo "Fuseki starting at $(FUSEKI_URL) (UI: $(FUSEKI_URL)/#/dataset/$(FUSEKI_DS)/query). Load data with: make fuseki-load"

fuseki-load: dataset serve ## Build the dataset and (re)load it into Fuseki's named graphs
	@echo "Waiting for the $(FUSEKI_DS) dataset endpoint to come up..."
	@for i in $$(seq 1 60); do \
		curl -fsS "$(FUSEKI_URL)/$(FUSEKI_DS)/query" \
			--data-urlencode 'query=ASK{}' >/dev/null 2>&1 && break || sleep 1; \
	done
	@# Auth for the write endpoints is fed via `curl -K -` from a printf builtin, so the
	@# password is never in the process argv (visible to `ps`); FUSEKI_PW is the one knob
	@# (serve propagates it to the server, above).
	@echo "Clearing dataset $(FUSEKI_DS)..."
	@printf 'user = "admin:%s"\n' '$(FUSEKI_PW)' | curl -fsS -K - -X POST "$(FUSEKI_URL)/$(FUSEKI_DS)/update" \
		--data-urlencode 'update=DROP ALL' >/dev/null
	@echo "Loading dist/music_dataset.trig (4 named graphs)..."
	@printf 'user = "admin:%s"\n' '$(FUSEKI_PW)' | curl -fsS -K - -X POST "$(FUSEKI_URL)/$(FUSEKI_DS)/data" \
		-H 'Content-Type: application/trig' --data-binary @dist/music_dataset.trig >/dev/null
	@echo "Loaded. Query the graphs at $(FUSEKI_URL)/#/dataset/$(FUSEKI_DS)/query"

down: ## Stop the Fuseki server (keeps the TDB volume; use `docker compose down -v` to wipe)
	docker compose down

check: validate test shacl shacl-negative demo-updates ## Run the full validation gate (CI; reasoner is separate, needs Docker)

clean: ## Remove the virtual environment
	rm -rf .venv
