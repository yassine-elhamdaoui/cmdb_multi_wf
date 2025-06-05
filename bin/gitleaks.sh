#!/bin/bash
set -eo pipefail

# Install the gitleaks cli from github.
curl -L -o ./build/gitleaks.tar.gz https://github.com/zricethezav/gitleaks/releases/download/v8.15.3/gitleaks_8.15.3_linux_x64.tar.gz

# Untar the gitleaks tarball
cd build
tar -zxvf gitleaks.tar.gz gitleaks
chmod +x gitleaks

# Run the gitleaks command on a non git repository to avoid failures from the commit history.
./gitleaks detect -v 5 --no-git -s ..
