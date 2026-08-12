#!/bin/bash
# Builds and packages TA_runzero_asset_sync using the UCC framework (ucc-gen).
#
# Usage: ./scripts/build.sh
# Output: TA_runzero_asset_sync-<version>.spl (repo root)
#
# This script always runs the full build -> patch -> package pipeline in one
# step. Do NOT run `ucc-gen build`/`ucc-gen package` manually and skip this
# script -- see the "case preservation" step below for why that would produce
# a package that silently breaks existing customers' saved account
# credentials and settings on upgrade.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
UCC_DIR="$REPO_ROOT/ucc"
cd "$UCC_DIR"

APP_NAME="TA_runzero_asset_sync"
OUTPUT_DIR="output"

echo "==> Installing/syncing build dependencies (ucc-gen) via uv"
uv sync --quiet

VENV_PYTHON="$(uv run python3 -c 'import sys; print(sys.executable)')"

# Read the version to build from package/app.manifest so it
# doesn't depend on git tag/describe state (ucc-gen otherwise falls back
# to auto-detecting a version via dunamai from the enclosing git repo).
VERSION="$(python3 -c "import json; print(json.load(open('package/app.manifest'))['info']['id']['version'])")"

echo "==> Building add-on with ucc-gen (version $VERSION)"
rm -rf "$OUTPUT_DIR"
uv run ucc-gen build \
    --source ./package \
    --config ./globalConfig.json \
    --ta-version "$VERSION" \
    -o "$OUTPUT_DIR" \
    --python-binary-name "$VENV_PYTHON" \
    --overwrite

APP_DIR="$OUTPUT_DIR/$APP_NAME"

# -----------------------------------------------------------------------
# Case preservation patch
# -----------------------------------------------------------------------
# ucc-gen unconditionally lowercases the REST handler conf-type name it
# derives from restRoot/tab-name for Configuration-page tabs (account,
# settings) -- see splunk_add_on_ucc_framework's
# RestEndpointBuilder.conf_name, which defaults to `self.name.lower()`
# (commands/rest_builder/endpoint/base.py). There is a documented `"conf"`
# globalConfig.json key, but it is only wired through to the *entity*
# object, never to the endpoint's own conf_name used for file generation --
# confirmed by reading the ucc-gen 6.5.3 source and by empirically
# rebuilding with an explicit `"conf"` override set on the account tab,
# which had no effect (still produced ta_runzero_asset_sync_account.conf.spec,
# lowercase). This does not appear to be tracked in any existing upstream
# GitHub issue as of ucc-gen 6.5.3.
#
# For an add-on whose original AOB-era name used mixed case
# (TA_runzero_asset_sync), this silently renames the account/settings conf
# files and REST handler conf-type strings to lowercase on every build. If
# shipped as-is, upgrading customers' saved account credentials and
# settings would no longer be found.
#
# This step restores the original mixed case after every build.
echo "==> Restoring original mixed-case conf names for backward compatibility"
sed -i.bak "s/'ta_runzero_asset_sync_account'/'TA_runzero_asset_sync_account'/" \
    "$APP_DIR/bin/TA_runzero_asset_sync_rh_account.py"
sed -i.bak "s/'ta_runzero_asset_sync_settings'/'TA_runzero_asset_sync_settings'/" \
    "$APP_DIR/bin/TA_runzero_asset_sync_rh_settings.py"
sed -i.bak \
    -e "s/reload.ta_runzero_asset_sync_settings/reload.TA_runzero_asset_sync_settings/" \
    -e "s/reload.ta_runzero_asset_sync_account/reload.TA_runzero_asset_sync_account/" \
    "$APP_DIR/default/app.conf"
rm -f "$APP_DIR"/bin/*.bak "$APP_DIR"/default/*.bak

mv "$APP_DIR/default/ta_runzero_asset_sync_settings.conf" \
   "$APP_DIR/default/TA_runzero_asset_sync_settings.conf"
mv "$APP_DIR/README/ta_runzero_asset_sync_settings.conf.spec" \
   "$APP_DIR/README/TA_runzero_asset_sync_settings.conf.spec"
mv "$APP_DIR/README/ta_runzero_asset_sync_account.conf.spec" \
   "$APP_DIR/README/TA_runzero_asset_sync_account.conf.spec"

if grep -rq "ta_runzero_asset_sync_account\|ta_runzero_asset_sync_settings" \
    "$APP_DIR"/bin/*.py "$APP_DIR"/default/*.conf "$APP_DIR"/README/*.spec 2>/dev/null; then
    echo "ERROR: lowercase conf-name references remain after patching. Aborting build." >&2
    exit 1
fi

echo "==> Packaging add-on"
uv run ucc-gen package --path "$APP_DIR" -o "$OUTPUT_DIR"

BUILT_PACKAGE="$(ls -t "$OUTPUT_DIR"/"$APP_NAME"-*.tar.gz | head -1)"
cp "$BUILT_PACKAGE" "$REPO_ROOT/${APP_NAME}-${VERSION}.spl"

echo "==> Done: ${APP_NAME}-${VERSION}.spl"
