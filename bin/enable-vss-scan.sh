#!/bin/bash
set -exo pipefail

# check if CONTAINER_REGISTRY_REGION and CONTAINER_REPO_NAME are defined and valid
if [[ -z "${CONTAINER_REGISTRY_REGION}" ]]; then
  echo "Please provide a valid value for CONTAINER_REGISTRY_REGION."
  exit 1
fi

if [[ -z "${CONTAINER_REPO_NAME}" ]]; then
  echo "Please provide a valid value for CONTAINER_REPO_NAME."
  exit 1
fi

export OCI_CLI_CONFIG_FILE=./config

# --------------------------------
# Enable VSS Scanning
# --------------------------------

cat > ./target-registry-options.json <<EOL
{
    "type": "OCIR",
    "url": "https://${CONTAINER_REGISTRY_REGION}.ocir.io",
    "compartmentId": "${TF_VAR_tenancy_ocid}",
    "repositories": [
        "${CONTAINER_REPO_NAME}/${CI_PROJECT_NAME}"
    ]
}
EOL

# Check if the container repo exists, if not create new and enable VSS on it
repo_found=$(oci artifacts container repository list --config-file $OCI_CLI_CONFIG_FILE --region $CLUSTER_REGION --compartment-id "${TF_VAR_tenancy_ocid}" --display-name "${CONTAINER_REPO_NAME}/${CI_PROJECT_NAME}" | jq '.data."repository-count"')

if [[ $repo_found -eq 0 ]]; then

    # Create a new container repo
    oci artifacts container repository create --config-file $OCI_CLI_CONFIG_FILE --region $CLUSTER_REGION --compartment-id "${TF_VAR_tenancy_ocid}" --display-name "${CONTAINER_REPO_NAME}/${CI_PROJECT_NAME}" --wait-for-state AVAILABLE
	echo "Container Repo ${CONTAINER_REPO_NAME}/${CI_PROJECT_NAME} not found. Created new"

    # Create a new container image scan recipe
	scan_recipe_id=$(oci vulnerability-scanning container scan recipe create --config-file $OCI_CLI_CONFIG_FILE --region $CLUSTER_REGION --compartment-id "${TF_VAR_tenancy_ocid}" --display-name "${CONTAINER_REPO_NAME}/${CI_PROJECT_NAME}-ContainerScanRecipe" --scan-settings '{"scanLevel": "STANDARD"}' | jq -r '.data.id')
	echo "Created Container Image Scan Recipe \"${CONTAINER_REPO_NAME}/${CI_PROJECT_NAME}-ContainerScanRecipe\""

    # Create a new container image scan target
    oci vulnerability-scanning container scan target create --config-file $OCI_CLI_CONFIG_FILE --region $CLUSTER_REGION --compartment-id "${TF_VAR_tenancy_ocid}" --display-name "${CONTAINER_REPO_NAME}/${CI_PROJECT_NAME}-ContainerScanTarget" --container-scan-recipe-id $scan_recipe_id --target-registry file://./target-registry-options.json
	echo "Created Container Image Scan Target \"${CONTAINER_REPO_NAME}-dev/${CI_PROJECT_NAME}-ContainerScanTarget\""
fi
