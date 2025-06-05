#!/bin/bash
set -eo pipefail

export OCI_CLI_CONFIG_FILE=./config

# Check for VAULT_OCID ENV variable
if [[ -z "${VAULT_OCID}" ]]; then
  echo "VAULT_OCID value is invalid."
  exit 1
fi

# Fetch management endpoint of the vault.
MANAGEMENT_ENDPOINT=$(oci kms management vault get --config-file $OCI_CLI_CONFIG_FILE --region $CLUSTER_REGION --vault-id "${VAULT_OCID}" --query 'data."management-endpoint"' --raw-output)
if [[ -z "${MANAGEMENT_ENDPOINT}" ]]; then
  echo "MANAGEMENT_ENDPOINT not found."
  exit 1
fi

# Check for IMG_SIGN_KEY_OCID ENV variable
if [[ -z "${IMG_SIGN_KEY_OCID}" ]]; then
  echo "IMG_SIGN_KEY_OCID value is invalid."
  exit 1
fi

# Fetch key version OCID of the key.
key_version_ocid_string=$(oci kms management key-version list --config-file $OCI_CLI_CONFIG_FILE --region $CLUSTER_REGION --key-id "${IMG_SIGN_KEY_OCID}" --endpoint "${MANAGEMENT_ENDPOINT}" --all --sort-by "TIMECREATED" | jq '.data[0].id')
key_version_ocid=$(awk -F'"|"' '{print $2}' <<< $key_version_ocid_string)
if [[ -z "${key_version_ocid}" ]]; then
  echo "key_version_ocid not found."
  exit 1
fi

# Fetch the container image OCID from OCIR.
image_ocid_string=$(oci artifacts container image list --config-file $OCI_CLI_CONFIG_FILE --region $CLUSTER_REGION --compartment-id "${TF_VAR_tenancy_ocid}" --display-name "${CONTAINER_REPO_NAME}/${CI_PROJECT_NAME}:${version}" | jq '.data.items[0].id')
image_ocid=$(awk -F'"|"' '{print $2}' <<< $image_ocid_string)
if [[ -z "${image_ocid}" ]]; then
  echo "image_ocid not found."
  exit 1
fi

#-----------------------------------------------------------
# Image sign upload
#-----------------------------------------------------------
oci artifacts container image-signature sign-upload --config-file $OCI_CLI_CONFIG_FILE --region $CLUSTER_REGION --compartment-id "${TF_VAR_tenancy_ocid}" --kms-key-id "${IMG_SIGN_KEY_OCID}" --kms-key-version-id "${key_version_ocid}" --signing-algorithm SHA_256_RSA_PKCS_PSS --image-id "${image_ocid}" --description "Signed Image for ${CI_PROJECT_NAME}:${version}"

echo "Image ${CI_PROJECT_NAME}:$version signed.........."
