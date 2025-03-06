#!/bin/bash

if ! [ -x "$(command -v aws)" ]; then
    echo "AWS Command Line Interface must be installed on this computer"
    exit 1
fi

if ! [ -x "$(command -v docker)" ]; then
    echo "Docker must be installed on this computer"
    exit 1
fi

docker info > /dev/null 2>&1
if [ "$?" != "0" ]; then
    echo "Cannot connect to Docker daemon"
    exit 1
fi

AWS_PROFILE="cryptoreus"
AWS_REGION="eu-west-1"
REPOSITORY="439065282679.dkr.ecr.${AWS_REGION}.amazonaws.com/cryptoreus-python"
eval $(aws ecr get-login --no-include-email --profile ${AWS_PROFILE} --region ${AWS_REGION})
docker build -t ${REPOSITORY}:latest .
docker push ${REPOSITORY}:latest
