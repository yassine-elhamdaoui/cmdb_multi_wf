#!/bin/bash
set -eo pipefail

#Copy private key file contents
cp -f "$key_file" ./api_key.pem
chown $(id -u):$(id -g) ./api_key.pem
chmod 400 ./api_key.pem

#Create a oci config file
cat > ./config <<EOL
[DEFAULT]
user=${TF_VAR_user_ocid}
fingerprint=${TF_VAR_fingerprint}
tenancy=${TF_VAR_tenancy_ocid}
region=${TF_VAR_region}
key_file=./api_key.pem
EOL

chmod 400 ./config
export OCI_CLI_CONFIG_FILE=./config
