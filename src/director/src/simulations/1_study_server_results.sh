#!/bin/bash

export AWS_ACCESS_KEY_ID=xxxxxx
export AWS_SECRET_ACCESS_KEY=xxxxx
export AWS_DEFAULT_REGION=eu-west-1

aws s3 sync results_server_1 s3://tradis-simulation-results
