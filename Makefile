container:
	podman run --arch amd64 -it -p 8001:8000 -e "SPLUNK_PASSWORD=password" -e "SPLUNK_START_ARGS=--accept-license" -e SPLUNK_GENERAL_TERMS=--accept-sgt-current-at-splunk-com splunk/splunk:latest
