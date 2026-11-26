# Common tasks. Needs: node >= 20, python3, Playwright for Python (pip install playwright && playwright install chromium)
.PHONY: help build serve test test-api test-ui lint scan export plan deploy outputs drift events teardown

# AWS environment = section of infra/aws/samconfig.toml (dev | prod)
ENV ?= dev
export ENV

help:
	@echo "make build      regenerate app/standalone from app/artifact/index.html"
	@echo "make serve      local server (standalone build + local API, fake Google) on http://localhost:8787"
	@echo "make test       API unit tests + every Playwright suite"
	@echo "make lint       cfn-lint the AWS template (+ sam validate --lint if installed), check the store schema"
	@echo "make scan       look for secrets / real ids before pushing"
	@echo "make export LIVE=/path/live.html   re-export a newly published artifact into the repo (needs config/private.json)"
	@echo "make plan     ENV=prod   preview the CloudFormation change set (nothing changes)"
	@echo "make deploy   ENV=prod   preview, confirm, apply, upload the app (YES=1 skips the question)"
	@echo "make outputs  ENV=prod   stack status + outputs (app URL, buckets, user pool)"
	@echo "make drift    ENV=prod   list resources changed outside CloudFormation"
	@echo "make events   ENV=prod   last stack events (why a deploy failed / rolled back)"
	@echo "make teardown ENV=prod   delete the stack (data bucket kept unless DELETE_DATA=yes)"

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
	@if command -v sam >/dev/null; then SAM_CLI_TELEMETRY=0 sam validate --lint -t infra/aws/template.yaml --region ca-central-1; else echo "sam CLI not installed: skipped sam validate (pip install aws-sam-cli)"; fi
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

plan:
	./infra/aws/deploy.sh --plan

deploy:
	./infra/aws/deploy.sh

outputs:
	./infra/aws/ops.sh outputs

drift:
	./infra/aws/ops.sh drift

events:
	./infra/aws/ops.sh events

teardown:
	./infra/aws/teardown.sh
