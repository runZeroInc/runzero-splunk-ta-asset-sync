#!/bin/bash
# Builds the add-on and runs Splunk AppInspect against it in `precert` mode --
# the same mode/checks used for Splunk Cloud vetting (including the
# `future_failure` checks that predict upcoming compatibility loss).
#
# Usage: ./scripts/check.sh
# Output: report.json (in appinspect/) with full per-check detail, plus a
#         console summary of any non-passing checks.
#
# See README.md "Running Splunk Cloud vetting (AppInspect) checks locally"
# for background on why this can't be reproduced just by installing the app
# in a local Splunk Enterprise instance.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
APP_NAME="TA_runzero_asset_sync"

echo "==> Building add-on"
"$SCRIPT_DIR/build.sh"

VERSION="$(python3 -c "import json; print(json.load(open('$REPO_ROOT/ucc/package/app.manifest'))['info']['id']['version'])")"
PACKAGE="$REPO_ROOT/${APP_NAME}-${VERSION}.spl"

echo "==> Running AppInspect (precert mode) against ${APP_NAME}-${VERSION}.spl"
cd "$REPO_ROOT/appinspect"
uv run splunk-appinspect inspect "$PACKAGE" --mode precert --output-file report.json

echo "==> Non-passing checks:"
uv run python -c "
import json
d = json.load(open('report.json'))
found = False
for g in d['reports'][0]['groups']:
    for chk in g['checks']:
        if chk['result'] not in ('success', 'not_applicable'):
            found = True
            print(chk['result'], '->', chk['name'])
if not found:
    print('(none)')
"
