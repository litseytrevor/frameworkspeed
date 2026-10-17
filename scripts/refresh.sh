#!/usr/bin/env bash
# Monthly refresh: fetch latest data, rebuild site.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/fetch_data.py
python3 scripts/build_site.py
