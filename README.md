# Validating and Updating runZero Asset Sync

1. Install Splunk Enterprise and Add-on Builder
    * Enterprise Free Trial: https://www.splunk.com/en_us/download/splunk-enterprise.html
    * Splunk Add-on Builder: https://splunkbase.splunk.com/app/2962
    
2. Clone the repository, then run `./build.sh` to build the SPL and finally install the SPL through "Manage Apps".

3. Open Add-on Builder in Splunk, find runZero Asset Sync in "Other apps and add-ons" and select "Validate & Package".
    * Don't use "Import Project" in the first tab of the Add-on Builder!!!  This is useful for testing/developing, but it will silently alter several files and break functionality.  For example, it will change the case of the package/settings names in a way that is backwards incompatible with older versions of the add-on.  It will also remove the api_key/api_endpoint account settings, and replace them with username/password.  Despite the tempation, don't use this option.
    * Validation could take a few minutes to finish.
    * If any errors are reported, correct and then re-validate.

4. Download the validated SPL from the Add-on Builder.

5. In Splunkbase, under "My Apps" select "Manage App" and then select "In Splunkbase Classic". After, on the version listing, select "New Version".
    * https://dev.splunk.com/enterprise/docs/releaseapps/splunkbase/managecontentonsplunkbase
