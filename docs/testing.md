# Functional testing plan

This is a manual regression checklist for verifying the add-on after any change.

Build the package to test with `./scripts/build.sh` (see main `README.md`), and use a local
Splunk Enterprise instance for all steps below.

## Testing upgrade safety

We need to test that an existing customer who upgrades in place does not lose any configuration
or data. Splunk installs/upgrades an app by untarring the new package over the existing app
directory — it only adds/overwrites files present in the new package.

### Before -> after upgrade test procedure

1. Start clean. Fully remove any existing install (stop Splunk, delete the app directory
   under `$SPLUNK_HOME/etc/apps/TA_runzero_asset_sync`, clear the Splunk Web static cache,
   restart). Splunk Web aggressively caches static JS/CSS by version number.

2. Install the previous release.

3. Configure every piece of state the add-on supports:
    - An account
    - Proxy settings
    - Logging level (set it to something other than the default)
    - An Assets input
    - Let the input run at least once so a checkpoint value exists

4. Record the "before" values for everything above:
    - Whether the account still resolves/decrypts correctly
    - The saved proxy/logging values
    - The input's checkpoint timestamp

5. Install the new build as an upgrade — use "Install app from file" and check the "Upgrade
   app" box.

6. Restart Splunk, then hard-refresh the browser to rule out stale static assets.

7. Run the input, by toggling its status off and then on again.

8. Compare after state to recorded before state:
    - Account tab still shows the account, with data
    - Proxy tab still shows all previously-saved values
    - Logging tab still shows the previously-selected level
    - The Assets input still exists with all previously-configured fields intact
    - The input resumes from its existing checkpoint
    - New assets are picked up on the subsequent run
    - No errors in `splunkd.log` or the browser console referencing missing/invalid conf

9. Make absolutely sure that new assets are picked up on the subsequent run as expected!

## Basic testing procedure

### 1. Fresh install

- Install the `.spl` on a clean Splunk Enterprise
- Confirm the "Configuration" page loads with Account / Proxy / Logging tabs and no
  JavaScript console errors.
- Confirm the "Inputs" page loads with the Assets input table.

### 2. Account tab

- Create an account
- Verify validators fire
- Edit, clone, and delete an account
- Case-sensitivity regression check: confirm the saved credential is stored under the
  mixed-case `TA_runzero_asset_sync_account` conf/stanza name, not a lowercased variant.

### 3. Proxy tab

- Enable proxy, set type/url/port/username/password/`proxy_rdns`. Save and reopen to confirm
  persistence.
- Disable proxy, confirm the input still runs successfully without a proxy configured.

### 4. Logging tab

- Change `loglevel` (default `INFO`) to `DEBUG`, ensure persistence.

### 5. Inputs — create/edit/delete

- Create an "Assets" input referencing an account (`global_account`), set index, `sync_type`
  (New/Updated/All), `import_services`, `search_filter`, `fields`, `interval`, `batch_size`.
- Confirm the table view and "more info" expanded view render all fields correctly.
- Edit an existing input, clone it, and delete it.

### 6. Data collection (core business logic)

- With a real (or test) runZero account, let the input run. Confirm events land in the
  configured index with the expected fields.
- Test each `sync_type`: `created`, `updated`, `all` — confirm the request URL/query
  differs as expected.
- If you need to trigger a re-run, toggle the Input to disabled, then enabled again.

### 7. Checkpointing

- Run the input once, note the last-imported timestamp. Run again and confirm only newer assets
  are pulled.

### 8. Dashboards & nav

- Confirm `asset_overview.xml` and `asset_risk.xml` dashboards load without errors, and that the
  nav menu links to them correctly.

### 9. AppInspect

- Run `./scripts/check.sh` and confirm no new `error`/`failure`/`future_failure` results.
