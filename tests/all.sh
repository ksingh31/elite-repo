#!/usr/bin/env bash
# Feature suites + standalone smoke (run.sh covers the regression set)
cd "$(dirname "$0")/.." && python3 tests/run_all.py features && exec python3 tests/run_all.py smoke
