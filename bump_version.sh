#!/bin/bash

set -eua

NEW_VERSION=${1:?Please provide a new version}
CURRENT_VERSION=$(grep -m1 '^version' pyproject.toml | sed -E 's/.*"(.*)".*/\1/')

if [ -n "$(git status --porcelain)" ]; then
  echo "Uncommitted changes"
  exit 1
fi

echo "Updating version from ${CURRENT_VERSION} to ${NEW_VERSION}"

echo "Updating in package.json"
WD=$PWD
cd ui/ && pnpm version ${NEW_VERSION} --no-git-tag-version --allow-same-version
cd $WD

echo "Updating pyproject.toml"
sed -i '' "s/^version = \".*\"/version = \"${NEW_VERSION}\"/" pyproject.toml

echo "Updating Dockerfile"
sed -i '' "s/^ARG MC_VERSION=.*/ARG MC_VERSION=v${NEW_VERSION}/" Dockerfile

uv sync
