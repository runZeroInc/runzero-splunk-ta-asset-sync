rm -f TA_runzero_asset_sync.tar TA_runzero_asset_sync.tar.gz *.spl
tar cf TA_runzero_asset_sync.tar TA_runzero_asset_sync && gzip -9 TA_runzero_asset_sync.tar && mv TA_runzero_asset_sync.tar.gz TA_runzero_asset_sync-3.0.4.spl
