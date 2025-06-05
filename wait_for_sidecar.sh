#!/bin/bash
until curl -fsI http://localhost:15021/healthz/ready; do
    echo 'Waiting for Sidecar...'
    sleep 1
done
function cleanup {
  echo "shutting proxy"
  # ask the istio-proxy to exit
  curl -fsI -X POST http://localhost:15020/quitquitquit
}

trap cleanup EXIT
# do the job here
$@
