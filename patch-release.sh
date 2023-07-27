#!/usr/bin/env bash

uesio login
uesio work
npm run push
echo "Creating new patch bundle..."
patchResult=$(uesio bundle create -t=patch)

# Extract version number from patchResult variable using grep
version=$(echo "$patchResult" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')

echo "Successfully created bundle with version = $version"
