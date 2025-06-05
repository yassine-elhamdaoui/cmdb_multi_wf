#!/bin/bash
set -e

sed -i "s/K8S_NAMESPACE/${K8S_NAMESPACE}/g" ./kubernetes/namespace.yaml
sed -i "s/PROJECT_NAME/${CI_PROJECT_NAME}/g" ./kubernetes/namespace.yaml

sed -i "s/LOB_NAMESPACE/${LOB_NAMESPACE}/g" ./kubernetes/sub-namespace.yaml
sed -i "s/K8S_NAMESPACE/${K8S_NAMESPACE}/g" ./kubernetes/sub-namespace.yaml

# sed -i "s/PROJECT_NAME/${CI_PROJECT_NAME}/g" ./kubernetes/deployment.yaml
# sed -i "s/K8S_NAMESPACE/${K8S_NAMESPACE}/g" ./kubernetes/deployment.yaml
# sed -i "s#CONTAINER_IMAGE#${CONTAINER_IMAGE}#g" ./kubernetes/deployment.yaml

sed -i "s/PROJECT_NAME/${CI_PROJECT_NAME}/g" ./kubernetes/cmdb-wf.yaml
sed -i "s/K8S_NAMESPACE/${K8S_NAMESPACE}/g" ./kubernetes/cmdb-wf.yaml
sed -i "s#CONTAINER_IMAGE#${CONTAINER_IMAGE}#g" ./kubernetes/cmdb-wf.yaml


# sed -i "s/PROJECT_NAME/${CI_PROJECT_NAME}/g" ./kubernetes/service.yaml
# sed -i "s/K8S_NAMESPACE/${K8S_NAMESPACE}/g" ./kubernetes/service.yaml

# sed -i "s/PROJECT_NAME/${CI_PROJECT_NAME}/g" ./kubernetes/virtual-service.yaml
# sed -i "s/K8S_NAMESPACE/${K8S_NAMESPACE}/g" ./kubernetes/virtual-service.yaml

# sed -i "s/PROJECT_NAME/${CI_PROJECT_NAME}/g" ./kubernetes/authorization-policy.yaml
# sed -i "s/K8S_NAMESPACE/${K8S_NAMESPACE}/g" ./kubernetes/authorization-policy.yaml

sed -i "s/PROJECT_NAME/${CI_PROJECT_NAME}/g" ./kubernetes/external-secret-adb-admin-credentials.yml
sed -i "s/K8S_NAMESPACE/${K8S_NAMESPACE}/g" ./kubernetes/external-secret-adb-admin-credentials.yml
sed -i "s/ADB_ADMIN_SECRET_NAME/${ADB_ADMIN_SECRET_NAME}/g" ./kubernetes/external-secret-adb-admin-credentials.yml

sed -i "s/PROJECT_NAME/${CI_PROJECT_NAME}/g" ./kubernetes/external-secret-adb-schema-credentials.yml
sed -i "s/K8S_NAMESPACE/${K8S_NAMESPACE}/g" ./kubernetes/external-secret-adb-schema-credentials.yml
sed -i "s/PROJ_VAULT_SECRET_NAME/${PROJ_VAULT_SECRET_NAME}/g" ./kubernetes/external-secret-adb-schema-credentials.yml

# sed -i "s/PROJECT_NAME/${CI_PROJECT_NAME}/g" ./kubernetes/schema_user_job.yaml
# sed -i "s/K8S_NAMESPACE/${K8S_NAMESPACE}/g" ./kubernetes/schema_user_job.yaml
# sed -i "s#DB_SCHEMA_CREATOR_IMAGE#${DB_SCHEMA_CREATOR_IMAGE}#g" ./kubernetes/schema_user_job.yaml
