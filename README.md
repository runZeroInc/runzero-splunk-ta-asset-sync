# Validating and Updating runZero Asset Sync

1. Install Splunk Enterprise and Add-on Builder
    * Enterprise Free Trial: https://www.splunk.com/en_us/download/splunk-enterprise.html
    * Splunk Add-on Builder: https://splunkbase.splunk.com/app/2962
    
2. Clone the repository, then run `./build.sh` to build the SPL and finally install the SPL through "Manage Apps".

3. Open Add-on Builder in Splunk, find runZero Asset Sync in "Other apps and add-ons" and select "Validate & Package".
    * "Import Project" in the first tab of the Add-on Builder will error and could leave behind artifacts of the install.
    * Validation could take a few minutes to finish.
    * If any errors are reported, correct and then re-validate.

4. Download the validated SPL from the Add-on Builder.

5. In Splunkbase, under "My Apps" select "Manage App" and then select "In Splunkbase Classic". After, on the version listing, select "New Version".
    * https://dev.splunk.com/enterprise/docs/releaseapps/splunkbase/managecontentonsplunkbase
