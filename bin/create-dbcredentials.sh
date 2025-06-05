#!/bin/bash
set -eo pipefail

UPDATE_SCHEMA=false
CREATE_SCHEMA=true
echo "Setting DB credentials in vaultnK8"

if (kubectl get secret/db-credentials -n "$K8S_NAMESPACE") &>> /dev/null; then
    existing_password=$(kubectl get secret/db-credentials -n "$K8S_NAMESPACE" -o jsonpath='{.data.DB_PASSWORD}' | base64 -d)
    if [[ $existing_password == $DB_SCHEMA_PASSWORD ]]; then
      echo "Creating DB credentials in vaultnK8"
      UPDATE_SCHEMA=false
      CREATE_SCHEMA=true
    else
      UPDATE_SCHEMA=true
      CREATE_SCHEMA=false
      echo "Updating DB credentials in vaultnK8"
    fi
fi

      UPDATE_SCHEMA=false
      CREATE_SCHEMA=true
if [ "$CREATE_SCHEMA" = true ] ; then
  echo "Generating Wallet"
  oci db autonomous-database generate-wallet --autonomous-database-id "$ADB_OCID" --file "db_wallet.zip" --password "$WALLET_PASSWORD" --region "$CLUSTER_REGION"
  unzip "./db_wallet.zip" -d "db_wallet"
  sed -i 's#?/network/admin#/opt/db-wallet#g' ./db_wallet/sqlnet.ora
  kubectl create secret generic "db-wallet" --from-file="./db_wallet" -n "$K8S_NAMESPACE" --save-config --dry-run=client -o yaml | kubectl apply -f -
  echo "Created new k8s secret db-wallet"
  rm -rf db_wallet.zip "./db_wallet"
  echo "Deleting extracted wallet"
  #export DB_TNS_NAME=$(printf "%s-----%s" "$ADB_OCID" "$CLUSTER_REGION")
  export DB_TNS_NAME=$(oci db autonomous-database get --autonomous-database-id "$ADB_OCID" --region "$CLUSTER_REGION" --query "data.\"connection-strings\".profiles[?\"consumer-group\"=='TP'].\"display-name\" | [0]" | tr -d '"')
  export DBX_SECRET=$(echo "{\"username\": \"$DB_SCHEMA_USERNAME\",\"password\": \"$DB_SCHEMA_PASSWORD\",\"service\": \"$DB_TNS_NAME\",\"wallet_password\": \"$WALLET_PASSWORD\",\"base_url\": \"$BASE_URL\"}")
  echo $DBX_SECRET
  export DB_B64_SECRET_CONTENT=$(echo "{\"username\": \"$DB_SCHEMA_USERNAME\",\"password\": \"$DB_SCHEMA_PASSWORD\",\"service\": \"$DB_TNS_NAME\",\"wallet_password\": \"$WALLET_PASSWORD\",\"base_url\": \"$BASE_URL\"}" | base64)
  oci vault secret create-base64 --compartment-id "$SECRET_COMPARTMENT_ID" --secret-name "$PROJ_VAULT_SECRET_NAME" --vault-id "$SECRET_VAULT_OCID" --secret-content-content "$DB_B64_SECRET_CONTENT" --secret-content-stage "CURRENT" --key-id "$SECRET_KEY_OCID" --region "$CLUSTER_REGION" --debug || true
  kubectl delete -f ./kubernetes/external-secret-adb-admin-credentials.yml --ignore-not-found=true
  kubectl delete -f ./kubernetes/external-secret-adb-schema-credentials.yml --ignore-not-found=true
  kubectl apply -f ./kubernetes/external-secret-adb-admin-credentials.yml
  kubectl apply -f ./kubernetes/external-secret-adb-schema-credentials.yml
 # kubectl delete -f ./kubernetes/schema_user_job.yaml --ignore-not-found=true
 # kubectl apply -f ./kubernetes/schema_user_job.yaml
elif [ "$UPDATE_SCHEMA" = true ] ; then
  export DB_TNS_NAME=$(oci db autonomous-database get --autonomous-database-id "$ADB_OCID" --region "$CLUSTER_REGION" --query "data.\"connection-strings\".profiles[?\"consumer-group\"=='TP'].\"display-name\" | [0]" | tr -d '"')
  export DB_B64_SECRET_CONTENT=$(echo "{\"username\": \"$DB_SCHEMA_USERNAME\",\"password\": \"$DB_SCHEMA_PASSWORD\",\"service\": \"$DB_TNS_NAME\",\"wallet_password\": \"$WALLET_PASSWORD\",\"base_url\": \"$BASE_URL\"}" | base64)
  secret_ocid=$(oci secrets secret-bundle get-secret-bundle-by-name --secret-name "$PROJ_VAULT_SECRET_NAME" --vault-id "$SECRET_VAULT_OCID" --region "$CLUSTER_REGION" | jq -r ".data" | jq -r '.["secret-id"]')
  oci vault secret update-base64 --secret-id $secret_ocid --force --secret-content-content "$DB_B64_SECRET_CONTENT" --secret-content-stage "CURRENT"  --region "$CLUSTER_REGION"
  sleep 30
  kubectl annotate es db-credentials force-sync=$(date +%s) -n "$K8S_NAMESPACE" --overwrite
  #kubectl delete -f ./kubernetes/schema_user_job.yaml --ignore-not-found=true
  #kubectl apply -f ./kubernetes/schema_user_job.yaml
else
  echo "No database credentials will be added"
fi
