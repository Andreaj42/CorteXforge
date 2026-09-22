#!/usr/bin/env bash

set -euo pipefail

# Usage:
#   ./upload_experiments.sh <username> <local_directory> <remote_directory>
#
# Example:
#   ./upload_experiments.sh andrea_joly cxf

USERNAME="$1"
LOCAL_DIR="$2"
REMOTE_DIR="${3:-/cortexlab/homes/${USERNAME}}"

HOST="gw.cortexlab.fr"

echo "Uploading:"
echo "  $LOCAL_DIR"
echo "to:"
echo "  ${USERNAME}@${HOST}:${REMOTE_DIR}"

rsync \
    -avh \
    --progress \
    "${LOCAL_DIR%/}/" \
    "${USERNAME}@${HOST}:${REMOTE_DIR%/}/${LOCAL_DIR}"

echo "Upload complete."