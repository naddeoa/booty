#!/bin/bash

# The repository owner and name
REPO_OWNER="naddeoa"
REPO_NAME="booty"
BIN_NAME="booty_mac_universal"

# Formulate the URL to fetch the latest release data from GitHub API
API_URL="https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/releases/latest"

BINARY_URL=$(curl -s $API_URL | grep "browser_download_url.*$BIN_NAME" | cut -d '"' -f 4)

# Check if the URL is empty
if [ -z "$BINARY_URL" ]; then
    echo "Failed to find the latest release binary URL. Exiting."
    exit 1
fi

# Download the binary file
echo "Downloading $BINARY_URL ..."
curl -L -o $BIN_NAME $BINARY_URL

# Apply executable permissions
chmod +x $BIN_NAME

echo "Downloaded booty to $(pwd)/$BIN_NAME"

