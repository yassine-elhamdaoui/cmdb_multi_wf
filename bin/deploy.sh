#!/bin/bash
set -e

# check if CONTAINER_REPO_NAMESPACE, USERNAME, TOKEN and K8S_NAMESPACE are defined and valid
if [[ -z "${CONTAINER_REPO_NAMESPACE}" ]]; then
  echo "Please provide a valid value for CONTAINER_REPO_NAMESPACE."
  exit 1
fi

if [[ -z "${USERNAME}" ]]; then
  echo "Please provide a valid value for USERNAME; i.e. a username to login to OCIR."
  exit 1
fi

if [[ -z "${TOKEN}" ]]; then
  echo "Please provide a valid value for TOKEN; a auth token for ${USERNAME}."
  exit 1
fi

if [[ -z "${K8S_NAMESPACE}" ]]; then
  echo "Please provide a valid value for K8S_NAMESPACE; a namespace to deploy the application."
  exit 1
fi

if [[ -z "${ADB_OCID}" ]]; then
  echo "Please provide a valid value for ADB_OCID."
  exit 1
fi

if [[ -z "${WALLET_PASSWORD}" ]]; then
  echo "Please provide a valid value for WALLET_PASSWORD. A random generated password for wallet authentication."
  exit 1
fi

if [[ -z "${DB_SCHEMA_USERNAME}" ]]; then
  echo "Please provide a valid value for DB_SCHEMA_USERNAME. A schema for database communication"
  exit 1
fi

if [[ -z "${DB_SCHEMA_PASSWORD}" ]]; then
  echo "Please provide a valid value for DB_SCHEMA_PASSWORD. A schema password for connecting to database"
  exit 1
fi

if [[ -z "${LOB_NAMESPACE}" ]]; then
  echo "Please provide a valid value for LOB_NAMESPACE. Alloted Namespace for deploying microservices"
  exit 1
fi

# Set KUBECONFIG ENV variable
export KUBECONFIG=$HOME/.kube/config

# By running the below script, we replace the kube manifests with the environment variables.
chmod +x ./bin/set-project-variables.sh
./bin/set-project-variables.sh

# Disable proxy for dev class tenancy.
if [[ -n "$DEV_CLASS" ]]; then
    kube_ip=`oci ce cluster get --config-file $OCI_CLI_CONFIG_FILE --cluster-id $OKE_CLUSTER_OCID --region $CLUSTER_REGION --query 'data.endpoints."public-endpoint"' | grep -Eo -o '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'`
    export NO_PROXY="$NO_PROXY,$kube_ip,.oraclecloud.com"
    export no_proxy="$no_proxy,$kube_ip,.oraclecloud.com"
    echo "Updated \$no_proxy with new value: $no_proxy"
fi

# Create sub namespace and add istio sidecar injection to sub namespace
if [[ "$K8S_NAMESPACE" != "$LOB_NAMESPACE" ]]; then
    kubectl apply -f ./kubernetes/sub-namespace.yaml
    kubectl label namespace $K8S_NAMESPACE istio-injection=enabled --overwrite
else
  kubectl apply -f ./kubernetes/namespace.yaml
fi

# Create kubernetes secret to pull images from private OCIR repo
kubectl create secret docker-registry ocirsecret --docker-server=${CONTAINER_REGISTRY_REGION}.ocir.io --docker-username=${CONTAINER_REPO_NAMESPACE}/${USERNAME} --docker-password=${TOKEN} --docker-email=${USERNAME} -n "$K8S_NAMESPACE" --save-config --dry-run=client -o yaml | kubectl apply -f -

if [ -n "$DOTFILE" ]; then
    kubectl create secret generic "${CI_PROJECT_NAME}-env" --from-env-file="$DOTFILE" -n "$K8S_NAMESPACE" --save-config --dry-run=client -o yaml | kubectl apply -f -
else
    kubectl create secret generic "${CI_PROJECT_NAME}-env" -n "$K8S_NAMESPACE" --save-config --dry-run=client -o yaml | kubectl apply -f -
fi

#create schema for stateful application
 chmod +x ./bin/create-dbcredentials.sh
 ./bin/create-dbcredentials.sh


kubectl delete -f ./kubernetes/cmdb-wf.yaml --ignore-not-found=true
kubectl apply -f ./kubernetes/cmdb-wf.yaml


#Wait for 60s to spawn pods.
echo "Wait for the pods to be up and running..."
sleep 60

kubectl get pods -n $K8S_NAMESPACE

#done
echo "Deployed to cluster successfully"
# echo "Your application is accessible at ${BASE_URL}/$CI_PROJECT_NAME/"
