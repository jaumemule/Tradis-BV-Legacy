#!/bin/bash

export AWS_ACCESS_KEY_ID=xxxxxxxx
export AWS_SECRET_ACCESS_KEY=xxxxxx
export AWS_DEFAULT_REGION=eu-west-1

aws s3 sync results_server_2 s3://tradis-simulation-results
