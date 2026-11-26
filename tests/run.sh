#!/usr/bin/env bash
# Regression suite (repo-relative; tests the app in app/artifact/index.html unless APP_HTML is set)
cd "$(dirname "$0")/.." && exec python3 tests/run_all.py regression
