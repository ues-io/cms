#!/usr/bin/env bash

uesio login
uesio work -n=dev
npm run push
echo "Creating new $RELEASE_TYPE bundle..."
uesio bundle create -t=$RELEASE_TYPE
