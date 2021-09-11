
import ta_rumble_asset_sync_declare

from splunktaucclib.rest_handler.endpoint import (
    field,
    validator,
    RestModel,
    SingleModel,
)
from splunktaucclib.rest_handler import admin_external, util
from splunk_aoblib.rest_migration import ConfigMigrationHandler

util.remove_http_proxy_env_vars()


fields = [
    field.RestField(
        'api_key',
        required=True,
        encrypted=True,
        default=None,
        validator=validator.String(
            min_len=16,
            max_len=256,
        )
    ),
    field.RestField(
        'api_endpoint',
        required=True,
        encrypted=False,
        default='console.rumble.run'
    ),
]
model = RestModel(fields, name=None)


endpoint = SingleModel(
    'ta_rumble_asset_sync_account',
    model,
)


if __name__ == '__main__':
    admin_external.handle(
        endpoint,
        handler=ConfigMigrationHandler,
    )

