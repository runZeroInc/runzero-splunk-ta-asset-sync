container:
	podman run --arch amd64 -it -p 8000:8000 -e "SPLUNK_PASSWORD=password" -e "SPLUNK_START_ARGS=--accept-license" splunk/splunk:latest
