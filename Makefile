# Common tasks. Needs: node >= 20, python3, Playwright for Python (pip install playwright && playwright install chromium)
.PHONY: help build serve test test-api test-ui lint scan export deploy teardown

help:
	@echo "make build      regenerate app/standalone from app/artifact/index.html"
	@echo "make serve      local server (standalone build + local API, fake Google) on http://localhost:8787"
	@echo "make test       API unit tests + every Playwright suite"
	@echo "make lint       cfn-lint the AWS template, check the store schema"
	@echo "make scan       look for secrets / real ids before pushing"
	@echo "make export LIVE=/path/live.html   re-export a newly published artifact into the repo (needs config/private.json)"
	@echo "make deploy     ./infra/aws/deploy.sh (see README for the env vars)"

build:
	node app/build/build_standalone.mjs

serve: build
	node api/local-server.mjs

test: test-api test-ui

test-api:
	cd api && npm test

test-ui:
	python3 tests/run_all.py

lint:
	cfn-lint infra/aws/template.yaml
	python3 -c "import json,jsonschema;s=json.load(open('schemas/store.schema.json'));jsonschema.Draft202012Validator.check_schema(s);jsonschema.validate(json.load(open('samples/store.sample.json')),s);print('schema ok')"

scan:
	python3 tools/scan_public.py

# LIVE = the exact HTML of the published artifact. Keeps the sample store; swaps real ids for placeholders.
export:
	@test -n "$(LIVE)" || (echo "usage: make export LIVE=/path/to/live.html" && exit 1)
	@test -f config/private.json || (echo "config/private.json is needed (see config/private.example.json)" && exit 1)
	python3 tools/store_tool.py publicize "$(LIVE)" config/private.json /tmp/elite-public.html
	python3 tools/store_tool.py inject /tmp/elite-public.html samples/store.sample.json app/artifact/index.html
	node app/build/build_standalone.mjs
	python3 tools/scan_public.py

deploy:
	./infra/aws/deploy.sh

teardown:
	./infra/aws/teardown.sh
