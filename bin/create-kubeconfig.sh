#!/bin/bash
set -e

# Create .kube directory under $HOME to store configuration files to access cluster.
mkdir -p "$HOME/.kube/${CI_PROJECT_NAME}/${CI_ENVIRONMENT_NAME}"

# Create ENV variables for oci cli to work.
export OCI_CONFIG_FILE=./config
export KUBECONFIG="$HOME/.kube/${CI_PROJECT_NAME}/${CI_ENVIRONMENT_NAME}/config"
#Check for kube config and remove if present
if [ -e $KUBECONFIG ]
then
    rm $KUBECONFIG
fi

# Create a kubeconfig to access to cluster.
oci ce cluster create-kubeconfig --config-file $OCI_CONFIG_FILE --cluster-id $OKE_CLUSTER_OCID --file $KUBECONFIG --overwrite --region $CLUSTER_REGION --token-version 2.0.0 --kube-endpoint PUBLIC_ENDPOINT
