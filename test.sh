#!/bin/bash

AUTH=`echo ${SPLUNK_USER}:${SPLUNK_PASSWORD} | base64.exe -w 0`

echo "[*] Getting an authentication token..."

TOKEN=$(curl -s \
   -X GET \
   -H "Authorization: Basic {$AUTH}" \
   -H "Cache-Control: no-cache" "https://api.splunk.com/2.0/rest/login/splunk" \
| jq -r .data.token)

PKG=`find -name '*.spl'`

echo "[*] Submitting ${PKG} for validation..."

DATA=$(curl -s \
   -X POST \
   -H "Authorization: bearer ${TOKEN}" \
   -H "Cache-Control: no-cache" \
   -H "Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW" \
   -F "app_package=@${PKG}" "https://appinspect.splunk.com/v1/app/validate")

RID=$(echo $DATA | jq -r .request_id)


REPORT_CMD="curl -s -H \"Authorization: bearer ${TOKEN}\" https://appinspect.splunk.com/v1/app/report/${RID}"
echo "[*] Download the report with ${REPORT_CMD}"