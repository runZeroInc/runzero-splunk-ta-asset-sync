
# encoding = utf-8

import datetime
import hashlib
import json
import os
import requests
import ssl
import sys
import time

'''
    IMPORTANT
    Edit only the validate_input and collect_events functions.
    Do not edit any other part in this file.
    This file is generated only once when creating the modular input.
'''

CHECKPOINT_KEY_SUFFIX="since"


def validate_input(helper, definition):
    """Implement your own validation logic to validate the input stanza configurations"""
    # This example accesses the modular input variable
    # sync_type = definition.parameters.get('sync_type', None)
    # search_filter = definition.parameters.get('search_filter', None)
    # services = definition.parameters.get('services', None)
    pass

def collect_events(helper, ew):
    # (log_level can be "debug", "info", "warning", "error" or "critical", case insensitive)
    #helper.set_log_level("debug")

    use_proxy = False
    if len(helper.get_proxy()) > 0:
        use_proxy = True

    # XXX: Special code to use system SSL trust store
    _patch_rest_helper(helper, use_proxy)

    stanza = helper.get_input_stanza_names()
    if isinstance(stanza, list):
        stanza = stanza[0]
    checkpoint_key = f"{stanza}_{CHECKPOINT_KEY_SUFFIX}"

    # Get options
    opt_sync_type = helper.get_arg('sync_type')
    opt_search_filter = helper.get_arg('search_filter')
    if opt_search_filter == None:
        opt_search_filter = ""
    opt_services = helper.get_arg('services')
    if opt_services == None:
        opt_services = ""
    opt_page_size = helper.get_arg('batch_size')
    if opt_page_size == None or opt_page_size == "":
        opt_page_size = "1000"

    # Get account credentials
    # NOTE: When testing inside the add-on builder UI, only username/password are
    # supported.  Add-on builder will overwrite the api_endpoint/api_key configuration
    # in the source files, so make sure you manually correct that after saving!!!
    global_account = helper.get_arg('global_account')
    if 'api_endpoint' in global_account:
        api_endpoint = global_account['api_endpoint']
    elif 'username' in global_account:
        # Work around when testing inside add-on builder
        # add-on builder doesn't support custom global account parameters
        api_endpoint = global_account['username']
    if 'api_key' in global_account:
        api_key = global_account['api_key']
    elif 'password' in global_account:
        # Work around when testing inside add-on builder
        # add-on builder doesn't support custom global account parameters
        api_key = global_account['password']

    try:
        opt_since = int(float(helper.get_check_point(checkpoint_key)))
    except (ValueError, TypeError):
        opt_since = 0

    if opt_since == 0:
        # try to find the old checkpoint value from the previous plugin version:
        splunk_home = os.environ.get('SPLUNK_HOME')
        old_chkpt_key = hashlib.sha256(stanza.encode("utf-8")).hexdigest()
        old_chkpt_file = os.path.join(splunk_home or "", 'var', 'lib', 'splunk', 'modinputs', 'assets', old_chkpt_key)
        helper.log_debug(f"Could not find checkpoint in kvstore, so attempting to read from file: {old_chkpt_file}")
        if os.path.isfile(old_chkpt_file):
            try:
                with open(old_chkpt_file, "r") as f:
                    old_chkpt_val = json.loads(f.read())
                    if old_chkpt_val and old_chkpt_val['data'] and old_chkpt_val['data']['since']:
                        opt_since = int(float(old_chkpt_val['data']['since']))
            except Exception as e:
                # ignore errors, we did our best
                helper.log_debug(f"Could not find old checkpoint: {e}")

    headers = {"Authorization": f"Bearer {api_key}"}
    checkpoint_ts = opt_since

    # Page through API
    start_key = ""
    cnt = 0
    helper.log_debug(f"Fetching assets {opt_sync_type} since {checkpoint_ts}")
    while True:
        url = f"https://{api_endpoint}/api/v1.0/export/org/assets/sync/{opt_sync_type}/assets.json?search={opt_search_filter}&since={opt_since}&services={opt_services}&start_key={start_key}&page_size={opt_page_size}"
        response = helper.send_http_request(url, "GET", parameters=None, payload=None,
                                            headers=headers, cookies=None, verify=True, cert=None,
                                            timeout=None, use_proxy=use_proxy)
        # check the response status, if the status is not sucessful, raise requests.HTTPError
        response.raise_for_status()

        r_json = response.json()
        if r_json == None or r_json['assets'] == None:
            helper.log_error("assets array missing")
            raise("assets array missing")
        assets = r_json['assets']

        if len(assets) == 0:
            break

        for asset in assets:
            event_ts = 0
            try:
                if opt_sync_type == 'created':
                    event_ts = float(asset['created_at'])
                else:
                    event_ts = float(asset['updated_at'])
                if event_ts > checkpoint_ts:
                    checkpoint_ts = event_ts
            except (ValueError, TypeError):
                event_ts = time.time()
                helper.log_debug(f"Could not determine {opt_sync_type} time for asset.id={asset['id']}.  Using current time ({event_ts}) for _splunk_event_ts instead")

            # TODO: Splunk isn't respecting the time sent through the time event.  But why?
            # We're adding extra timestamps to the JSON asset and using TIMESTAMP_FIELDS=splunk_event_ts
            # in props.conf to work around.
            asset['_splunk_event_ts'] = event_ts
            asset['_splunk_ingest_ts'] = time.time()

            # Write the event to Splunk index
            event = helper.new_event(source=helper.get_input_type(), index=helper.get_output_index(), sourcetype=helper.get_sourcetype(), data=json.dumps(asset), time=event_ts, done=True, unbroken=True)
            ew.write_event(event)
            cnt += 1

        # Older versions of runZero don't support pagination
        # If the response isn't paged, finish now to avoid an infinite loop
        if "next_key" not in r_json:
            helper.log_debug("Batch fetching was not supported by the console, so ingested all records in one request.")
            break

        if r_json["next_key"] == "":
            break

        start_key = r_json["next_key"]

    if cnt > 0:
        helper.log_info(f"Successfully imported {cnt} assets {opt_sync_type} since {opt_since}.")
    else:
        helper.log_info(f"No assets {opt_sync_type} since {opt_since} to import.")

    # Save checkpoint so we'll only refresh newly created/updated assets on next iteration
    if checkpoint_ts > opt_since:
        helper.log_debug(f"Saving {checkpoint_ts} checkpoint to {checkpoint_key}")
        helper.save_check_point(checkpoint_key, int(checkpoint_ts))


class CustomHTTPAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ca_files = []
        if sys.platform.startswith('linux'):
            ca_files = [
                '/etc/pki/tls/certs/ca-bundle.crt',   # RedHat
                '/etc/pki/tls/cert.pem',              # Fedora <= 34, RHEL <= 9, CentOS <= 9
                '/etc/ssl/certs/ca-certificates.crt', # Debian
                '/etc/ssl/cert.pem',                  # Alpine, Arch, Fedora 34+, OpenWRT, RHEL 9+, BSD
                '/etc/ssl/ca-bundle.pem',             # SUSE
            ]
        elif sys.platform.startswith('darwin'):
            ca_files = ['/usr/local/etc/openssl/cert.pem']

        ssl_ctx = ssl.create_default_context()
        for ca_file in ca_files:
            if os.path.isfile(ca_file):
                ssl_ctx.load_verify_locations(ca_file)

        super().init_poolmanager(*args, **kwargs, ssl_context=ssl_ctx)

def _patch_rest_helper(helper, use_proxy):
    # Monkey-patch the underlying requests session provided by
    # the AOB library (typically in splunk_aoblib/rest_helper.py)
    # to use the system trust store.
    if not (helper and helper.rest_helper):
        return

    http_session = requests.Session()
    http_session.mount(
        'http://', requests.adapters.HTTPAdapter(max_retries=3))
    http_session.mount(
        'https://', CustomHTTPAdapter(max_retries=3))
    helper.rest_helper.http_session = http_session

    # Now set the requests_proxy variable, since this is normally
    # set at the same time as the http_session.
    if use_proxy:
        proxy_uri = None
        proxy = helper.get_proxy()
        if proxy and proxy.get('proxy_url') and proxy.get('proxy_type'):
            proxy_uri = proxy['proxy_url']
            if proxy.get('proxy_port'):
                proxy_uri = '{0}:{1}'.format(proxy_uri, proxy.get('proxy_port'))
            if proxy.get('proxy_username') and proxy.get('proxy_password'):
                proxy_uri = '{0}://{1}:{2}@{3}/'.format(proxy['proxy_type'], proxy[
                    'proxy_username'], proxy['proxy_password'], proxy_uri)
            else:
                proxy_uri = '{0}://{1}'.format(proxy['proxy_type'], proxy_uri)
        helper.rest_helper.requests_proxy = {'http': proxy_uri, 'https': proxy_uri}
