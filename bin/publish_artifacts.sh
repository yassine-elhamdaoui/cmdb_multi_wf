#!/bin/bash

if [[ -v CI_COMMIT_TAG ]]; then
  export version="$CI_COMMIT_TAG"
elif [[ -v CI_COMMIT_SHORT_SHA ]]; then
  export version="$CI_COMMIT_SHORT_SHA"
else
  echo "CI_COMMIT_SHORT_SHA value is invalid. Make sure you are running this in Gitlab CI"
  exit 1
fi

#building a docker image and push to prod artifactory
if [[ -n "$DEV_CLASS" ]] || [[ $CI_ENVIRONMENT_NAME == "UAT" ]] || [[ $CI_ENVIRONMENT_NAME == "PROD" ]]; then
  docker build . -t "${CI_PROJECT_NAME}:$version" --pull --build-arg set_proxy=true
else
  docker build . -t "${CI_PROJECT_NAME}:$version" --pull
fi
docker tag "${CI_PROJECT_NAME}:$version" "$CONTAINER_IMAGE_BASE:$version"
docker push "$CONTAINER_IMAGE_BASE:$version"

# ./bin/check-image-severity.sh
./bin/sign-image.sh

DIGEST=`docker inspect "$CONTAINER_IMAGE_BASE:$version" | jq -r '.[0].RepoDigests[0]' | cut -d'@' -f2`
export CONTAINER_IMAGE="$CONTAINER_IMAGE_BASE@$DIGEST"
echo $CONTAINER_IMAGE
./bin/deploy.sh
