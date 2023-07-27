#!/usr/bin/env bash

set -e

uesio login
uesio work
npm run push
echo "Creating new $RELEASE_TYPE bundle..."
uesio bundle create -t=$RELEASE_TYPE
