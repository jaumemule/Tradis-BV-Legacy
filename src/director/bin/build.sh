#!/bin/bash

set -e

MODELS_DIR=/usr/app/src/director/saves/agent
echo "Downloading current models from \"${MODELS_BUCKET}\" to \"${MODELS_DIR}\""
mkdir -p ${MODELS_DIR}
aws s3 sync s3://${MODELS_BUCKET}/ ${MODELS_DIR}/

echo "Director succesfuly installed. Building director"

currentDir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

projectDir=$currentDir/../app

# RUN build
echo "RUNNING director"
echo "Job succesfully done"

python ./director_worker.py