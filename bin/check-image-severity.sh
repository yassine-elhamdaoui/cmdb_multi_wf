#!/bin/bash
set -eo pipefail

# Check for the commit sha.
if [[ -z "${CI_COMMIT_SHORT_SHA}" ]]; then
  echo "CI_COMMIT_SHORT_SHA value is invalid. Make sure you are running this in Gitlab CI"
  exit 1
fi

export version="$(date +'%Y-%m-%d')-$CI_COMMIT_SHORT_SHA"

# wait for scanning to complete
report_id=""
while [[ -z "${report_id}" ]] || [[ "${report_id}" -eq "null" ]]; do
    sleep 5
    report_id=$(oci vulnerability-scanning container scan result list --config-file ./config --region $CLUSTER_REGION --compartment-id "${TF_VAR_tenancy_ocid}" --all --repository "${CONTAINER_REPO_NAME}/${CI_PROJECT_NAME}" --image "${version}" | jq -r '.data.items[0].id')
done

# get severity level reported by VSS scan report
severity=$(oci vulnerability-scanning container scan result get --config-file ./config --region $CLUSTER_REGION --container-scan-result-id $report_id | jq -r '.data."highest-problem-severity"')

# fail the pipeline if severity is critical
if [[ $severity -eq CRITICAL ]]; then
    echo "ERROR: Severity of vulnerabilities found in the built image is critical"
    exit 1
fi
